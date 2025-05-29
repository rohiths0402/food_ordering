from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from functools import wraps
from bson.objectid import ObjectId
import paypalrestsdk
from flask_cors import CORS


app = Flask(__name__) 
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})


# Config
app.config["MONGO_URI"] = "mongodb://localhost:27017/food_ordering"
app.config["SECRET_KEY"] = "P3VG$w%2h@4zT#9n!6Kf&D7XeU^uZqLb"


mongo = PyMongo(app)

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": "ASynPwGjKT4hKHPrtXeK9P4QMeCSoU4fX0ZLekoYSGoT0PyVOJ5L-IA-RDC6MRpItwNGUssVnhv2GyTR",
    "client_secret": "EGtkClVtorItbUlHE-mshWdiPZHqnt3PF5sgcYz5cqLzYXqbUm88TpHzJfCh24zx-mLnPNgfgqLE4xCJ"
})

COUNTRY_TAX_CONFIG = {
    'India': {'tax_rate': 0.18, 'currency': 'INR', 'symbol': '₹'},
    'America': {'tax_rate': 0.07, 'currency': 'USD', 'symbol': '$'}
}



def access_control(allowed_roles, check_country=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = request.headers.get('Role', '').lower()
            user_id = request.headers.get('User-Id')
            country = request.headers.get('Country', '').capitalize()

            if not role or not user_id:
                return jsonify({'message': 'Missing Role or User-Id headers'}), 401

            if role not in allowed_roles:
                return jsonify({'message': 'Access denied: invalid role'}), 403

            if check_country:
                if not country or country not in COUNTRY_TAX_CONFIG:
                    return jsonify({'message': 'Invalid or missing country header'}), 403

            request.user = {'role': role, 'id': user_id, 'country': country}
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = mongo.db.users.find_one({'username': username})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    # Return user info (no JWT)
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'country': user['country'],
            'role': user['role']
        }
    })

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', '').lower().strip()
    country = data.get('country', '').capitalize().strip()

    if not username or not password or role not in ['admin', 'manager', 'member'] or country not in COUNTRY_TAX_CONFIG:
        return jsonify({'message': 'Invalid signup data'}), 400

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'User already exists'}), 400

    hashed_pw = generate_password_hash(password)
    user = {'username': username, 'password': hashed_pw, 'role': role, 'country': country}
    result = mongo.db.users.insert_one(user)

    return jsonify({'message': 'User created', 'id': str(result.inserted_id)}), 201


# Cart
@app.route('/cart', methods=['GET'])

@access_control(['admin', 'manager', 'member'])
def get_cart():
    user_id = request.user['id']
    cart = mongo.db.carts.find_one({'user_id': user_id})
    return jsonify({'cartItems': cart['items'] if cart else []})

@app.route('/cart', methods=['PUT'])

@access_control(['admin', 'manager', 'member'])
def update_cart():
    user_id = request.user['id']
    data = request.json
    cart_items = data.get('cartItems', [])
    mongo.db.carts.update_one(
        {'user_id': user_id},
        {'$set': {'items': cart_items, 'updated_at': datetime.datetime.utcnow()}},
        upsert=True
    )
    return jsonify({'message': 'Cart synced'}), 200

# Restaurants
@app.route('/restaurants', methods=['GET'])

@access_control(['admin', 'manager', 'member'])
def list_restaurants():
    country = request.user['country']
    restaurants = list(mongo.db.restaurants.find({'country': country}))
    for r in restaurants:
        r['_id'] = str(r['_id'])
    return jsonify(restaurants)

@app.route('/food', methods=['GET'])
@access_control(['admin', 'manager', 'member'])
def list_food_items():
    country = request.user.get('country')
    if not country:
        return jsonify({"error": "Country not found in user data"}), 400

    foods = []
    restaurants = mongo.db.restaurants.find({'country': country})
    for restaurant in restaurants:
        items = restaurant.get('items', [])
        if isinstance(items, list):
            foods.extend(items)

    return jsonify(foods)


# Orders
@app.route('/orders', methods=['POST'])

@access_control(['admin', 'manager', 'member'], check_country=True)
def create_order():
    user_id = request.user['id']
    country = request.user['country']
    cart = mongo.db.carts.find_one({'user_id': user_id})
    if not cart or not cart.get('items'):
        return jsonify({'message': 'Cart is empty'}), 400

    cart_items = cart['items']
    subtotal = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in cart_items)
    tax_rate = COUNTRY_TAX_CONFIG[country]['tax_rate']
    tax = subtotal * tax_rate
    total = subtotal + tax

    order = {
        'user_id': user_id,
        'items': cart_items,
        'status': 'created',
        'country': country,
        'created_at': datetime.datetime.utcnow(),
        'pricing': {
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'total': round(total, 2),
            'currency': COUNTRY_TAX_CONFIG[country]['currency'],
            'symbol': COUNTRY_TAX_CONFIG[country]['symbol']
        }
    }

    result = mongo.db.orders.insert_one(order)
    mongo.db.carts.delete_one({'user_id': user_id})

    return jsonify({
        'message': 'Order created',
        'order_id': str(result.inserted_id),
        'pricing': order['pricing']
    }), 201

@app.route('/orders/<order_id>/checkout', methods=['POST'])

@access_control(['admin', 'manager'], check_country=True)
def checkout_order(order_id):
    order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
    if not order or order['country'].lower() != request.user['country'].lower() or order['status'] != 'created':
        return jsonify({'message': 'Invalid order state or access denied'}), 403

    total_amount = order['pricing']['total']
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:5000/payment/execute",
            "cancel_url": "http://localhost:5000/payment/cancel"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "Order Payment",
                    "sku": "001",
                    "price": str(total_amount),
                    "currency": order['pricing']['currency'],
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(total_amount),
                "currency": order['pricing']['currency']
            },
            "description": "Food order payment"
        }]
    })

    if payment.create():
        mongo.db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {'status': 'payment_pending', 'paypal_payment_id': payment.id}}
        )
        for link in payment.links:
            if link.method == "REDIRECT":
                return jsonify({'redirect_url': str(link.href)}), 202
    else:
        return jsonify({'message': 'Payment creation failed', 'error': payment.error}), 500

@app.route('/payment/execute', methods=['GET'])
def execute_payment():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        mongo.db.orders.update_one({'paypal_payment_id': payment_id}, {'$set': {'status': 'paid'}})
        return jsonify({'message': 'Payment successful'})
    else:
        return jsonify({'message': 'Payment execution failed', 'error': payment.error}), 500

if __name__ == '__main__':
    app.run(debug=True)