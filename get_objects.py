import pandas as pd
import numpy as np
from ultralytics import YOLO
import requests
from PIL import Image
from io import BytesIO
import torch
from concurrent.futures import ThreadPoolExecutor

# Load the YOLOv8 pre-trained model with GPU support
device = 'cuda' if torch.cuda.is_available() else 'cpu'  # Check if GPU is available
model = YOLO('yolov8s.pt')  # Use the YOLOv8 small model for better accuracy
model.to(device)  # Load the model on the specified device (GPU or CPU)
vehicle_classes = {
    'car': 2,         # COCO class ID for car
    'motorbike': 3,   # COCO class ID for motorcycle
    'truck': 7,       # COCO class ID for truck
    'bus': 5,         # COCO class ID for bus
    'train': 6        # COCO class ID for train
}

# Function to fetch and process image
def fetch_and_process_image(image_url):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image = image.resize((640, 640))  # Resize for YOLOv8
        return image
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

# Batch processing for YOLO
def detect_vehicles(images):
    results = model(images)
    counts_list = []
    for result in results: 
        counts = {vehicle: 0 for vehicle in vehicle_classes.keys()}
        for box in result.boxes:
            class_id = int(box.cls[0])  # Detected class ID
            for vehicle, coco_id in vehicle_classes.items():
                if class_id == coco_id:
                    counts[vehicle] += 1
        counts_list.append(counts)
    return counts_list

# Load dataset and initialize columns
traffic = pd.read_csv(r"traffic_images_2.csv")
traffic2 = traffic[40902:]
for vehicle in vehicle_classes.keys():
    traffic2[f'num_{vehicle}s'] = 0

# Fetch images and run detection
batch_size = 8
image_urls = traffic2['image_url'].tolist()

for i in range(0, len(image_urls), batch_size):
    batch_urls = image_urls[i:i+batch_size]
    with ThreadPoolExecutor() as executor:
        images = list(executor.map(fetch_and_process_image, batch_urls))
    images = [img for img in images if img is not None]  # Filter out failed images

    if images:
        counts_list = detect_vehicles(images)
        for j, counts in enumerate(counts_list):
            index = i + j
            for vehicle, count in counts.items():
                traffic2.at[index, f'num_{vehicle}s'] = count

# Save updated dataset
traffic2_predicted_path = "traffic2_rest40902_predicted.csv"
traffic2.to_csv(traffic2_predicted_path, index=False)
print(f"Predictions added and saved to {traffic2_predicted_path}") 