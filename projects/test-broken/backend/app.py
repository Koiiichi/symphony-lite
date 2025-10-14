from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='../frontend')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    
    # Intentionally broken: return 501 to simulate error
    return jsonify({
        'success': False,
        'message': 'Contact endpoint not implemented'
    }), 501

if __name__ == '__main__':
    app.run(debug=True, port=5000)
