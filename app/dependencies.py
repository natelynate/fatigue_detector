from typing import Annotated
from fastapi import Header, HTTPException
import numpy as np
import mediapipe as mp
import cv2
import time


async def get_token_header(x_token: str = Header(default=None)):
    pass # Temporary pass all requests


class BlinkDetector:
    """
    BlinkDetector object used for processing the webcam frames.
    Returns: mean EAR at frame f, and annotated frame (if annotation is set True during init)
    """
    def __init__(self, annotate=False):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # MediaPipe indices for the eye landmarks
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]

        # State tracking variable for intelligent blink detection
        self.counter = 0
        self.closure = None
        self.total_blinks = 0
        self.EAR_THRESHOLD = 0.28
        self.MIN_CONSECUTIVE_FRAMES = 3 # Minimum number of consecutive frames to be recognized as a blink
        self.MAX_CONSECUTIVE_FRAMES = 24

        # configs for the instance
        self.annotate = annotate


    def calculate_ear(self, eye_landmarks):
        """
        Calculate eye aspect ratio given eye landmarks
        """
        # Vertical distances
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        
        # Horizontal distance
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        # Calculate EAR
        ear = (A + B) / (2.0 * C)
        return ear
    
    
    def process_frame(self, frame, **kwargs):
        """
        Process a single frame and detect blinks
        """
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        frame_height, frame_width = frame.shape[:2]
        ear = None # EAR = None indicates no face presnece or no valid face landmarks
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0] # Choose the first one
            left_eye = np.array([[face_landmarks.landmark[i].x * frame_width,
                                face_landmarks.landmark[i].y * frame_height] 
                                for i in self.LEFT_EYE])
            right_eye = np.array([[face_landmarks.landmark[i].x * frame_width,
                                 face_landmarks.landmark[i].y * frame_height] 
                                 for i in self.RIGHT_EYE])  
            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)

            # Average EAR
            ear = (left_ear + right_ear) / 2.0
            
            # Spontaneous blink detection
            if ear < self.EAR_THRESHOLD:
                if self.closure is None:  # Start of new closure
                    self.closure = time.time()
                self.counter += 1  # Increment counter for every frame while eye is closed
                # print(f"self.counter:{self.counter}", ear, time.time())
            
            elif ear > self.EAR_THRESHOLD:  # Eye is open
                if self.closure is not None:  
                    if self.counter >= self.MIN_CONSECUTIVE_FRAMES:
                        self.total_blinks += 1
                # Reset tracking variables
                self.closure = None
                self.counter = 0

            if self.annotate: # Visualization
                for eye in [left_eye, right_eye]:
                    for point in eye:
                        cv2.circle(frame, tuple(point.astype(int)), 2, (0, 255, 0), -1)
                cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Blinks: {self.total_blinks}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
        return frame, ear