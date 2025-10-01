from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime, timedelta
import uuid
import random
import threading
import time

app = Flask(__name__)
app.secret_key = 'profitx-secret-key-2025'

# Data file paths
USERS_FILE = 'data/users.json'
MARKET_DATA_FILE = 'data/market_data.json'
CHARGES_FILE = 'data/charges.json'
DEPOSITS_FILE = 'data/deposits.json'
WITHDRAWALS_FILE = 'data/withdrawals.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Initialize data files
def init_data_files():
    """Initialize all data files with default data"""
    # Users data
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
    
    # Market data
    if not os.path.exists(MARKET_DATA_FILE):
        default_market_data = {
            "btc": {
                "name": "Bitcoin",
                "price": 41250.75,
                "change": 2.35,
                "mode": "auto",
                "history": [],
                "last_update": datetime.now().isoformat()
            },
            "xau": {
                "name": "Gold",
                "price": 1985.40,
                "change": -0.85,
                "mode": "auto",
                "history": [],
                "last_update": datetime.now().isoformat()
            },
            "nft": {
                "name": "NFT Index",
                "price": 3245.60,
                "change": 5.20,
                "mode": "auto",
                "history": [],
                "last_update": datetime.now().isoformat()
            }
        }
        with open(MARKET_DATA_FILE, 'w') as f:
            json.dump(default_market_data, f, indent=2)
    
    # Charges data
    if not os.path.exists(CHARGES_FILE):
        default_charges = {
            "transaction_fee": 0.5,
            "withdrawal_fee": 1.0,
            "inactivity_fee": 2.0
        }
        with open(CHARGES_FILE, 'w') as f:
            json.dump(default_charges, f, indent=2)
    
    # Deposits data
    if not os.path.exists(DEPOSITS_FILE):
        with open(DEPOSITS_FILE, 'w') as f:
            json.dump([], f)
    
    # Withdrawals data
    if not os.path.exists(WITHDRAWALS_FILE):
        with open(WITHDRAWALS_FILE, 'w') as f:
            json.dump([], f)

# Load data functions
def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except:
        return False

