from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import datetime
from functools import wraps
from bson.objectid import ObjectId
import paypalrestsdk

app = Flask(__name__)


app.config["MONGO_URI"] = "mongodb://localhost:27017/food_ordering"  
paypalrestsdk.configure({
    "mode": "sandbox",  # or "live" in production
    "client_id": "ASynPwGjKT4hKHPrtXeK9P4QMeCSoU4fX0ZLekoYSGoT0PyVOJ5L-IA-RDC6MRpItwNGUssVnhv2GyTR",
    "client_secret": "EGtkClVtorItbUlHE-mshWdiPZHqnt3PF5sgcYz5cqLzYXqbUm88TpHzJfCh24zx-mLnPNgfgqLE4xCJ"
})

COUNTRY_TAX_CONFIG = {
    'India': {
        'tax_rate': 0.18,    
        'currency': 'INR',
        'symbol': '₹'
    },
    'America': {
        'tax_rate': 0.07,     
        'currency': 'USD',
        'symbol': '$'
    }
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

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password'].strip()
    role = data.get('role', '').lower().strip()
    country = data.get('country', '').capitalize().strip()

    valid_countries = ['America', 'India']

    if role not in ['admin', 'manager', 'member']:
        return jsonify({'message': 'Invalid role'}), 400

    if country not in valid_countries:
        return jsonify({'message': 'Country is required'}), 400

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)

    user_data = {
        'username': username,
        'password': hashed_password,
        'role': role,
        'country': country
    }

    mongo.db.users.insert_one(user_data)

    return jsonify({
        'message': 'User created',
        'username': username,
        'role': role,
        'country': country
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    ip = request.remote_addr
    country = getIP(ip)
    if not country:
        country = data.get('country', 'Unknown')  

    username = data['username']
    password = data['password']

    user = mongo.db.users.find_one({'username': username})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    return jsonify({
        'message': 'Login successful',
        'username': user['username'],
        'role': user['role'],
        'country': user['country']
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
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
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
            return jsonify({'message': 'Token expired! Please login again.'}), 401
        except Exception as e:
            return jsonify({'message': f'Token is invalid! {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated

def access_control(allowed_roles, check_country=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = getattr(request, 'user', None)
            if not user:
                return jsonify({'message': 'User info missing in request!'}), 403

            if user['role'].lower() not in allowed_roles:
                return jsonify({'message': 'Access denied: insufficient role'}), 403

            if check_country:
                requested_country = request.args.get('country') or (request.json and request.json.get('country'))
                if requested_country and requested_country.lower() != user['country'].lower():
                    return jsonify({'message': 'Access denied: cannot access other country data'}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/restaurants', methods=['POST'])
def add_restaurant():
    data = request.json
    name = data.get('name')
    country = data.get('country')
    food = data.get('food', [])

    if not name or not country:
        return jsonify({'message': 'name and country are required'}), 400

    restaurant = {
        'name': name,
        'country': country,
        'food': food  
    }

    result = mongo.db.restaurants.insert_one(restaurant)
    return jsonify({'message': 'Restaurant added', 'id': str(result.inserted_id)}), 201

@app.route('/orders', methods=['POST'])
@token_required
@access_control(allowed_roles=['admin', 'manager', 'member'], check_country=True)
def create_order():
    data = request.json
    if not data or not data.get('restaurant_id') or not data.get('items'):
        return jsonify({'message': 'restaurant_id and items required'}), 400

    try:
        restaurant = mongo.db.restaurants.find_one({'_id': ObjectId(data['restaurant_id'])})
    except:
        return jsonify({'message': 'Invalid restaurant_id'}), 400

    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404

    if restaurant['country'].lower() != request.user['country'].lower():
        return jsonify({'message': 'Cannot order from restaurant outside your country'}), 403

    items = data['items']  # list of food item names
    ordered_items = []
    subtotal = 0.0

    for item_name in items:
        food_item = next((f for f in restaurant['food'] if f['name'] == item_name), None)
        if not food_item:
            return jsonify({'message': f'Item "{item_name}" not found in restaurant'}), 400
        subtotal += float(food_item['price'])
        ordered_items.append(food_item)

    country_info = COUNTRY_TAX_CONFIG.get(restaurant['country'])
    tax_rate = country_info['tax_rate']
    currency = country_info['currency']
    symbol = country_info['symbol']

    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount

    order = {
        'user_id': request.user['id'],
        'restaurant_id': str(restaurant['_id']),
        'items': ordered_items,
        'status': 'created',
        'country': restaurant['country'],
        'created_at': datetime.datetime.utcnow(),
        'pricing': {
            'subtotal': round(subtotal, 2),
            'tax': round(tax_amount, 2),
            'total': round(total, 2),
            'currency': currency,
            'symbol': symbol
        }
    }

    result = mongo.db.orders.insert_one(order)

    return jsonify({
        'message': 'Order created',
        'order_id': str(result.inserted_id),
        'pricing': order['pricing']
    }), 201

@app.route('/orders/<order_id>/checkout', methods=['POST'])
@token_required
@access_control(allowed_roles=['admin', 'manager'], check_country=True)
def place_order(order_id):
    order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    if order['country'].lower() != request.user['country'].lower():
        return jsonify({'message': 'Cannot place order outside your country'}), 403

    if order['status'] != 'created':
        return jsonify({'message': f'Order cannot be placed, current status: {order["status"]}'}), 400

    # Simulate item total
    total_amount = 10.00  # Ideally calculate this from `order['items']`

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": "http://localhost:5000/payment/execute",  # Adjust for your app
            "cancel_url": "http://localhost:5000/payment/cancel"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "Order Payment",
                    "sku": "001",
                    "price": str(total_amount),
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(total_amount),
                "currency": "USD"
            },
            "description": "Payment for food order"
        }]
    })

    if payment.create():
        mongo.db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {'status': 'payment_pending', 'paypal_payment_id': payment.id}}
        )

        # Get PayPal approval URL
        for link in payment.links:
            if link.method == "REDIRECT":
                approval_url = str(link.href)
                return jsonify({
                    'message': 'Redirect to PayPal to complete payment',
                    'redirect_url': approval_url
                }), 202
    else:
        return jsonify({'message': 'Payment creation failed', 'error': payment.error}), 500

@app.route('/orders/<order_id>/cancel', methods=['POST'])
@token_required
@access_control(allowed_roles=['admin', 'manager'], check_country=True)
def cancel_order(order_id):
    order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    if order['country'].lower() != request.user['country'].lower():
        return jsonify({'message': 'Cannot cancel order outside your country'}), 403
    if order['status'] not in ['created', 'paid']:
        return jsonify({'message': 'Order cannot be cancelled'}), 400

    mongo.db.orders.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': 'cancelled'}})
    return jsonify({'message': 'Order cancelled'})

@app.route('/payment-method', methods=['PUT'])
@token_required
@access_control(allowed_roles=['admin'])
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
        mongo.db.orders.update_one(
            {'paypal_payment_id': payment_id},
            {'$set': {'status': 'paid'}}
        )
        return jsonify({'message': 'Payment successful'})
    else:
        return jsonify({'message': 'Payment execution failed', 'error': payment.error}), 500


# Start the app
if __name__ == '__main__':
    app.run(debug=True)
