from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Firebase Admin SDK
try:
    firebase_config = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if not firebase_config:
        logger.error("FIREBASE_CREDENTIALS_JSON environment variable is not set.")
        raise ValueError("FIREBASE_CREDENTIALS_JSON environment variable is not set.")

    cred_dict = json.loads(firebase_config)
    required_fields = ["project_id", "private_key", "client_email"]
    if not all(field in cred_dict for field in required_fields):
        logger.error("FIREBASE_CREDENTIALS_JSON is missing required fields.")
        raise ValueError("FIREBASE_CREDENTIALS_JSON is missing required fields.")
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, name='school-guardian')
    logger.info("Firebase Admin SDK initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
    raise

@app.route('/send-notification', methods=['POST'])
def send_notification():
    try:
        data = request.get_json(silent=True)
        if not data:
            logger.warning("No JSON data provided in request.")
            return jsonify({'error': 'No JSON data provided'}), 400

        fcm_token = data.get('fcmToken')
        student_name = data.get('studentName')
        entry_type = data.get('entryType')

        if not fcm_token or not student_name or not entry_type:
            logger.warning(f"Missing fields: fcmToken={fcm_token}, studentName={student_name}, entryType={entryType}")
            return jsonify({'error': 'Missing required fields'}), 400

        valid_entry_types = ['in', 'out']
        if entry_type.lower() not in valid_entry_types:
            logger.warning(f"Invalid entryType: {entry_type}")
            return jsonify({'error': f'Invalid entryType, must be one of {valid_entry_types}'}), 400

        title = "Attendance Notification"
        body = f"{student_name} has been checked {entry_type.lower()}."

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=fcm_token
        )

        response = messaging.send(message)
        logger.info(f"Notification sent successfully: messageId={response}")
        return jsonify({'messageId': response}), 200

    except messaging.FirebaseError as e:
        logger.error(f"Firebase error sending notification: {str(e)} (code: {e.code})")
        if e.code in ('messaging/invalid-registration-token', 'messaging/registration-token-not-registered'):
            return jsonify({'error': 'Invalid or unregistered FCM token'}), 400
        elif e.code == 'messaging/mismatch-sender-id':
            return jsonify({'error': 'FCM token does not match sender ID'}), 400
        elif e.code == 'messaging/quota-exceeded':
            return jsonify({'error': 'FCM quota exceeded, try again later'}), 429
        else:
            return jsonify({'error': f'Firebase error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error sending notification: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))  # Default to 8080 to match Railway
    logger.info(f"Starting Flask app on host 0.0.0.0 and port {port} (development mode)")
    app.run(host='0.0.0.0', port=port)