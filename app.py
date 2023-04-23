import os
import time
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

OFFER_HASHES = os.getenv("OFFER_HASHES").split(',')
NOONES_AUTOGREETING_MESSAGE = os.getenv("NOONES_AUTOGREETING_MESSAGE")
NOONES_AUTOGREETING_DELAY = int(os.getenv("NOONES_AUTOGREETING_DELAY"))

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        webhook_event = request.json
        print(f"Webhook data: {webhook_event}")

        if webhook_event['event'] == 'trade.started' and webhook_event['data']['offer_hash'] in OFFER_HASHES:
            time.sleep(NOONES_AUTOGREETING_DELAY / 1000)
            send_greeting_message(webhook_event['data']['trade_hash'])

        return "OK", 200

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return "Error", 400

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
