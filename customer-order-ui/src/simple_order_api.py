from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# In-memory order queue (for demo)
orders = []

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'product_name' not in data:
        return jsonify({'error': 'Missing product_name'}), 400
    order = {
        'id': len(orders) + 1,
        'product_name': data['product_name'],
        'product_details': data.get('product_details', {})
    }
    orders.append(order)
    # Here you would publish to MQTT or forward to orchestrator
    return jsonify(order), 201

@app.route('/orders', methods=['GET'])
def list_orders():
    return jsonify(orders)

if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
