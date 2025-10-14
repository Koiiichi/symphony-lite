
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    # Basic validation
    if not all([name, email, message]):
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400

    # Simulate a successful contact form submission handling
    return jsonify({'success': True, 'message': 'Contact information received successfully!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
