from flask import Flask, request, render_template, jsonify
import os
#from mongoengine import connect, disconnect
#from flask_mongoengine import MongoEngine
#from models.models_mongo import Order, Item
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

load_dotenv(find_dotenv())

app = Flask(__name__)

#disconnect()

#connect(host = os.getenv("MONGODB_URI"))

#app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  # Set a secret key for security purposes
#app.config['MONGODB_URI'] = os.getenv("MONGODB_URI")
app.config['MONGODB_HOST'] = os.getenv("MONGODB_URI")
  
# use a database named "myDatabase"
#db = MongoEngine(app)

client = MongoClient(os.environ.get("MONGODB_URI"))

restaurant_name = os.environ.get("RESTAURANT")

if restaurant_name == "Biryani":
  orders_db = client.orders_biryani
elif restaurant_name == "GamaBC":
  orders_db = client.orders_gamabc

order_number_counter = 1

collection_name = os.getenv("MODE", "test")  # Default to "test" if not defined

@app.route('/', methods=['GET'])
def hi():
    return "Hello World"

@app.route('/orders', methods=['GET', 'POST'])
def add_order_record():
    global order_number_counter
    
    if request.method == 'POST':
        data = request.json
        print("POST order on orders endpoint: ", data)
        items_data = data.get('items', [])  # Default to an empty list if not provided
        
        # Get current UTC time and format it as dd.mm hh:mm
        timestamp_utc = datetime.utcnow().strftime('%d.%m %H:%M')

        # Create Item instances for each item in the request
        #items = [Item(name=item['name'], quantity=item['quantity']) for item in items_data]
        
        order_to_pass = {"orderNumber":order_number_counter, 
                         "items":[{'name':item['name'], 'quantity':item['quantity']} for item in items_data], 
                         "timestamp": timestamp_utc,
                         "published":False}
        
        print(order_to_pass, "\n\n\n\n")


        # Depending on the mode, save to the appropriate collection
        if collection_name == "test":
            order_collection = orders_db.test
        else:
            order_collection = orders_db.production
        
        print(type(order_collection))

        # Create a new Order instance
        #order = Order(items=items, orderNumber=order_number_counter)
        
        order_number_counter += 1
        if 'items' in data:
            # Save the order to the selected collection and keep the reference
            order_collection.insert_one(order_to_pass)  # Assuming Order has a to_mongo method       
            last_inserted_document = order_collection.find().sort('_id', -1).limit(1)
            # Since `find` returns a cursor, we convert it to a list to access the document
            # If there is a document, it will be the first in the list
            if last_inserted_document:
                document_to_post = list(last_inserted_document)[0]
                print(document_to_post)
                # Update the 'published' attribute of the fetched document to True
                result = order_collection.update_one({'_id': document_to_post['_id']}, {'$set': {'published': True}})

                # Check if the update was successful
                if result.matched_count > 0:
                    print("Document updated successfully. Published set to True.")
                    return "Document updated successfully. Published set to True."
                else:
                    print("Document not found for update.")
                    return "Document not found for update."
        return jsonify({"response":"Order Successfully Posted with \"published:False\"!"})
        
        if 'action' in data:

            if data["action"] == "PUBLISH_THE_ORDER":
                last_inserted_document = order_collection.find().sort('_id', -1).limit(1)

                # Since `find` returns a cursor, we convert it to a list to access the document
                # If there is a document, it will be the first in the list
                if last_inserted_document:
                    document_to_post = list(last_inserted_document)[0]
                    print(document_to_post)
                    # Update the 'published' attribute of the fetched document to True
                    result = order_collection.update_one({'_id': document_to_post['_id']}, {'$set': {'published': True}})

                    # Check if the update was successful
                    if result.matched_count > 0:
                        print("Document updated successfully. Published set to True.")
                        return "Document updated successfully. Published set to True."
                    else:
                        print("Document not found for update.")
                        return "Document not found for update."
            
            elif data["action"] == "DELETE_THE_ORDER":
                last_inserted_document = order_collection.find().sort('_id', -1).limit(1)
                if last_inserted_document:
                    document_to_delete = list(last_inserted_document)[0]
                    print(document_to_delete)

                    # Delete the fetched document
                    delete_result = order_collection.delete_one({'_id': document_to_delete['_id']})

                    # Check if the delete was successful
                    if delete_result.deleted_count > 0:
                        print("Document deleted successfully.")
                        return "Document deleted successfully."
                    else:
                        print("No document was deleted.")
                        return "No document was deleted."
    
    elif request.method == 'GET':
        # For a GET request, return a simple message
        return 'Send a POST request to submit an order.'


@app.route('/orders/view', methods=['GET'])
def view_orders():
    
    if collection_name == "test":
        order_collection = orders_db.test
    else:
        order_collection = orders_db.production
    
    # Query all orders from the database
    orders = list(order_collection.find())
    
    print(orders, "\n\n\n\n\n\n\n\n\n\n")

    # Format orders for display
    orders_list = []
    for order in orders:
        # Assuming 'orderNumber' is already a string that represents the order ID
        # If 'orderNumber' is not defined in your Order model, you might want to use str(order.id)
        order_info = {
            'orderId': order['orderNumber'],
            'foods': [item for item in order['items']],
            'timestamp': order['timestamp'],
            'published':order['published']
        }
        orders_list.append(order_info)
        print("Orders_list: \n\n", orders_list, "\n\n\n\n")

    # Render the HTML page with orders
    return render_template('orders.html', orders=orders_list, restaurant_name=restaurant_name)

    # For simplicity, return JSON representation of the orders
    #return jsonify(orders=orders_list)

@app.route('/privacy-policy', methods=['GET'])
def view_policy():
    return render_template('policy.html')

if __name__ == '__main__':
    app.run(debug=True)