def load_market_data():
    try:
        with open(MARKET_DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_market_data(market_data):
    try:
        with open(MARKET_DATA_FILE, 'w') as f:
            json.dump(market_data, f, indent=2)
        return True
    except:
        return False

def load_deposits():
    try:
        with open(DEPOSITS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_deposits(deposits):
    try:
        with open(DEPOSITS_FILE, 'w') as f:
            json.dump(deposits, f, indent=2)
        return True
    except:
        return False

def load_withdrawals():
    try:
        with open(WITHDRAWALS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_withdrawals(withdrawals):
    try:
        with open(WITHDRAWALS_FILE, 'w') as f:
            json.dump(withdrawals, f, indent=2)
        return True
    except:
        return False

# Market data generator
def generate_market_data():
    """Generate new market data based on current modes"""
    market_data = load_market_data()
    current_time = datetime.now()
    
    for market in ['btc', 'xau', 'nft']:
        if market not in market_data:
            continue
            
        current_price = market_data[market]['price']
        mode = market_data[market]['mode']
        
        # Generate price change based on mode
        if mode == 'up':
            change_percent = random.uniform(0.1, 0.5)
        elif mode == 'down':
            change_percent = random.uniform(-0.5, -0.1)
        else:  # auto
            change_percent = random.uniform(-0.2, 0.2)
        
        new_price = current_price * (1 + change_percent / 100)
        
        # Create candle data
        candle = {
            'timestamp': current_time.timestamp() * 1000,
            'open': current_price,
            'high': max(current_price, new_price) * (1 + random.uniform(0, 0.01)),
            'low': min(current_price, new_price) * (1 - random.uniform(0, 0.01)),
            'close': new_price,
            'time': current_time.isoformat()
        }
        
        # Update market data
        market_data[market]['price'] = new_price
        market_data[market]['change'] = ((new_price - current_price) / current_price) * 100
        market_data[market]['last_update'] = current_time.isoformat()
        
        # Add to history
        market_data[market]['history'].append(candle)
        if len(market_data[market]['history']) > 100:
            market_data[market]['history'] = market_data[market]['history'][-100:]
    
    save_market_data(market_data)

# Background market updater
def market_updater():
    while True:
        try:
            generate_market_data()
            time.sleep(10)  # Update every 10 seconds
        except Exception as e:
            print(f"Market updater error: {e}")
            time.sleep(10)

# Initialize data and start updater
init_data_files()
updater_thread = threading.Thread(target=market_updater, daemon=True)
updater_thread.start()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/trade')
def trade():
    return render_template('trade.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# API Routes
@app.route('/api/market_data')
def api_market_data():
    """Get current market data for all users"""
    try:
        market_data = load_market_data()
        return jsonify(market_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()
        
        if not phone or not password:
            return jsonify({'success': False, 'message': 'Phone and password required'})
        
        users = load_users()
        
        # Check if user exists
        if any(user['phone'] == phone for user in users):
            return jsonify({'success': False, 'message': 'User already exists'})
        
        # Create new user
        new_user = {
            'id': str(uuid.uuid4()),
            'phone': phone,
            'password': password,
            'balance': 0.0,
            'positions': [],
            'trade_history': [],
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat()
        }
        
        users.append(new_user)
        save_users(users)
        
        # Set session
        session['user_id'] = new_user['id']
        session['user_phone'] = new_user['phone']
        
        # Return user without password
        user_response = new_user.copy()
        user_response.pop('password')
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user_response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()
        
        if not phone or not password:
            return jsonify({'success': False, 'message': 'Phone and password required'})
        
        users = load_users()
        user = next((u for u in users if u['phone'] == phone and u['password'] == password), None)
        
        if user:
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            save_users(users)
            
            # Set session
            session['user_id'] = user['id']
            session['user_phone'] = user['phone']
            
            # Return user without password
            user_response = user.copy()
            user_response.pop('password')
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user_response
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/current_user')
def api_current_user():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)
        
        if user:
            # Return user without password
            user_response = user.copy()
            user_response.pop('password')
            return jsonify({'success': True, 'user': user_response})
        else:
            session.clear()
            return jsonify({'success': False, 'message': 'User not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/place_order', methods=['POST'])
def api_place_order():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.json
        market = data.get('market')
        order_type = data.get('type')
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'})
        
        if order_type not in ['buy', 'sell']:
            return jsonify({'success': False, 'message': 'Invalid order type'})
        
        if market not in ['btc', 'xau', 'nft']:
            return jsonify({'success': False, 'message': 'Invalid market'})
        
        # Get current market price
        market_data = load_market_data()
        current_price = market_data[market]['price']
        
        users = load_users()
        user_index = next((i for i, u in enumerate(users) if u['id'] == session['user_id']), None)
        
        if user_index is None:
            return jsonify({'success': False, 'message': 'User not found'})
        
        user = users[user_index]
        
        # Calculate size based on amount
        size = amount / current_price
        
        if order_type == 'buy':
            total_cost = amount
            if user['balance'] < total_cost:
                return jsonify({'success': False, 'message': 'Insufficient balance'})
            
            user['balance'] -= total_cost
            
            # Create position
            position = {
                'id': str(uuid.uuid4()),
                'market': market,
                'type': 'buy',
                'size': size,
                'entry_price': current_price,
                'current_price': current_price,
                'amount': amount,
                'created_at': datetime.now().isoformat()
            }
            
            user['positions'].append(position)
            
        else:  # sell
            # For demo, we'll allow selling without checking if they own the asset
            user['balance'] += amount
            
            # Create position
            position = {
                'id': str(uuid.uuid4()),
                'market': market,
                'type': 'sell',
                'size': size,
                'entry_price': current_price,
                'current_price': current_price,
                'amount': amount,
                'created_at': datetime.now().isoformat()
            }
            
            user['positions'].append(position)
        
        # Add to trade history
        trade_record = {
            'id': str(uuid.uuid4()),
            'market': market,
            'type': order_type,
            'size': size,
            'price': current_price,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        }
        
        user['trade_history'].append(trade_record)
        
        save_users(users)
        
        # Return updated user without password
        user_response = user.copy()
        user_response.pop('password')
        
        return jsonify({
            'success': True,
            'message': f'{order_type.upper()} order executed successfully',
            'user': user_response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/deposit', methods=['POST'])
def api_deposit():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.json
        amount = float(data.get('amount', 0))
        method = data.get('method', 'card')
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'})
        
        # Create deposit record
        deposit = {
            'id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'user_phone': session['user_phone'],
            'amount': amount,
            'method': method,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        deposits = load_deposits()
        deposits.append(deposit)
        save_deposits(deposits)
        
        return jsonify({
            'success': True,
            'message': 'Deposit request submitted for admin approval'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/withdraw', methods=['POST'])
def api_withdraw():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.json
        amount = float(data.get('amount', 0))
        method = data.get('method', 'bank')
        details = data.get('details', {})
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'})
        
        # Check balance
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        if user['balance'] < amount:
            return jsonify({'success': False, 'message': 'Insufficient balance'})
        
        # Create withdrawal record
        withdrawal = {
            'id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'user_phone': session['user_phone'],
            'amount': amount,
            'method': method,
            'details': details,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        withdrawals = load_withdrawals()
        withdrawals.append(withdrawal)
        save_withdrawals(withdrawals)
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal request submitted for admin approval'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Admin API Routes
@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return jsonify({'success': True, 'message': 'Admin login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/logout')
def api_admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({'success': True, 'message': 'Admin logged out'})

@app.route('/api/admin/check_auth')
def api_admin_check_auth():
    if session.get('admin_logged_in'):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@app.route('/api/admin/users')
def api_admin_users():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    users = load_users()
    # Remove passwords from response
    for user in users:
        user.pop('password', None)
    
    return jsonify({'success': True, 'users': users})

@app.route('/api/admin/deposits')
def api_admin_deposits():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    deposits = load_deposits()
    return jsonify({'success': True, 'deposits': deposits})

@app.route('/api/admin/withdrawals')
def api_admin_withdrawals():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    withdrawals = load_withdrawals()
    return jsonify({'success': True, 'withdrawals': withdrawals})

@app.route('/api/admin/approve_deposit', methods=['POST'])
def api_admin_approve_deposit():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        data = request.json
        deposit_id = data.get('deposit_id')
        
        deposits = load_deposits()
        deposit_index = next((i for i, d in enumerate(deposits) if d['id'] == deposit_id), None)
        
        if deposit_index is None:
            return jsonify({'success': False, 'message': 'Deposit not found'})
        
        deposit = deposits[deposit_index]
        
        # Update user balance
        users = load_users()
        user_index = next((i for i, u in enumerate(users) if u['id'] == deposit['user_id']), None)
        
        if user_index is not None:
            users[user_index]['balance'] += deposit['amount']
            save_users(users)
        
        # Update deposit status
        deposits[deposit_index]['status'] = 'approved'
        deposits[deposit_index]['approved_at'] = datetime.now().isoformat()
        save_deposits(deposits)
        
        return jsonify({'success': True, 'message': 'Deposit approved'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/reject_deposit', methods=['POST'])
def api_admin_reject_deposit():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        data = request.json
        deposit_id = data.get('deposit_id')
        
        deposits = load_deposits()
        deposit_index = next((i for i, d in enumerate(deposits) if d['id'] == deposit_id), None)
        
        if deposit_index is None:
            return jsonify({'success': False, 'message': 'Deposit not found'})
        
        # Update deposit status
        deposits[deposit_index]['status'] = 'rejected'
        deposits[deposit_index]['rejected_at'] = datetime.now().isoformat()
        save_deposits(deposits)
        
        return jsonify({'success': True, 'message': 'Deposit rejected'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/approve_withdrawal', methods=['POST'])
def api_admin_approve_withdrawal():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        data = request.json
        withdrawal_id = data.get('withdrawal_id')
        
        withdrawals = load_withdrawals()
        withdrawal_index = next((i for i, w in enumerate(withdrawals) if w['id'] == withdrawal_id), None)
        
        if withdrawal_index is None:
            return jsonify({'success': False, 'message': 'Withdrawal not found'})
        
        withdrawal = withdrawals[withdrawal_index]
        
        # Update user balance
        users = load_users()
        user_index = next((i for i, u in enumerate(users) if u['id'] == withdrawal['user_id']), None)
        
        if user_index is not None:
            users[user_index]['balance'] -= withdrawal['amount']
            save_users(users)
        
        # Update withdrawal status
        withdrawals[withdrawal_index]['status'] = 'approved'
        withdrawals[withdrawal_index]['approved_at'] = datetime.now().isoformat()
        save_withdrawals(withdrawals)
        
        return jsonify({'success': True, 'message': 'Withdrawal approved'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/reject_withdrawal', methods=['POST'])
def api_admin_reject_withdrawal():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        data = request.json
        withdrawal_id = data.get('withdrawal_id')
        
        withdrawals = load_withdrawals()
        withdrawal_index = next((i for i, w in enumerate(withdrawals) if w['id'] == withdrawal_id), None)
        
        if withdrawal_index is None:
            return jsonify({'success': False, 'message': 'Withdrawal not found'})
        
        # Update withdrawal status
        withdrawals[withdrawal_index]['status'] = 'rejected'
        withdrawals[withdrawal_index]['rejected_at'] = datetime.now().isoformat()
        save_withdrawals(withdrawals)
        
        return jsonify({'success': True, 'message': 'Withdrawal rejected'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/market_control', methods=['POST'])
def api_admin_market_control():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        data = request.json
        market = data.get('market')
        mode = data.get('mode')
        
        if market not in ['btc', 'xau', 'nft']:
            return jsonify({'success': False, 'message': 'Invalid market'})
        
        if mode not in ['auto', 'up', 'down']:
            return jsonify({'success': False, 'message': 'Invalid mode'})
        
        market_data = load_market_data()
        market_data[market]['mode'] = mode
        market_data[market]['last_update'] = datetime.now().isoformat()
        
        save_market_data(market_data)
        
        return jsonify({'success': True, 'message': f'Market {market} set to {mode} mode'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/market_modes')
def api_admin_market_modes():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    market_data = load_market_data()
    modes = {market: data['mode'] for market, data in market_data.items()}
    
    return jsonify({'success': True, 'modes': modes})

if __name__ == '__main__':
    print("🚀 ProfitX Trading Platform Started!")
    print("📍 Trading: http://localhost:5000")
    print("📍 Admin: http://localhost:5000/admin")
    print("🔑 Admin Login: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)