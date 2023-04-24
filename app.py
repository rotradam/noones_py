import os
import time
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
import json
import nacl.signing
import nacl.encoding
import base64

load_dotenv()

app = Flask(__name__)

OFFER_HASHES = os.getenv("OFFER_HASHES").split(',')
NOONES_AUTOGREETING_MESSAGE = os.getenv("NOONES_AUTOGREETING_MESSAGE")
NOONES_AUTOGREETING_DELAY = int(os.getenv("NOONES_AUTOGREETING_DELAY"))

# Replace the public key with the correct one for Noones
PUBLIC_KEY = os.getenv("PUBLIC_KEY")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Check for validation request
    if not request.json:
        challenge_header = request.headers.get('X-Noones-Request-Challenge')
        response = Response()
        response.headers['X-Noones-Request-Challenge'] = challenge_header
        return response

    # Validate the signature
    signature = request.headers.get('X-Noones-Signature')
    webhook_target_url = os.environ.get('WEBHOOK_TARGET_URL')
    signature_validation_payload = f'{webhook_target_url}:{request.data.decode("utf-8")}'

    public_key = nacl.signing.VerifyKey(
        base64.b64decode(PUBLIC_KEY))  # Use the correct public key here

    try:
        public_key.verify(signature_validation_payload.encode('utf-8'),
                          base64.b64decode(signature))
    except nacl.exceptions.BadSignatureError:
        return Response("Invalid signature", status=401)

    # Process the webhook
    event_data = request.json

    # Add your processing logic here
    print(event_data)

    return Response("OK", status=200)

@app.route('/trade-chat/get', methods=['POST'])
def get_trade_chat():
    access_token = get_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}

    trade_hash = request.form.get('trade_hash')

    if not trade_hash:
        return jsonify({"status": "error", "timestamp": int(time.time())}), 400

    # Fetch trade chat messages
    trade_chat_url = 'https://api.noones.com/noones/v1/trade-chat/get'
    data = {'trade_hash': trade_hash}
    response = requests.post(trade_chat_url, data=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        return jsonify({"data": response_data, "status": "success", "timestamp": int(time.time())}), 200
    else:
        return jsonify({"status": "error", "timestamp": int(time.time())}), 400

@app.route('/trade-chat/post', methods=['POST'])
def post_trade_chat():
    access_token = get_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}

    message = request.form.get('message')
    trade_hash = request.form.get('trade_hash')

    if not message or not trade_hash:
        return jsonify({"status": "error", "timestamp": int(time.time())}), 400

    # Post trade chat messages
    trade_chat_url = 'https://api.noones.com/noones/v1/trade-chat/post'
    data = {'trade_hash': trade_hash, 'message': message}
    response = requests.post(trade_chat_url, data=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        return jsonify({"data": response_data, "status": "success", "timestamp": int(time.time())}), 200
    else:
        return jsonify({"status": "error", "timestamp": int(time.time())}), 400

def send_greeting_message(trade_hash):
    access_token = get_access_token()
    trade_chat_url = 'https://api.noones.com/trade-chat/post'
    headers = {'Authorization': f'Bearer {access_token}'}
    data = {'trade_hash': trade_hash, 'message': NOONES_AUTOGREETING_MESSAGE}
    response = requests.post(trade_chat_url, json=data, headers=headers)

    if response.status_code == 200:
        print(f"Sent greeting message for trade hash: {trade_hash}")
    else:
        print(f"Error sending greeting message for trade hash: {trade_hash}")

def get_access_token():
    token_url = 'https://auth.noones.com/oauth2/token'
    client_id = os.getenv("NOONES_CLIENT_ID")
    client_secret = os.getenv("NOONES_CLIENT_SECRET")
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'noones:trade:get noones:trade-chat:post'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(token_url, data=data, headers=headers)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Error getting access token")

if __name__ == '__main__':
    app.run(port=int(os.getenv("PORT", 3000)), debug=True)