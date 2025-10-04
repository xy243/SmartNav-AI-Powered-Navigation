SmartNav – Navigation Assistant for Visually Impaired Users

SmartNav is a Python-based navigation assistant designed to help visually impaired users navigate safely indoors and outdoors. It combines real-time object detection using YOLOv8 with text-to-speech alerts and emergency notifications.

Features

Indoor Mode: Detects and announces common indoor objects (chair, table, laptop, bottle, etc.) to help users orient themselves in unfamiliar indoor spaces.

Outdoor Mode: Detects outdoor objects (person, vehicle, traffic signals, etc.) and provides spoken directions with position (left/right/ahead) and distance (very close, medium distance, far ahead).

Voice Destination Navigation: Users can speak their desired destination, and SmartNav guides them step by step.

Emergency Alerts: Sends an email to a guardian or caregiver in case of emergencies.

Real-Time Camera Feed: Uses a webcam to detect objects and obstacles in real time.

Accessible Interface: Fully voice-enabled for hands-free operation.

How It Helps Visually Impaired Users

Provides audio cues for objects around the user, helping them avoid obstacles indoors.

Announces nearby obstacles and directions outdoors, reducing the risk of accidents.

Supports hands-free operation via voice input for destinations.

Sends emergency notifications to guardians, adding a safety layer.

Installation

>Clone the repository:

git clone https://github.com/xy243/SmartNav-AI-Powered-Navigation.git
cd SmartNav


Install required packages from requirements.txt:

pip install -r requirements.txt


Download the YOLOv8 model (yolov8l.pt) and place it in the project directory.

Ensure a working webcam and microphone are available.

Configuration

Email Alerts:
Update SENDER_EMAIL, SENDER_PASSWORD, and RECEIVER_EMAIL in smart_nav.py for emergency notifications.

Mode Switching:

-Press I for indoor mode

-Press O for outdoor mode

-Press E to send an emergency alert

-Press Q to quit the application

Usage:

Run the main script:

python smart_nav.py


Starts in indoor mode by default.

Announces detected objects to assist the user.

Provides navigation instructions in outdoor mode when a destination is set.

Indoor Mode

Announces only the names of indoor objects detected.

>Helps visually impaired users identify objects around them and avoid obstacles.

Outdoor Mode

Announces object names, positions, and distances.

Guides users safely while walking outdoors.

>Dependencies

All dependencies are listed in requirements.txt. Ensure you have Python 3.8+ installed.

Example dependencies included:

-ultralytics (YOLOv8)

-opencv-python

-pyttsx3 (Text-to-speech)

-SpeechRecognition (Voice input)

-requests (API calls for geocoding and routing)

>Install them with:

pip install -r requirements.txt

Folder Structure
SmartNav/
│
├─ smart_nav.py        # Main Python script
├─ yolov8l.pt          # YOLOv8 model
├─ requirements.txt    # Python dependencies
└─ README.md

>Notes for Users

Ensure a stable internet connection for geocoding and navigation features.

Proper lighting improves indoor detection accuracy.

Use a valid Gmail account for emergency alerts (or update SMTP configuration for another provider).
