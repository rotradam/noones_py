import os
import time
import requests
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

app = Flask(__name__)

OFFER_HASHES = os.getenv("OFFER_HASHES").split(',')
NOONES_AUTOGREETING_MESSAGE = os.getenv("NOONES_AUTOGREETING_MESSAGE")
NOONES_AUTOGREETING_DELAY = int(os.getenv("NOONES_AUTOGREETING_DELAY"))

print("OFFER_HASHES:", OFFER_HASHES)


@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_event = request.json
    print("Received webhook event:", webhook_event)
    
    if webhook_event['event'] == 'trade.started' and webhook_event['data']['offer_hash'] in OFFER_HASHES:
        time.sleep(NOONES_AUTOGREETING_DELAY / 1000)
        send_greeting_message(webhook_event['data']['trade_hash'])

    return "OK", 200

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
