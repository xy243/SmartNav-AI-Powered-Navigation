from ultralytics import YOLO
import cv2
import pyttsx3
import time
import requests
import speech_recognition as sr
import threading
import queue
import smtplib
from email.message import EmailMessage

# ------------------- Email Config -------------------
SENDER_EMAIL = "bhargaviborkhade@gmail.com"
SENDER_PASSWORD = "ywleierfxdomnuah"
RECEIVER_EMAIL = "pingleshreya97@gmail.com"

# ------------------- TTS -------------------
engine = pyttsx3.init()
engine.setProperty("rate", 150)
tts_queue = queue.Queue()

def tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()
        tts_queue.task_done()

tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

def speak(text):
    print("🔊", text)
    tts_queue.put(text)

# ------------------- YOLO -------------------
model = YOLO("yolov8l.pt")

# ------------------- Camera -------------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ Camera not accessible")
    exit()

# ------------------- Settings -------------------
last_time = time.time()
cooldown = 1.0
mode = "indoor"  # default mode
outdoor_objects = ["person","car","truck","bus","bicycle","pole","traffic light","bench","bird","cat","dog"]
indoor_objects = ["chair","table","sofa","bed","bottle","tiffin","bag","handbag","tie","laptop","mouse","remote","keyboard",
                  "cell phone","microwave","oven","toaster","sink","refrigerator","book","clock","vase","scissors",
                  "teddy bear","cup","fork","knife","spoon","bowl"]

# ------------------- Navigation State -------------------
navigation_steps = []
nav_thread = None
nav_stop_event = threading.Event()
destination_set = False
current_lat, current_lon = 18.5294, 73.8478  # simulated start
prev_alerts_set = set()

# ------------------- Guardian Alert -------------------
def send_guardian_alert():
    msg = EmailMessage()
    msg['Subject'] = "SmartNav Emergency Alert"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content("⚠ Emergency Alert! User pressed emergency.")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("✅ Guardian notified")
    except Exception as e:
        print("❌ Email failed:", e)

# ------------------- Voice Destination -------------------
def get_destination_voice(retries=3):
    r = sr.Recognizer()
    for _ in range(retries):
        with sr.Microphone() as source:
            speak("Please tell me the destination.")
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening for destination...")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=8)
            except Exception:
                continue
        try:
            dest = r.recognize_google(audio)
            print("Destination recognized:", dest)
            speak(f"You said: {dest}")
            return dest
        except sr.UnknownValueError:
            speak("Sorry, I did not catch that. Please repeat.")
    speak("Could not recognize destination.")
    return None

