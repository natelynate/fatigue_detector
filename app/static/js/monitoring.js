class WebcamMonitor {
    constructor() {
        this.mediaStream = null;
        this.videoTrack = null;
        this.trackProcessor = null;
        this.trackGenerator = null;
        this.ws = null;
        this.isRecording = false;
        this.displayCanvas = document.getElementById('displayCanvas');
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

            // Create MediaStreamTrackGenerator for displaying processed frames
            this.trackGenerator = new MediaStreamTrackGenerator({ kind: 'video' });

            // Connect WebSocket
            this.connectWebSocket();

            // Start frame processing
            this.processFrames();

        } catch (error) {
            console.error('Recording start error:', error);
        }
    }

    connectWebSocket() {
        this.ws = new WebSocket('ws://localhost:8000/monitoring/websocket_process');

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isRecording = true;
        };

        this.ws.onmessage = (event) => {
            // Handle annotated frame from backend
            if (event.data instanceof Blob) {
                this.displayAnnotatedFrame(event.data);
            }
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

    displayAnnotatedFrame(frame) {
        const ctx = this.displayCanvas.getContext('2d');
        
        const img = new Image();
        img.onload = () => {
            // Resize canvas to match image
            this.displayCanvas.width = img.width;
            this.displayCanvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            URL.revokeObjectURL(img.src);
        };
        img.src = URL.createObjectURL(frame);
    }

    stopRecording() {
        this.isRecording = false;
        
        // Close video track
        if (this.videoTrack) {
            this.videoTrack.stop();
        }

        // Close media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }

        // Close track processor and generator
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

const monitor = new WebcamMonitor();
document.getElementById('recordBtn').addEventListener('click', () => {
    if (monitor.isRecording) {
        monitor.stopRecording();
    } else {
        monitor.startRecording();
    }
});