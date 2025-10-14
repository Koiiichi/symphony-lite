from flask import Flask, request, jsonify
from flask_cors import CORS

# Serve the frontend from the 'frontend' directory
app = Flask(__name__, static_folder='frontend', static_url_path='/')
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    # Serve the frontend index.html from the static folder
    return app.send_static_file('index.html')

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
