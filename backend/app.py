import os
import requests as req
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2

# Hardcoded schedules for the identified classes
MEDICINE_SCHEDULES = {
    "Hairbless": {
        "dosage": "1 Tablet",
        "frequency": "Twice Daily (BD)",
        "timing": ["09:00 AM", "09:00 PM"],
        "duration": "30 days",
        "instructions": "Take after food with water.",
        "food_interaction": "Avoid grapefruit juice.",
        "refill_reminder": "10 days"
    },
    "Lobate": {
        "dosage": "Apply thin layer",
        "frequency": "Once Daily (OD)",
        "timing": ["10:00 PM"],
        "duration": "14 days",
        "instructions": "Apply to affected area only.",
        "food_interaction": "No interactions.",
        "refill_reminder": "5 days"
    }
}

from model_loader import load_prediction_model
from preprocessor import preprocess_prescription

app = Flask(__name__)
# Enable CORS for all routes (important for cross-origin hosting)
CORS(app)

# Health check for Render
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "PillPulse Backend is healthy"}), 200

@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        model = load_prediction_model()
        
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        file = request.files["image"]
        image_bytes = file.read()

        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({"success": False, "error": "Could not decode image"}), 400

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter contours by size
        MIN_W, MIN_H = 40, 20
        MAX_W, MAX_H = img.shape[1] * 0.9, img.shape[0] * 0.9

        boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if MIN_W <= w <= MAX_W and MIN_H <= h <= MAX_H:
                boxes.append((x, y, w, h))

        # Sort top-to-bottom, left-to-right (reading order)
        boxes = sorted(boxes, key=lambda b: (b[1] // 40, b[0]))

        # Cap at 10 segments max
        boxes = boxes[:10]

        # Input size from model
        input_size = (160, 80) # Consistent with preprocessor.py

        if len(boxes) == 0:
            segment = cv2.resize(gray, input_size)
            boxes_to_predict = [segment]
        else:
            boxes_to_predict = []
            for (x, y, w, h) in boxes:
                crop = gray[y:y+h, x:x+w]
                resized = cv2.resize(crop, input_size)
                boxes_to_predict.append(resized)

        CLASS_NAMES = ["Hairbless", "Lobate"]
        best_per_class = {}

        for segment in boxes_to_predict:
            normalized = segment.astype("float32") / 255.0
            # Reshape for model (usually 1, 80, 160, 1) or similar
            # Checking model input shape dynamically
            try:
                if len(model.layers[0].input_shape) == 1: # list of shapes
                    raw_shape = model.layers[0].input_shape[0]
                else:
                    raw_shape = model.layers[0].input_shape
                
                if len(raw_shape) == 4:
                    if raw_shape[-1] == 1:
                        inp = normalized.reshape(1, input_size[1], input_size[0], 1)
                    else:
                        inp = np.stack([normalized]*3, axis=-1)
                        inp = inp.reshape(1, input_size[1], input_size[0], 3)
                else:
                    inp = normalized.reshape(1, -1)
            except:
                # Fallback to standard 1, 80, 160, 1
                inp = normalized.reshape(1, 80, 160, 1)

            preds = model.predict(inp, verbose=0)[0]

            for idx, conf in enumerate(preds):
                if idx < len(CLASS_NAMES):
                    name = CLASS_NAMES[idx]
                    conf_pct = float(conf) * 100
                    if conf_pct > 60:
                        if name not in best_per_class or conf_pct > best_per_class[name]:
                            best_per_class[name] = conf_pct

        # Build final medicines list
        medicines = []
        for name, conf in sorted(
            best_per_class.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            schedule = MEDICINE_SCHEDULES.get(name, {})
            medicines.append({
                "name": name,
                "confidence": round(conf, 1),
                "status": "identified",
                "dosage": schedule.get("dosage", "As prescribed"),
                "frequency": schedule.get("frequency", "As prescribed"),
                "timing": schedule.get("timing", []),
                "duration": schedule.get("duration", "As prescribed"),
                "instructions": schedule.get("instructions", ""),
                "food_interaction": schedule.get("food_interaction", ""),
                "refill_reminder": schedule.get("refill_reminder", "")
            })

        # If nothing passed the 60% threshold, return the top prediction from first box
        if len(medicines) == 0 and len(boxes_to_predict) > 0:
            segment = boxes_to_predict[0]
            normalized = segment.astype("float32") / 255.0
            inp = normalized.reshape(1, 80, 160, 1)
            preds = model.predict(inp, verbose=0)[0]
            best_idx = int(np.argmax(preds))
            if best_idx < len(CLASS_NAMES):
                name = CLASS_NAMES[best_idx]
                conf = float(preds[best_idx]) * 100
                schedule = MEDICINE_SCHEDULES.get(name, {})
                medicines = [{
                    "name": name,
                    "confidence": round(conf, 1),
                    "status": "identified",
                    "dosage": schedule.get("dosage", "As prescribed"),
                    "frequency": schedule.get("frequency", "As prescribed"),
                    "timing": schedule.get("timing", []),
                    "duration": schedule.get("duration", "As prescribed"),
                    "instructions": schedule.get("instructions", ""),
                    "food_interaction": schedule.get("food_interaction", ""),
                    "refill_reminder": schedule.get("refill_reminder", "")
                }]

        return jsonify({
            "success": True,
            "medicines": medicines,
            "total_found": len(medicines)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ═══════════════════════════════════════
# ESCALATION NOTIFICATION SYSTEM ENDPOINTS
# ═══════════════════════════════════════

# In-memory storage for demo — will reset on Render restarts
# Use a database for production persistence
PATIENTS = {}

def send_fcm_notification(token, title, body):
    """Send FCM notification via Firebase HTTP v1 API (fallback: legacy API)."""
    try:
        FCM_SERVER_KEY = os.environ.get('FCM_SERVER_KEY', '')
        if not FCM_SERVER_KEY:
            print('[FCM] No server key configured — skipping push')
            return {'success': False, 'reason': 'No FCM server key'}

        response = req.post(
            'https://fcm.googleapis.com/fcm/send',
            json={
                'to': token,
                'notification': {
                    'title': title,
                    'body': body,
                    'icon': 'https://pillpulse.vercel.app/logo.png', # Remote URL for icon
                    'click_action': 'https://pillpulse.vercel.app',
                },
                'webpush': {
                    'notification': {
                        'requireInteraction': True
                    }
                }
            },
            headers={
                'Authorization': f'key={FCM_SERVER_KEY}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f'[FCM] Error sending notification: {e}')
        return {'success': False, 'error': str(e)}

@app.route('/api/register-patient', methods=['POST'])
def register_patient():
    data = request.get_json()
    patient_code = data.get('patientCode')
    name = data.get('name')
    token = data.get('token')
    
    PATIENTS[patient_code] = {
        'name': name,
        'token': token,
        'caregivers': [],
        'dose_log': []
    }
    print(f'[Patient] Registered {name} with code {patient_code}')
    return jsonify({'success': True})

@app.route('/api/register-caregiver', methods=['POST'])
def register_caregiver():
    data = request.get_json()
    patient_code = data.get('patientCode')
    caregiver_name = data.get('caregiverName')
    relation = data.get('relation')
    token = data.get('token')

    if patient_code not in PATIENTS:
        return jsonify({'success': False, 'error': 'Patient code not found'}), 404

    PATIENTS[patient_code]['caregivers'].append({
        'name': caregiver_name,
        'relation': relation,
        'token': token
    })
    
    patient_name = PATIENTS[patient_code]['name']
    send_fcm_notification(
        token, 
        "\ud83c\udfe5 Connected to Patient", 
        f"You are now monitoring {patient_name}."
    )
    
    print(f'[Caregiver] Registered {caregiver_name} for patient {patient_code}')
    return jsonify({'success': True, 'patientName': patient_name})

@app.route('/api/patient-status', methods=['GET'])
def patient_status():
    patient_code = request.args.get('patientCode')
    if patient_code not in PATIENTS:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    
    patient = PATIENTS[patient_code]
    return jsonify({
        'success': True,
        'patientName': patient['name'],
        'doseLog': patient['dose_log'][-20:]
    })

@app.route('/api/log-dose', methods=['POST'])
def log_dose():
    data = request.get_json()
    patient_code = data.get('patientCode')
    medicine_name = data.get('medicineName')
    timing_slot = data.get('timingSlot')
    status = data.get('status')
    timestamp = data.get('timestamp')
    
    if patient_code in PATIENTS:
        PATIENTS[patient_code]['dose_log'].append({
            'medicineName': medicine_name,
            'timingSlot': timing_slot,
            'status': status,
            'timestamp': timestamp
        })
    return jsonify({'success': True})

@app.route('/api/notify-caregiver', methods=['POST'])
def notify_caregiver():
    """Send escalation notification to a caregiver via FCM."""
    data = request.get_json()
    patient_code = data.get('patientCode')
    medicine_name = data.get('medicineName')
    skip_count = data.get('skipCount')
    timing_slot = data.get('timingSlot')

    if patient_code not in PATIENTS:
        return jsonify({'success': False, 'error': 'Not found'}), 404
        
    patient = PATIENTS[patient_code]
    patient_name = patient['name']
    caregivers = patient['caregivers']
    
    count = 0
    fcm_title = f'\U0001f6a8 {patient_name} needs attention'
    fcm_body = f'{patient_name} has skipped their {medicine_name} dose '
    if skip_count:
        fcm_body += f'{skip_count} times today ({timing_slot}). '
    else:
        fcm_body += f'at {timing_slot}. '
    fcm_body += 'Please check on them immediately.'
    
    for c in caregivers:
        if c.get('token'):
            send_fcm_notification(c['token'], fcm_title, fcm_body)
            count += 1
            
    return jsonify({'success': True, 'count': count})

if __name__ == '__main__':
    # Load model on startup
    load_prediction_model()
    # Support RENDER port injection
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
