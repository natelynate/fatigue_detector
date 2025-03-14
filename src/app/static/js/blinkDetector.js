export class BlinkDetector {
    constructor(annotate = false) {
        this.faceMesh = null;
        this.ready = false;
        this.annotate = annotate;
        
        // State tracking variables
        this.counter = 0;
        this.closure = null;
        this.total_blinks = 0;
        this.EAR_THRESHOLD = 0.30;
        this.MIN_CONSECUTIVE_FRAMES = 4;
        this.MAX_CONSECUTIVE_FRAMES = 24;

        // MediaPipe indices for the eye landmarks
        this.LEFT_EYE = [362, 385, 387, 263, 373, 380];
        this.RIGHT_EYE = [33, 160, 158, 133, 153, 144];

        // Initialize MediaPipe
        this.initialize();
    }

    async initialize() {
        this.faceMesh = new FaceMesh({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
            }
        });

        // Configure FaceMesh
        this.faceMesh.setOptions({
            maxNumFaces: 1,
            refineLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        // Set up onResults callback
        this.faceMesh.onResults((results) => {
            this.results = results;
        });

        // Wait for FaceMesh to be ready
        await this.faceMesh.initialize();
        this.ready = true;
    }

    calculateEAR(eyeLandmarks) {
        const distance = (point1, point2) => {
            return Math.sqrt(
                Math.pow(point1.x - point2.x, 2) + 
                Math.pow(point1.y - point2.y, 2)
            );
        };

        const A = distance(eyeLandmarks[1], eyeLandmarks[5]);
        const B = distance(eyeLandmarks[2], eyeLandmarks[4]);
        const C = distance(eyeLandmarks[0], eyeLandmarks[3]);
        
        return (A + B) / (2.0 * C);
    }

    async processFrame(canvas) {
        if (!this.ready) {
            console.log('FaceMesh not ready yet');
            return { ear_value: null, timestamp: Date.now() / 1000 };
        }

        // Process the frame
        await this.faceMesh.send({ image: canvas });
        
        let ear = null;
        const ctx = canvas.getContext('2d');
        let event_onset = false;  // Initialize to false by default
        let event_end = false;    // Initialize to false by default

        if (this.results && this.results.multiFaceLandmarks && this.results.multiFaceLandmarks.length > 0) {
            const faceLandmarks = this.results.multiFaceLandmarks[0];
            
            const leftEye = this.LEFT_EYE.map(index => ({
                x: faceLandmarks[index].x * canvas.width,
                y: faceLandmarks[index].y * canvas.height
            }));

            const rightEye = this.RIGHT_EYE.map(index => ({
                x: faceLandmarks[index].x * canvas.width,
                y: faceLandmarks[index].y * canvas.height
            }));

            const leftEAR = this.calculateEAR(leftEye);
            const rightEAR = this.calculateEAR(rightEye);
            ear = (leftEAR + rightEAR) / 2.0;

            if (0 < ear && ear < this.EAR_THRESHOLD) {
                if (this.closure === null) {
                    this.closure = Date.now();
                    event_onset = true;  // Signal blink onset
                    console.log("Blink onset detected"); // debug
                }
                this.counter++;
                console.log(`counter:${this.counter}`, ear, this.total_blinks);
            } else if (ear > this.EAR_THRESHOLD) {
                if (this.closure !== null) {
                    if (this.counter >= this.MIN_CONSECUTIVE_FRAMES) {
                        this.total_blinks++;
                        event_end = true;  // Signal valid blink end
                        console.log("Blink end detected");
                    }
                    this.closure = null;
                    this.counter = 0;
                }
            }

            if (this.annotate) {
                [leftEye, rightEye].forEach(eye => {
                    eye.forEach(point => {
                        ctx.beginPath();
                        ctx.arc(point.x, point.y, 2, 0, 2 * Math.PI);
                        ctx.fillStyle = 'rgb(0, 255, 0)';
                        ctx.fill();
                    });
                });

                ctx.font = '24px Arial';
                ctx.fillStyle = 'rgb(0, 255, 0)';
                ctx.fillText(`EAR: ${ear?.toFixed(2)}`, 10, 30);
                ctx.fillText(`Blinks: ${this.total_blinks}`, 10, 60);
            }
        }

        return {
            ear_value: ear,
            timestamp: Date.now() / 1000,
            event_onset: event_onset,
            event_end: event_end
        };
    }
}