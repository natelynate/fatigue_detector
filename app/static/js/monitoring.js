class EARGraph {
    constructor(containerId) {
        this.graphContainer = document.getElementById(containerId);
        
        // Default dimensions if container is not available
        this.margin = {top: 20, right: 20, bottom: 30, left: 50};
        this.width = 300; // Default width
        this.height = 200; // Default height

        // Update dimensions when container is available
        if (this.graphContainer) {
            const containerRect = this.graphContainer.getBoundingClientRect();
            this.width = Math.max(containerRect.width - this.margin.left - this.margin.right, 300);
            this.height = Math.max(containerRect.height - this.margin.top - this.margin.bottom, 200);
        }
        
        this.liveGraphData = [];
        this.initializeGraph();
    }

    initializeGraph() {
        // Check if graph container exists and has an ID
        if (!this.graphContainer) {
            console.warn('Graph container not found');
            return;
        }
        console.log('Initializing graph');  

        // Clear any existing SVG
        if (this.graphContainer.id) {
            d3.select(`#${this.graphContainer.id} svg`).remove();
        } else {
            // Fallback if no ID
            d3.select(this.graphContainer).select('svg').remove();
        }

        // Create SVG
        this.svg = d3.select(this.graphContainer)
            .append("svg")
            .attr("width", this.width + this.margin.left + this.margin.right)
            .attr("height", this.height + this.margin.top + this.margin.bottom)
            .append("g")
            .attr("transform", `translate(${this.margin.left},${this.margin.top})`);

        // Initialize scales and line
        this.x = d3.scaleTime().range([0, this.width]);
        this.y = d3.scaleLinear()
            .range([this.height, 0])
            .domain([-0.1, 0.8]);
        this.line = d3.line()
            .x(d => this.x(d.time))
            .y(d => this.y(d.value))
            .curve(d3.curveMonotoneX);

        // Add axes
        this.svg.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${this.height})`)
            .call(d3.axisBottom(this.x).tickFormat(d => {
                const date = new Date(d * 1000);
                return date.toTimeString().split(' ')[0];
            }))

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
        const dataPoint = {
            time: processedData.time instanceof Date ? processedData.time : new Date(processedData.time * 1000),
            value: processedData.value
        };
        
        this.liveGraphData.push(dataPoint);
        
        // Keep last 100 data points
        if (this.liveGraphData.length > 300) {
            this.liveGraphData.shift();
        }

        // Update scales
        this.x.domain(d3.extent(this.liveGraphData, d => d.time));

        // Update line
        this.svg.select(".line")
            .datum(this.liveGraphData)
            .attr("d", this.line);

        // Update axes
        this.svg.select(".x-axis").call(
            d3.axisBottom(this.x)
                .tickFormat(d => {
                    return d.toTimeString().split(' ')[0]; // Conver unix timestamp to timestamp
                })
        );
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
            const lastPoint = this.liveGraphData[this.liveGraphData.length - 1];
            this.update({
                time: lastPoint.time, // Use existing time instead of creating new Date
                value: lastPoint.value
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
            let videoContainer = document.querySelector('.video-container');
            if (!videoContainer) {
                const videoContainer = document.createElement('div');
                videoContainer.classList.add('video-container');
                videoContainer.innerHTML = `<canvas id="displayCanvas"></canvas>`;
                const recordSection = document.querySelector('.record-section');
                recordSection.insertAdjacentElement('afterend', videoContainer);
                this.displayCanvas = videoContainer.querySelector('#displayCanvas');  // Update displayCanvas reference
            }

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
                        time: data.timestamp, // Send raw timestamp, let EARGraph handle conversion
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
    const monitor = new WebcamMonitor(null);
    let graphContainer = null;
    let earGraph = null;
    // Button event listener
    document.getElementById('recordBtn').addEventListener('click', () => {
        if (monitor.isRecording) {
            monitor.stopRecording();
        } else {
            // Only create graph container if it doesn't exist
            if (!document.querySelector('.viz-panel')) {
                graphContainer = document.createElement('div');
                graphContainer.classList.add('section', 'viz-panel');
                graphContainer.innerHTML = `
                    <h2>Live Monitoring</h2>
                    <div id="liveGraphData"></div>
                `;
                const recordSection = document.querySelector('.record-section');
                if (recordSection) {
                    recordSection.insertAdjacentElement('afterend', graphContainer);
                }
            }
            const liveGraphDataElement = document.getElementById('liveGraphData');
            if (!earGraph && liveGraphDataElement) {
                try {
                    earGraph = new EARGraph('liveGraphData');
                } catch (error) {
                    console.error('Error creating graph:', error);
                    return;
                }
            }
            
            if (earGraph) {
                monitor.graph = earGraph;
                monitor.startRecording();
            } else {
                console.error('Could not create graph');
            }    
        }
    });
    window.addEventListener('resize', () => {
        if (earGraph) {
            earGraph.handleResize();
        }
    });
});