# ------------------- Geocoding -------------------
def get_coordinates(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 3}
    headers = {"User-Agent": "SmartNavApp/1.0 (contact: bhargaviborkhade@gmail.com)"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        print("Geocoding error:", e)
    return None, None

# ------------------- Routing -------------------
def get_route_steps(start_lat, start_lon, end_lat, end_lon):
    url = f"http://router.project-osrm.org/route/v1/foot/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {"overview":"full","steps":"true","geometries":"geojson"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        steps_out = []
        for leg in data.get("routes",[{}])[0].get("legs", []):
            for step in leg.get("steps", []):
                maneuver = step.get("maneuver", {})
                step_obj = {
                    "distance": float(step.get("distance",0)),
                    "duration": float(step.get("duration",0)),
                    "name": step.get("name",""),
                    "modifier": maneuver.get("modifier",""),
                    "location": maneuver.get("location", [])
                }
                steps_out.append(step_obj)
        return steps_out
    except Exception as e:
        print("Routing error:", e)
        return []

# ------------------- Navigation Worker -------------------
def navigation_worker(steps, stop_event):
    speak("Navigation started. I will guide you step by step.")
    for step in steps:
        if stop_event.is_set():
            print("Navigation stopped.")
            return
        dist = int(round(step.get("distance", 0)))
        mins = int(round(step.get("duration", 0)/60))
        modifier = step.get("modifier","")
        name = step.get("name","")
        instr = f"In {dist} meters, {('turn '+modifier) if modifier else 'proceed'}"
        if name:
            instr += f" onto {name}."
        else:
            instr += "."
        if mins>0:
            instr += f" Approx {mins} minute{'s' if mins>1 else ''}."
        print("NAV:", instr)
        speak(instr)
        total_wait = max(1.0, min(step.get("duration",5), 8.0))
        slept = 0.0
        chunk = 0.5
        while slept < total_wait:
            if stop_event.is_set():
                print("Navigation stopped mid-step.")
                return
            time.sleep(chunk)
            slept += chunk
    speak("You have arrived at your destination.")
    print("Navigation complete.")

# ------------------- Main Loop -------------------
speak("Starting SmartNav in Indoor mode")
print("✅ SmartNav ready. Keys: O outdoor, I indoor, E emergency, Q quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera frame error")
            break

        h, w = frame.shape[:2]
        scale = 480/max(h,w)
        if scale<1:
            frame = cv2.resize(frame,(int(w*scale),int(h*scale)))
            h, w = frame.shape[:2]

        # YOLO detection
        results = model(frame)[0]
        alerts_set = set()
        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = model.names[cls]
            if conf<0.45:
                continue
            if (mode=="outdoor" and label not in outdoor_objects) or (mode=="indoor" and label not in indoor_objects):
                continue

            x1,y1,x2,y2 = map(int, box.xyxy[0])
            center_x = (x1+x2)//2
            if center_x < w//3:
                loc = "on your right"
            elif center_x > 2*w//3:
                loc = "on your left"
            else:
                loc = "ahead"

            area_ratio = (x2-x1)*(y2-y1)/(w*h)
            if area_ratio>0.25:
                dist_text="very close"
            elif area_ratio>0.07:
                dist_text="medium distance"
            else:
                dist_text="far ahead"

            alert_text = f"{label} {loc}, {dist_text}"
            alerts_set.add(alert_text)

            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
            cv2.putText(frame,f"{label} {conf:.2f}",(x1,y1-8),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),1)

        # Speak new alerts only
        new_alerts = alerts_set - prev_alerts_set
        if new_alerts and (time.time()-last_time)>cooldown:
            speak(", ".join(new_alerts))
            last_time = time.time()
        prev_alerts_set = alerts_set

        # Display
        cv2.imshow("SmartNav Debug", cv2.resize(frame,(320,240)))

        # Key handling
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q') or key == ord('Q'):
            speak("Quitting SmartNav")
            break
        elif key == ord('e') or key == ord('E'):
            speak("Emergency alert activated")
            send_guardian_alert()
        elif key == ord('i') or key == ord('I'):
            if nav_thread and nav_thread.is_alive():
                nav_stop_event.set()
                nav_thread.join(timeout=1)
                nav_stop_event.clear()
            mode="indoor"
            destination_set=False
            navigation_steps.clear()
            speak("Indoor mode activated")
            print("Mode => indoor")
        elif key == ord('o') or key == ord('O'):
            if nav_thread and nav_thread.is_alive():
                nav_stop_event.set()
                nav_thread.join(timeout=1)
                nav_stop_event.clear()
            mode="outdoor"
            destination_set=False
            navigation_steps.clear()
            speak("Outdoor mode activated. Where do you want to go?")
            print("Mode => outdoor. Asking destination...")

            dest_name = None
            for _ in range(3):
                dest_name = get_destination_voice(retries=1)
                if dest_name:
                    break
            if not dest_name:
                speak("Could not get destination. Cancelled navigation.")
                continue

            lat, lon = get_coordinates(dest_name)
            if lat is None:
                speak("Destination not found. Please try again.")
                continue

            steps = get_route_steps(current_lat, current_lon, lat, lon)
            if not steps:
                speak("No walking route found. Try another destination.")
                continue

            navigation_steps = steps
            destination_set=True
            nav_stop_event.clear()
            nav_thread = threading.Thread(target=navigation_worker,args=(navigation_steps,nav_stop_event),daemon=True)
            nav_thread.start()

finally:
    cap.release()
    cv2.destroyAllWindows()
    tts_queue.put(None)
    tts_thread.join(timeout=1)
    if nav_thread and nav_thread.is_alive():
        nav_stop_event.set()
        nav_thread.join(timeout=1)
    print("Exited SmartNav")
