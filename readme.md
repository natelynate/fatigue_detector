## Outline

This project implements a comprehensive eye fatigue detection and monitoring system that tracks users' eye movements through webcam video analysis. The system calculates Eye Aspect Ratio (EAR) values in real-time to detect blinks and measure fatigue indicators.

## Architecture
Frontend: JavaScript-based webcam monitoring with real-time EAR calculation and D3.js visualization
Backend: FastAPI application handling user authentication and WebSocket connections
Messaging: Kafka-based event streaming for session events and frame data
Analytics: Time-window processing of eye metrics to detect fatigue patterns
Deployment: Kubernetes-based infrastructure with Helm charts for service orchestration

## Features
Real-time eye blink detection using MediaPipe face mesh
WebSocket streaming of EAR values to backend services
Kafka event processing for durable storage of monitoring sessions
Time-window analytics to calculate fatigue indicators:

1. Blink frequency
2. Average intervals between blinks
3. Average eye closure duration