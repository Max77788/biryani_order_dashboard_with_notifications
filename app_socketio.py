from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, emit
import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

app = Flask(__name__)
socketio = SocketIO(app)

client = MongoClient(os.environ.get("MONGODB_URI"))
restaurant_name = os.environ.get("RESTAURANT")
order_number_counter = 1
collection_name = os.getenv("MODE", "test")  # Default to "test" if not defined

if restaurant_name == "Biryani":
    orders_db = client.orders_biryani
elif restaurant_name == "GamaBC":
    orders_db = client.orders_gamabc

@app.route('/orders', methods=['GET', 'POST'])
def add_order_record():
    global order_number_counter
    
    if request.method == 'POST':
        data = request.json
        items_data = data.get('items', [])
        timestamp_utc = datetime.utcnow().strftime('%d.%m %H:%M')
        order_to_pass = {"orderNumber":order_number_counter, 
                         "items":[{'name':item['name'], 'quantity':item['quantity']} for item in items_data], 
                         "timestamp": timestamp_utc,
                         "published":False}
        order_collection = orders_db.test_notification if collection_name == "test" else orders_db.production
        order_number_counter += 1

        order_collection.insert_one(order_to_pass)
        document_to_post = list(order_collection.find().sort('_id', -1).limit(1))[0]
        result = order_collection.update_one({'_id': document_to_post['_id']}, {'$set': {'published': True}})
        if result.matched_count > 0:
            socketio.emit('order_status', {'msg': 'New Order Was Added!'}, room=None)
            return "Document updated successfully. Published set to True."
        return "Document not found for update."
    elif request.method == 'GET':
        return 'Send a POST request to submit an order.'

@app.route('/orders/view', methods=['GET'])
def view_orders():
    return render_template('orders_socketio.html', restaurant_name=restaurant_name)


@app.route('/api/orders', methods=['GET'])
def api_orders():
    order_collection = orders_db.test_notification if collection_name == "test" else orders_db.production
    orders = list(order_collection.find())
    orders_list = [{
        'orderId': order['orderNumber'],
        'timestamp': order['timestamp'],
        'foods': order['items'],
        'published': order['published']
    } for order in orders]
    return jsonify(orders=orders_list)



@app.route('/privacy-policy', methods=['GET'])
def view_policy():
    return render_template('policy.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
