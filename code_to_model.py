# run local dog breed identifier model
import os
import json
import numpy as np
import pandas as pd
from keras.models import load_model
from keras.applications.resnet_v2 import preprocess_input
from PIL import Image

def run_model(image_path):
    # Load the pre-trained model
    model_path = os.path.join(os.path.dirname(__file__), 'dog_breed_identifier_model.h5')
    model = load_model(model_path)

    # Load and preprocess the image
    image = Image.open(image_path)
    image = image.resize((224, 224))  # Resize to match model input size
    image_array = np.array(image)
    image_array = preprocess_input(image_array)  # Preprocess for ResNet

    # Expand dimensions to match model input shape
    image_array = np.expand_dims(image_array, axis=0)

    # Make predictions
    predictions = model.predict(image_array)
    
    # Load breed labels
    with open(os.path.join(os.path.dirname(__file__), 'breed_labels.json'), 'r') as f:
        breed_labels = json.load(f)

    # Get the predicted breed
    predicted_breed_index = np.argmax(predictions[0])
    predicted_breed = breed_labels[str(predicted_breed_index)]

    return predicted_breedage_path
    # This function will be called to identify the dog breed from an image
def identify_dog_breed(image_path):
    try:
        breed = run_model(image_path)
        return f"The predicted dog breed is: {breed}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

identify_dog_breed("./dog_pictures/labrador/lab6.jpg")