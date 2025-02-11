import { BlinkDetector } from './blinkDetector.js';

const getGraphContainer = (() => {
    let container = null;
    return () => {
        if (!container) {
            container = document.querySelector('.viz-panel');
            if (!container) {
                container = document.createElement('div');
                container.classList.add('section', 'viz-panel');
                container.innerHTML = `
                    <h2>Live Monitoring</h2>
                    <div id="liveGraphData"></div>
                `;
                const recordSection = document.querySelector('.record-section');
                recordSection.insertAdjacentElement('afterend', container);
            }
        }
        return container.querySelector('#liveGraphData');
    };
})();

// Keep the existing EARGraph class unchanged
class EARGraph {
    constructor() {
        this.properties = {
            margin: { top: 20, right: 20, bottom: 30, left: 50 },
            maxDataPoints: 300,
            width: 0,
            height: 0,
            data: [],
            isActive: false
        };

        this.container = getGraphContainer();
        this.updateDimensions();
        this.initializeGraph();
        this.setupResizeHandler();
    }

    static getInstance() {
        if (!EARGraph.instance) {
            EARGraph.instance = new EARGraph();
        }
        return EARGraph.instance;
    }

    updateDimensions() {
        const containerRect = this.container.getBoundingClientRect();
        this.properties.width = Math.max(containerRect.width - this.properties.margin.left - this.properties.margin.right, 300);
        this.properties.height = Math.max(containerRect.height - this.properties.margin.top - this.properties.margin.bottom, 200);
    }

    initializeGraph() {
        d3.select(this.container).select('svg').remove();

        this.svg = d3.select(this.container)
            .append("svg")
            .attr("width", this.properties.width + this.properties.margin.left + this.properties.margin.right)
            .attr("height", this.properties.height + this.properties.margin.top + this.properties.margin.bottom)
            .append("g")
            .attr("transform", `translate(${this.properties.margin.left},${this.properties.margin.top})`);

        this.initializeScales();
        this.initializeAxes();
        this.initializeLine();
    }

    initializeScales() {
        this.scales = {
            x: d3.scaleTime()
                .range([0, this.properties.width]),
            y: d3.scaleLinear()
                .range([this.properties.height, 0])
                .domain([-0.1, 0.8])
        };
    }

    initializeAxes() {
        this.svg.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${this.properties.height})`);

        this.svg.append("g")
            .attr("class", "y-axis");
    }

    initializeLine() {
        this.line = d3.line()
            .x(d => this.scales.x(d.time))
            .y(d => this.scales.y(d.value))
            .curve(d3.curveMonotoneX);

        this.svg.append("path")
            .attr("class", "line")
            .style("fill", "none")
            .style("stroke", "#2c3e50")
            .style("stroke-width", "2px");
    }

    updateData(rawData) {
        if (!this.properties.isActive || rawData.ear_value === null) return;

        const processedData = {
            time: new Date(rawData.timestamp * 1000),
            value: rawData.ear_value
        };

        this.properties.data.push(processedData);

        if (this.properties.data.length > this.properties.maxDataPoints) {
            this.properties.data.shift();
        }

        this.updateGraphVisualization();
    }

    updateGraphVisualization() {
        this.scales.x.domain(d3.extent(this.properties.data, d => d.time));

        this.svg.select(".line")
            .datum(this.properties.data)
            .attr("d", this.line);

        this.updateAxes();
    }

    updateAxes() {
        this.svg.select(".x-axis").call(
            d3.axisBottom(this.scales.x)
                .tickFormat(d => d.toTimeString().split(' ')[0])
        );
        this.svg.select(".y-axis").call(d3.axisLeft(this.scales.y));
    }

    handleResize() {
        this.updateDimensions();
        this.initializeGraph();
        if (this.properties.data.length > 0) {
            this.updateGraphVisualization();
        }
    }

    setupResizeHandler() {
        window.addEventListener('resize', () => this.handleResize());
    }

    start() {
        this.properties.isActive = true;
    }

    stop() {
        this.properties.isActive = false;
    }

    clear() {
        this.properties.data = [];
        this.updateGraphVisualization();
    }
}


class WebcamMonitor {
    constructor() {
        this.mediaStream = null;
        this.videoTrack = null;
        this.trackProcessor = null;
        this.isRecording = false;
        this.displayCanvas = document.createElement('canvas');
        this.detector = new BlinkDetector(true);
        this.graph = EARGraph.getInstance();
        this.websocket = null;
        
        // Initialize display canvas
        document.querySelector('.container').appendChild(this.displayCanvas);
    }

    initializeWebSocket() {
        // Create WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/monitoring/websocket_process`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connection established');
        };
        
        this.websocket.onmessage = (event) => {
            const response = JSON.parse(event.data);
            console.log('Server response:', response);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }

    async startRecording() {
        try {
            this.initializeWebSocket(); // Initialize WebSocket connection
            await this.initializeMediaStream();
            this.isRecording = true;
            this.graph.start();
            document.getElementById('recordBtn').textContent = 'Stop Recording';
            this.processFrames();
        } catch (error) {
            console.error('Recording start error:', error);
            alert('Failed to start recording. Please check camera permissions.');
        }
    }

    async initializeMediaStream() {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30 }
            }
        });
        this.videoTrack = this.mediaStream.getVideoTracks()[0];
        this.trackProcessor = new MediaStreamTrackProcessor({ track: this.videoTrack });
    }

    async processFrames() {
        const frameStream = this.trackProcessor.readable;
        const frameProcessor = new WritableStream({
            write: async (videoFrame) => {
                if (!this.isRecording) {
                    videoFrame.close();
                    return;
                }
                try {
                    const bitmap = await createImageBitmap(videoFrame);
                    
                    // Set canvas dimensions if needed
                    if (this.displayCanvas.width !== bitmap.width) {
                        this.displayCanvas.width = bitmap.width;
                        this.displayCanvas.height = bitmap.height;
                    }

                    // Draw frame to canvas
                    const ctx = this.displayCanvas.getContext('2d', {
                        alpha: false,
                        willReadFrequently: true
                    });
                    ctx.drawImage(bitmap, 0, 0);
                    const blob = await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.8 });

                    // Process frame directly with BlinkDetector
                    const result = await this.detector.processFrame(this.displayCanvas);

                    // Send data through WebSocket if connection is open
                    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                        const data = {
                            timestamp: result.timestamp,
                            ear_value: result.ear_value
                        };
                        this.websocket.send(JSON.stringify(data));
                    }
                    
                    // Update graph with processed data
                    this.graph.updateData(result);
                    
                    videoFrame.close();
                    bitmap.close();
                } catch (error) {
                    console.error('Frame processing error:', error);
                }
            }
        });

        frameStream.pipeTo(frameProcessor);
    }

    stopRecording() {
        this.isRecording = false;
        this.graph.stop();
        document.getElementById('recordBtn').textContent = 'Start Recording';

        // Close WebSocket connection
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        // Stop mediastream
        if (this.videoTrack) this.videoTrack.stop();
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        if (this.trackProcessor) {
            this.trackProcessor.readable.cancel();
        }
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    const monitor = new WebcamMonitor();
    document.getElementById('recordBtn').addEventListener('click', () => {
        if (monitor.isRecording) {
            monitor.stopRecording();
        } else {
            monitor.startRecording();
        }
    });
});