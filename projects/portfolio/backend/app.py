
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re

frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app = Flask(__name__, static_folder=None)
CORS(app)

@app.route('/')
def index():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    if not (name and email and message):
        return jsonify({'success': False, 'error': 'Missing required fields: name, email, and message'}), 400
    
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'error': 'Invalid email format'}), 400
    
    # Log the incoming data to the console for debugging
    print(f"Received contact submission: Name: {name}, Email: {email}, Message: {message}")

    return jsonify({'success': True, 'message': 'Thank you for your message! We will get back to you shortly.'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
