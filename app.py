from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Change this to the correct Rasa server port (default is 5005)
RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get("message")
        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        # Send user message to Rasa
        response = requests.post(RASA_SERVER_URL, json={"sender": "user", "message": user_message})

        # Handle response errors
        if response.status_code != 200:
            return jsonify({"error": f"Failed to connect to Rasa: {response.status_code}"}), 500
        
        # Ensure response is JSON
        try:
            response_json = response.json()
        except ValueError:
            return jsonify({"error": "Invalid JSON response from Rasa"}), 500

        bot_messages = [resp.get("text", "") for resp in response_json]
        return jsonify({"messages": bot_messages})

    except Exception as e:
        return jsonify({"error": f"Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
