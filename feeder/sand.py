from flask import Flask, jsonify, render_template, request
import sqlite3

app = Flask(__name__)

# Function to get the amount from the SQLite database
def get_amount_from_db():
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Execute query to get the amount
    # cursor.execute("SELECT amount FROM transactions LIMIT 1 ")
    cursor.execute("SELECT amount FROM transactions ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    # Return the amount if exists, else None
    return result[0] if result else None

def add_amount_to_db(amount):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (amount) VALUES (?)", (amount,))
    conn.commit()
    conn.close()

# Define the API endpoint
@app.route('/get_amount', methods=['GET'])
def get_amount():
    # Fetch the amount from the database
    amount = get_amount_from_db()
    
    # Return as JSON response
    if amount is not None:
        return jsonify({"amount": amount}), 200
    else:
        return jsonify({"error": "No data found"}), 404
    
@app.route('/set_amount', methods=['POST'])
def set_amount():
    data = request.get_json()
    
    # Validate that the amount is provided
    if not data or 'amount' not in data:
        return jsonify({"error": "Amount is required"}), 400
    
    amount = data['amount']
    
    # Insert the amount into the database
    add_amount_to_db(amount)
    return jsonify({"message": "Amount added successfully", "amount": amount}), 201

# Define the route for the homepage
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)