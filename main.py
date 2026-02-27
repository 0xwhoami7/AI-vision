import cv2
import eel
import time
import threading
import requests
import re
from config import Config
from PIL import Image
import io
from datetime import datetime
import google.generativeai as gai

gai.configure(api_key=Config['API-KEY'])
model = gai.GenerativeModel("gemini-1.5-flash")
REQUEST_TIMEOUT_SECONDS = 8
MAX_COMMAND_LENGTH = 300

def get_location_from_ip():
    try:
        ip_info_url = "https://ipinfo.io"
        response = requests.get(ip_info_url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        
        # Extract location data
        location = data['loc'].split(',')
        latitude = location[0]
        longitude = location[1]
        
        return latitude, longitude
    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"Error: {e}")
        return None, None

eel.init('web')


camera = cv2.VideoCapture(0)
weather_api_url = "https://api.api-ninjas.com/v1/weather"

def get_video_frame():
    ret, frame = camera.read()
    if not ret:
        return None
    return frame

def vision():
    while True:
        frame = get_video_frame()
        if frame is not None:
            cv2.imshow("Video Feed", frame)
        else:
            print("Failed to decode frame.")
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        time.sleep(0.03)

@eel.expose
def process_command(command: str):
    if not isinstance(command, str):
        return "Invalid command format."

    safe_command = re.sub(r"[\x00-\x1f\x7f]", "", command).strip()
    if not safe_command:
        return "Please provide a valid voice command."
    if len(safe_command) > MAX_COMMAND_LENGTH:
        return "Command is too long. Please keep it under 300 characters."

    frame = get_video_frame()
    if frame is not None:
        response = process_frame_with_gemini(frame, safe_command)
        return response
    return "Failed to capture frame."

def process_frame_with_gemini(frame, data: str):
    ret, buffer = cv2.imencode('.jpg', frame)
    image = buffer.tobytes()
    image = Image.open(io.BytesIO(image))
    response = model.generate_content([image, (data + " in 30 words with no special characters.")])
    return response.text

@eel.expose
def start_weather_updates():
    try:
        lat, lon = get_location_from_ip()
        
        if lat is None or lon is None:
            return "Failed to get location."

        headers = {'X-Api-Key': Config['API_KEY_weather']}
        params = {'lat': lat, 'lon': lon}

        response = requests.get(
            weather_api_url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        weather_data = {
            'temp': data.get('temp', 'N/A'),
            'humidity': data.get('humidity', 'N/A'),
            'wind_speed': data.get('wind_speed', 'N/A'),
            'weather_condition': data.get('condition', 'N/A'),  
            'sunrise': convert_unix_to_time(data.get('sunrise', 0)),  
            'sunset': convert_unix_to_time(data.get('sunset', 0))   
        }
        eel.update_weather(weather_data)
    except (requests.RequestException, ValueError, TypeError) as e:
        print(f"Error: {e}")
        eel.update_weather_error("Unable to fetch weather data right now.")

def convert_unix_to_time(timestamp):
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime("%I:%M %p")

threading.Thread(target=vision, daemon=True).start()

eel.start('index.html', size=(800, 600))

camera.release()
cv2.destroyAllWindows()
