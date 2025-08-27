# load dog breed identification model from folder
# write test function to check dog image classification
import os
import json
import numpy as np 
import pandas as pd 
from tensorflow import keras
import tf_keras as k3
from sklearn.preprocessing import LabelEncoder


from keras.models import load_model
from keras.applications.resnet_v2 import preprocess_input
from PIL import Image


# def load_model(model_path):
#     """
#     Load the dog breed identification model from the specified path.
    
#     Args:
#         model_path (str): Path to the model directory.
    
#     Returns:
#         dict: Model configuration and parameters.
#     """
#     if not os.path.exists(model_path):
#         raise FileNotFoundError(f"Model path {model_path} does not exist.")
    
#     with open(os.path.join(model_path, 'model_config.json'), 'r') as f:
#         model_config = json.load(f)
    
#     return model_config

def test_model(image_path):
    """
    Test the dog breed identification model with a given image.
    
    Args:
        model (dict): The loaded model configuration.
        image_path (str): Path to the image to be classified.
    
    Returns:
        str: Predicted dog breed.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image path {image_path} does not exist.")
    
    from keras.layers import TFSMLayer
    encoder = LabelEncoder()

    # Replace with the correct call_endpoint if different
    # model = TFSMLayer('./model', call_endpoint='serving_default')
    model = k3.models.load_model('./model', compile=False)


    im_size = 224  # Set your image size here
    pred_img_path = image_path
    try:
        pred_img_array = Image.open(pred_img_path)
        pred_img_array = pred_img_array.convert('RGB')  # Ensure image is in RGB mode
    except Exception as e:
        raise ValueError(f"Cannot open image file {pred_img_path}: {e}")
    pred_img_array = pred_img_array.resize((im_size, im_size))
    pred_img_array = preprocess_input(np.expand_dims(np.array(pred_img_array).astype(np.float32), axis=0))

    # TFSMLayer is a layer, so we need to call it directly
    pred_label = model(pred_img_array)

    pred_label = np.argmax(pred_label, axis=1)

    print("Predicted Label for this Dog is :", pred_label)

    # match the encoder to the labels csv file
    labels_df = pd.read_csv('./labels.csv')
    encoder.fit(labels_df['breed'].values)
    pred_breed = encoder.inverse_transform(pred_label)
    print("Predicted Breed for this Dog is :", pred_breed)
    

test_image = './dog_pictures/german_shepherd/germanShep4.jpg'
test_model(test_image)