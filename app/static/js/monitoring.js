class EARGraph {
    constructor(containerId) {
        this.graphContainer = document.getElementById(containerId);
        this.margin = {top: 20, right: 20, bottom: 30, left: 50};
        this.width = this.graphContainer.clientWidth - this.margin.left - this.margin.right;
        this.height = this.graphContainer.clientHeight - this.margin.top - this.margin.bottom;
        
        this.liveGraphData = [];
        this.initializeGraph();
    }

    initializeGraph() {
        // Clear any existing SVG
        d3.select(`#${this.graphContainer.id} svg`).remove();

        // Create SVG
        this.svg = d3.select(`#${this.graphContainer.id}`)
            .append("svg")
            .attr("width", this.width + this.margin.left + this.margin.right)
            .attr("height", this.height + this.margin.top + this.margin.bottom)
            .append("g")
            .attr("transform", `translate(${this.margin.left},${this.margin.top})`);

        // Initialize scales and line
        this.x = d3.scaleTime().range([0, this.width]);
        this.y = d3.scaleLinear().range([this.height, 0]);
        this.line = d3.line()
            .x(d => this.x(d.time))
            .y(d => this.y(d.value))
            .curve(d3.curveMonotoneX);

        // Add axes
        this.svg.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${this.height})`);

        this.svg.append("g")
            .attr("class", "y-axis");

        // Add path for the line
        this.svg.append("path")
            .attr("class", "line")
            .style("fill", "none")
            .style("stroke", "#2c3e50")
            .style("stroke-width", "2px");
    }

    update(processedData) {
        if (processedData.value === null) return;
        
        this.liveGraphData.push(processedData);
        
        // Keep last 100 data points
        if (this.liveGraphData.length > 100) {
            this.liveGraphData.shift();
        }

        // Update scales
        this.x.domain(d3.extent(this.liveGraphData, d => d.time));
        this.y.domain([0, d3.max(this.liveGraphData, d => d.value) * 1.1]); // Add 10% padding

        // Update line
        this.svg.select(".line")
            .datum(this.liveGraphData)
            .attr("d", this.line);

        // Update axes
        this.svg.select(".x-axis").call(d3.axisBottom(this.x));
        this.svg.select(".y-axis").call(d3.axisLeft(this.y));
    }

    // Handle window resize
    handleResize() {
        this.width = this.graphContainer.clientWidth - this.margin.left - this.margin.right;
        this.height = this.graphContainer.clientHeight - this.margin.top - this.margin.bottom;
        
        // Recreate the entire graph
        this.initializeGraph();
        
        // Re-render the last state
        if (this.liveGraphData.length > 0) {
            this.update({
                time: new Date(),
                value: this.liveGraphData[this.liveGraphData.length - 1].value
            });
        }
    }
}

// WebSocket and Video Processing Class
class WebcamMonitor {
    constructor(displayCanvasId, graphInstance) {
        this.mediaStream = null;
        this.videoTrack = null;
        this.trackProcessor = null;
        this.ws = null;
        this.isRecording = false;
        this.displayCanvas = document.getElementById(displayCanvasId);
        this.graph = graphInstance;
        this.recordBtn = document.getElementById('recordBtn');
    }

    async startRecording() {
        try {
            // Request webcam access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 30 }
                } 
            });

            // Get the first video track
            this.videoTrack = this.mediaStream.getVideoTracks()[0];

            // Create MediaStreamTrackProcessor
            this.trackProcessor = new MediaStreamTrackProcessor({ 
                track: this.videoTrack 
            });

            // Update record button state
            this.recordBtn.classList.add('recording');
            this.recordBtn.textContent = 'Stop Recording';

            // Connect WebSocket
            this.connectWebSocket();

            // Start frame processing
            this.processFrames();

        } catch (error) {
            console.error('Recording start error:', error);
            alert('Failed to start recording. Please check camera permissions.');
        }
    }

    connectWebSocket() {
        this.ws = new WebSocket('ws://localhost:8000/monitoring/websocket_process');
        const videoContainer = document.querySelector('.video-container');

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isRecording = true;
        };

        this.ws.onmessage = async (event) => {
            if (event.data instanceof Blob) {
                // Display annotated frame
                const ctx = this.displayCanvas.getContext('2d');
                
                const img = new Image();
                img.onload = () => {
                    // Resize canvas to match image
                    this.displayCanvas.width = img.width;
                    this.displayCanvas.height = img.height;
                    // Adjust video container to match frame dimensions
                    if (videoContainer) {
                        videoContainer.classList.add('active');
                        videoContainer.style.height = `${img.height}px`;
                    }
                    
                    ctx.drawImage(img, 0, 0);
                    URL.revokeObjectURL(img.src);
                };
                img.src = URL.createObjectURL(event.data);
            } else {
                // Parse JSON data
                try {
                    const data = JSON.parse(event.data);
                    // Update graph with processed data
                    this.graph.update({
                        time: new Date(data.timestamp * 1000),
                        value: data.processed_data
                    });
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.stopRecording();
        };

        this.ws.onclose = () => {
            this.isRecording = false;
            console.log('WebSocket disconnected');
        };
    }

    async processFrames() {
        // Create a ReadableStream from the track processor
        const frameStream = this.trackProcessor.readable;
        
        // Create a WritableStream for sending frames
        const frameSender = new WritableStream({
            write: async (videoFrame) => {
                if (!this.isRecording || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    videoFrame.close();
                    return;
                }

                try {
                    // Convert VideoFrame to Blob
                    const bitmap = await createImageBitmap(videoFrame);
                    const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(bitmap, 0, 0);

                    // Convert to blob and send
                    const blob = await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.8 });
                    this.ws.send(blob);

                    // Close the frame to prevent memory leaks
                    videoFrame.close();
                    bitmap.close();
                } catch (error) {
                    console.error('Frame processing error:', error);
                }
            }
        });

        // Pipe the frame stream to the sender
        frameStream.pipeTo(frameSender);
    }

    stopRecording() {
        this.isRecording = false;
        
        // Reset record button
        this.recordBtn.classList.remove('recording');
        this.recordBtn.textContent = 'Start Recording';
        
        // Reset video panel
        const videoPanel = document.querySelector('.video-container');
        videoPanel.classList.remove('active');
        videoPanel.style.minHeight = '200px';

        // Clear canvas
        const ctx = this.displayCanvas.getContext('2d');
        ctx.clearRect(0, 0, this.displayCanvas.width, this.displayCanvas.height);
        this.displayCanvas.width = 0;
        this.displayCanvas.height = 0;
        
        // Close video track
        if (this.videoTrack) {
            this.videoTrack.stop();
        }

        // Close media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }

        // Close track processor
        if (this.trackProcessor) {
            this.trackProcessor.readable.cancel();
        }

        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Initialization when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Create graph instance first
    const earGraph = new EARGraph('liveGraphData');

    // Create webcam monitor, passing graph instance
    const monitor = new WebcamMonitor('displayCanvas', earGraph);

    // Button event listener
    document.getElementById('recordBtn').addEventListener('click', () => {
        if (monitor.isRecording) {
            monitor.stopRecording();
        } else {
            monitor.startRecording();
        }
    });

    // Handle window resize for graph
    window.addEventListener('resize', () => {
        earGraph.handleResize();
    });
});