import subprocess
import sys
import os

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError:
        print(f"Failed to install {package}. You may need to install it manually.")
        sys.exit(1)

# Check and install required packages
required_packages = ['vosk', 'sounddevice', 'numpy', 'pyttsx3', 'requests']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"{package} not found. Attempting to install...")
        install_package(package)

# Now import the required modules
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import numpy as np
import pyttsx3
import requests
import json

# Download Vosk model if not present
model_path = "vosk-model-small-en-us-0.15"
if not os.path.exists(model_path):
    print("Downloading Vosk model...")
    import urllib.request
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    urllib.request.urlretrieve(url, "vosk-model.zip")
    import zipfile
    with zipfile.ZipFile("vosk-model.zip", 'r') as zip_ref:
        zip_ref.extractall(".")
    os.remove("vosk-model.zip")

# Initialize the recognizer and text-to-speech engine
model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    print("Listening...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        rec = KaldiRecognizer(model, 16000)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result['text']
                if text:
                    print(f"You said: {text}")
                    return text

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def get_ollama_response(prompt):
    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama2",
        "prompt": prompt
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        response_text = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if 'response' in data:
                    response_text += data['response']
        
        return response_text.strip()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama API: {e}")
        return "Sorry, I couldn't reach the AI model."

if __name__ == "__main__":
    import queue
    q = queue.Queue()

    while True:
        user_input = listen()
        if user_input:
            model_response = get_ollama_response(user_input)
            print(f"Ollama said: {model_response}")
            
            # Always speak the response
            speak(model_response)