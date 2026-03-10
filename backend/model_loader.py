import os
# Force TensorFlow to use legacy Keras for .h5 compatibility
os.environ['TF_USE_LEGACY_KERAS'] = '1'
import tensorflow as tf
from tensorflow.keras.models import load_model

model = None
probability_model = None

def load_prediction_model():
    global model, probability_model
    if probability_model is None:
        # Default to local path for dev, allow override for Render via environment variable
        # For Render, upload your FinalModel2.h5 to the repo root and set MODEL_PATH=FinalModel2.h5
        model_path = os.environ.get('MODEL_PATH', 'FinalModel2.h5')
        
        # Check if file exists to avoid crashing
        if not os.path.exists(model_path):
            # Try absolute path from local machine if that fails (for dev)
            local_path = 'C:/pillpulse/Handwritten-Prescription-Medicine-Recognition-master/PrescriptionDetection/home/FinalModel2.h5'
            if os.path.exists(local_path):
                model_path = local_path
            else:
                print(f"CRITICAL: Model file not found at {model_path} or {local_path}")
                # Create a placeholder in memory to allow server to start, though prediction will fail
                # In production, make sure the model is in the repo!
                return None

        print(f"Loading model from {model_path}")
        try:
            model = load_model(model_path, compile=False)
            probability_model = tf.keras.Sequential([model, tf.keras.layers.Softmax()])
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
            
    return probability_model
