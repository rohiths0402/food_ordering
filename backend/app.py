from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)


app.config["MONGO_URI"] = "mongodb://localhost:27017/yourdb"  
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

# Start the app
if __name__ == '__main__':
    app.run(debug=True)
