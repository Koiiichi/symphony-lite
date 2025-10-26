from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# Serve the frontend from the '../frontend' directory (one level up)
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app = Flask(__name__, static_folder=None)  # Disable default static folder
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    # Serve the frontend index.html from the frontend directory
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    if not (name and email and message):
        return jsonify({'success': False, 'error': 'Missing required fields: name, email, and message'}), 400

    # In a real application, you would send an email or store the message here.
    return jsonify({'success': True, 'message': 'Thank you for your message! We will get back to you shortly.'}), 200

if __name__ == '__main__':
    # Run on all interfaces so you can access from localhost:5000
    app.run(debug=True, host='0.0.0.0', port=5000)
