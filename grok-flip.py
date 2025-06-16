from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging to track interactions and errors
logging.basicConfig(filename='sms_llm.log', level=logging.INFO)

# URL of the local LLM server running on the MacBook
LLM_SERVER_URL = 'http://localhost:5000/generate'
host = '0.0.0.0' #TODO get ngrok url

@app.route('/sms', methods=['POST'])
def sms_webhook():
    """
    Handle incoming SMS messages from Twilio, process them as AI prompts,
    and send the AI response back to the sender.
    """
    try:
        # Extract the message body (prompt) and sender's phone number
        body = request.values.get('Body', '').strip()
        from_number = request.values.get('From', '')

        # Log the incoming message
        logging.info(f'Received message from {from_number}: {body}')

        # Check if the message is empty
        if not body:
            resp = MessagingResponse()
            resp.message('Please send a valid prompt.')
            logging.info('Sent response: Empty prompt message')
            return str(resp)

        # Send the prompt to the LLM server
        try:
            response = requests.post(
                LLM_SERVER_URL,
                json={'prompt': body},
                timeout=10  # Timeout after 10 seconds to avoid Twilio webhook timeout
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            ai_response = response.json().get('response', 'Error: No response from AI')
        except requests.RequestException as e:
            logging.error(f'Error communicating with LLM server: {str(e)}')
            ai_response = 'Error: Could not get response from AI'

        # Prepare and send the response back via Twilio
        resp = MessagingResponse()
        resp.message(ai_response)
        logging.info(f'Sent response to {from_number}: {ai_response}')
        return str(resp)

    except Exception as e:
        # Handle unexpected errors
        logging.error(f'Unexpected error: {str(e)}')
        resp = MessagingResponse()
        resp.message('An unexpected error occurred.')
        return str(resp)

if __name__ == '__main__':
    # Run the Flask app in debug mode (for development)
    app.run(debug=True, host=host, port=5001)