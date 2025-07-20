from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

app = Flask(__name__)

# ✅ Load Firebase credentials from environment variable
firebase_config = os.environ.get("FIREBASE_CREDENTIALS_JSON")
if not firebase_config:
    raise ValueError("Missing FIREBASE_CREDENTIALS_JSON environment variable.")

cred_dict = json.loads(firebase_config)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)

@app.route('/send-notification', methods=['POST'])
def send_notification():
    data = request.get_json()
    fcm_token = data.get('fcmToken')
    student_name = data.get('studentName')
    entry_type = data.get('entryType')

    if not fcm_token or not student_name or not entry_type:
        return jsonify({'error': 'Missing required fields'}), 400

    title = "Check Notification"
    body = f"Your {student_name} is checked {entry_type}"

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=fcm_token
    )

    try:
        response = messaging.send(message)
        return jsonify({'messageId': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ Correct port and host binding for Railway
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4999))
    app.run(host='0.0.0.0', port=port)
