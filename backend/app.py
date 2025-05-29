from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import datetime
from functools import wraps
from bson.objectid import ObjectId
import paypalrestsdk
import jwt

app = Flask(__name__)

# App Config
app.config["MONGO_URI"] = "mongodb://localhost:27017/food_ordering"


# PayPal Config
paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": "ASynPwGjKT4hKHPrtXeK9P4QMeCSoU4fX0ZLekoYSGoT0PyVOJ5L-IA-RDC6MRpItwNGUssVnhv2GyTR",
    "client_secret": "EGtkClVtorItbUlHE-mshWdiPZHqnt3PF5sgcYz5cqLzYXqbUm88TpHzJfCh24zx-mLnPNgfgqLE4xCJ"
})

# Constants
COUNTRY_TAX_CONFIG = {
    'India': {'tax_rate': 0.18, 'currency': 'INR', 'symbol': '₹'},
    'America': {'tax_rate': 0.07, 'currency': 'USD', 'symbol': '$'}
}

mongo = PyMongo(app)

def getIP(ip):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/country_name/")
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"IP API error: {e}")
    return None

def generate_token(user_id):
    payload = {
        'user_id': str(user_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, algorithm='HS256')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password'].strip()
    role = data.get('role', '').lower().strip()
    country = data.get('country', '').capitalize().strip()

    if role not in ['admin', 'manager', 'member']:
        return jsonify({'message': 'Invalid role'}), 400

    if country not in COUNTRY_TAX_CONFIG:
        return jsonify({'message': 'Invalid or missing country'}), 400

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)

    user_data = {
        'username': username,
        'password': hashed_password,
        'role': role,
        'country': country
    }

    result = mongo.db.users.insert_one(user_data)
    return jsonify({'message': 'User created', 'id': str(result.inserted_id)}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    username = data['username']
    password = data['password']
    user = mongo.db.users.find_one({'username': username})

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = generate_token(user['_id'])
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'username': user['username'],
            'role': user['role'],
            'country': user['country']
        }
    })

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth = request.headers['Authorization']
            if auth.startswith("Bearer "):
                token = auth.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, algorithms=["HS256"])
            current_user = mongo.db.users.find_one({'_id': ObjectId(data['user_id'])})
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
            request.user = {
                'id': str(current_user['_id']),
                'username': current_user['username'],
                'role': current_user['role'],
                'country': current_user['country']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired!'}), 401
        except Exception as e:
            return jsonify({'message': f'Token is invalid: {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated

def access_control(allowed_roles, check_country=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = getattr(request, 'user', None)
            if not user:
                return jsonify({'message': 'Unauthorized access'}), 403

            if user['role'].lower() not in allowed_roles:
                return jsonify({'message': 'Insufficient role access'}), 403

            if check_country:
                req_country = request.args.get('country') or (request.json and request.json.get('country'))
                if req_country and req_country.lower() != user['country'].lower():
                    return jsonify({'message': 'Access denied to other country data'}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/restaurants', methods=['GET'])
@token_required
@access_control(['admin', 'manager', 'member'])
def list_restaurants():
    country = request.user['country']
    restaurants = list(mongo.db.restaurants.find({'country': country}))
    for r in restaurants:
        r['_id'] = str(r['_id'])
    return jsonify(restaurants)

@app.route('/orders', methods=['POST'])
@token_required
@access_control(['admin', 'manager', 'member'], check_country=True)
def create_order():
    data = request.json
    restaurant_id = data.get('restaurant_id')
    items = data.get('items', [])

    if not restaurant_id or not items:
        return jsonify({'message': 'restaurant_id and items are required'}), 400

    try:
        restaurant = mongo.db.restaurants.find_one({'_id': ObjectId(restaurant_id)})
    except:
        return jsonify({'message': 'Invalid restaurant_id'}), 400

    if not restaurant or restaurant['country'].lower() != request.user['country'].lower():
        return jsonify({'message': 'Restaurant not found or access denied'}), 403

    ordered_items = []
    subtotal = 0.0

    for item_name in items:
        food_item = next((f for f in restaurant['food'] if f['name'] == item_name), None)
        if not food_item:
            return jsonify({'message': f'Item "{item_name}" not found'}), 400
        subtotal += float(food_item['price'])
        ordered_items.append(food_item)

    country_info = COUNTRY_TAX_CONFIG[restaurant['country']]
    tax = subtotal * country_info['tax_rate']
    total = subtotal + tax

    order = {
        'user_id': request.user['id'],
        'restaurant_id': str(restaurant['_id']),
        'items': ordered_items,
        'status': 'created',
        'country': restaurant['country'],
        'created_at': datetime.datetime.utcnow(),
        'pricing': {
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'total': round(total, 2),
            'currency': country_info['currency'],
            'symbol': country_info['symbol']
        }
    }

    result = mongo.db.order.insert_one(order)
    return jsonify({'message': 'Order created', 'order_id': str(result.inserted_id), 'pricing': order['pricing']}), 201
@app.route('/categories', methods=['GET'])
@token_required
@access_control(['admin', 'manager', 'member'])
def get_categories():
    country = request.user['country']
    categories = list(mongo.db.categories.find({'country': country}))
    for cat in categories:
        cat['_id'] = str(cat['_id'])
    return jsonify(categories)

@app.route('/orders/<order_id>/checkout', methods=['POST'])
@token_required
@access_control(['admin', 'manager'], check_country=True)
def place_order(order_id):
    order = mongo.db.order.find_one({'_id': ObjectId(order_id)})
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    if order['country'].lower() != request.user['country'].lower() or order['status'] != 'created':
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
        mongo.db.order.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {'status': 'payment_pending', 'paypal_payment_id': payment.id}}
        )
        for link in payment.links:
            if link.method == "REDIRECT":
                return jsonify({'redirect_url': str(link.href)}), 202
    else:
        return jsonify({'message': 'Payment failed', 'error': payment.error}), 500

@app.route('/orders/<order_id>/cancel', methods=['POST'])
@token_required
@access_control(['admin', 'manager'], check_country=True)
def cancel_order(order_id):
    order = mongo.db.order.find_one({'_id': ObjectId(order_id)})
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    if order['country'].lower() != request.user['country'].lower() or order['status'] not in ['created', 'paid']:
        return jsonify({'message': 'Cannot cancel this order'}), 400

    mongo.db.order.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': 'cancelled'}})
    return jsonify({'message': 'Order cancelled'})

@app.route('/payment-method', methods=['PUT'])
@token_required
@access_control(['admin'])
def update_payment_method():
    data = request.json
    if not data or not data.get('payment_method'):
        return jsonify({'message': 'payment_method is required'}), 400

    return jsonify({'message': 'Payment method updated by admin'})

@app.route('/payment/execute', methods=['GET'])
def execute_payment():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        mongo.db.order.update_one(
            {'paypal_payment_id': payment_id},
            {'$set': {'status': 'paid'}}
        )
        return jsonify({'message': 'Payment successful'})
    else:
        return jsonify({'message': 'Payment execution failed', 'error': payment.error}), 500

if __name__ == '__main__':
    app.run(debug=True)
