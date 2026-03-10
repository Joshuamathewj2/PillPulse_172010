import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'
import tensorflow as tf
from tensorflow.keras.models import load_model

model = None
probability_model = None

def load_prediction_model():
    global model, probability_model
    if probability_model is None:
        model_path = os.environ.get('MODEL_PATH', 'C:/pillpulse/Handwritten-Prescription-Medicine-Recognition-master/PrescriptionDetection/home/FinalModel2.h5')
        print(f"Loading model from {model_path}")
        model = load_model(model_path)
        probability_model = tf.keras.Sequential([model, tf.keras.layers.Softmax()])
    return probability_model
