from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Simple in-memory store for demo purposes
contacts = []

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'email', 'message')):
        return jsonify({'success': False, 'error': 'Invalid payload'}), 400
    entry = {
        'name': data['name'],
        'email': data['email'],
        'message': data['message']
    }
    contacts.append(entry)
    print(f"Received contact: {entry}")
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
