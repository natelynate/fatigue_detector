document.addEventListener('DOMContentLoaded', function() {
    // Record Button Effects
    const recordBtn = document.getElementById('recordBtn');
    let isRecording = false;

    recordBtn.addEventListener('click', function() {
        isRecording = !isRecording;
        this.classList.toggle('recording');
        
        if (isRecording) {
            this.style.transform = 'scale(0.95)';
            this.textContent = 'Stop Recording';
            // WebSocket connection would be initialized here
        } else {
            this.style.transform = 'scale(1)';
            this.textContent = 'Start Recording';
            // WebSocket connection would be closed here
        }
    });

    // Initialize D3.js Graph
    const margin = {top: 20, right: 20, bottom: 30, left: 50};
    const width = document.getElementById('liveGraph').clientWidth - margin.left - margin.right;
    const height = document.getElementById('liveGraph').clientHeight - margin.top - margin.bottom;

    const svg = d3.select("#liveGraph")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Initialize scales
    const x = d3.scaleTime()
        .range([0, width]);

    const y = d3.scaleLinear()
        .range([height, 0]);

    // Initialize line
    const line = d3.line()
        .x(d => x(d.time))
        .y(d => y(d.value));

    // Add axes
    svg.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0,${height})`);

    svg.append("g")
        .attr("class", "y-axis");

    // Initialize Webcam
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                const video = document.getElementById('webcamFeed');
                video.srcObject = stream;
            })
            .catch(function(error) {
                console.error("Could not access webcam:", error);
            });
    }
});