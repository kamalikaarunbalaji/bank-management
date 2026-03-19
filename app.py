from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

app = Flask(__name__)
CORS(app)

# JWT configuration
app.config["JWT_SECRET_KEY"] = "bankprojectsecret"
jwt = JWTManager(app)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Kamali2003arun@",
    database="bankmanagement"
)

# Create Account
@app.route("/createaccount", methods=["POST"])
@jwt_required()
def create_account():
    data = request.get_json()

    acc_no = data.get("acc_no")
    name = data.get("name")

    cursor = db.cursor()

    sql = "INSERT INTO accounts (acc_no, name, balance) VALUES (%s, %s, 0)"
    cursor.execute(sql, (acc_no, name))

    db.commit()
    cursor.close()

    return jsonify({"message": "Account Created Successfully"})


# Deposit
@app.route("/deposit", methods=["POST"])
@jwt_required()
def deposit():
    data = request.get_json()

    acc_no = data.get("acc_no")
    amount = data.get("amount")

    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO transactions (acc_no, trans_type, amount) VALUES (%s,'DEPOSIT',%s)",
        (acc_no, amount)
    )

    cursor.execute(
        "UPDATE accounts SET balance = balance + %s WHERE acc_no = %s",
        (amount, acc_no)
    )

    db.commit()
    cursor.close()

    return jsonify({"message": "Deposit Successful"})


# Withdraw
@app.route("/withdraw", methods=["POST"])
@jwt_required()
def withdraw():
    data = request.get_json()

    acc_no = data.get("acc_no")
    amount = data.get("amount")

    cursor = db.cursor()

    cursor.execute("SELECT balance FROM accounts WHERE acc_no = %s", (acc_no,))
    balance = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO transactions (acc_no, trans_type, amount) VALUES (%s,'WITHDRAW',%s)",
        (acc_no, amount)
    )

    cursor.execute(
        "UPDATE accounts SET balance = balance - %s WHERE acc_no = %s",
        (amount, acc_no)
    )

    db.commit()
    cursor.close()

    return jsonify({"message": "Withdraw Successful"})


# Transfer
@app.route("/transfer", methods=["POST"])
@jwt_required()
def transfer():
    data = request.get_json()

    from_acc = data.get("from_acc")
    to_acc = data.get("to_acc")
    amount = data.get("amount")

    cursor = db.cursor()

    cursor.execute("SELECT balance FROM accounts WHERE acc_no = %s", (from_acc,))
    balance = cursor.fetchone()[0]

    # Sender
    cursor.execute(
        "INSERT INTO transactions (acc_no, trans_type, amount) VALUES (%s,'TRANSFER_OUT',%s)",
        (from_acc, amount)
    )

    cursor.execute(
        "UPDATE accounts SET balance = balance - %s WHERE acc_no = %s",
        (amount, from_acc)
    )

    # Receiver
    cursor.execute(
        "INSERT INTO transactions (acc_no, trans_type, amount) VALUES (%s,'TRANSFER_IN',%s)",
        (to_acc, amount)
    )

    cursor.execute(
        "UPDATE accounts SET balance = balance + %s WHERE acc_no = %s",
        (amount, to_acc)
    )

    db.commit()
    cursor.close()

    return jsonify({"message": "Transfer Successful"})


# Balance Check
@app.route("/balance/<int:acc_no>", methods=["GET"])
@jwt_required()
def check_balance(acc_no):
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT balance FROM accounts WHERE acc_no = %s",
        (acc_no,)
    )

    balance = cursor.fetchone()
    cursor.close()

    return jsonify(balance)


# Recent Transactions
@app.route("/recenttransactions/<int:acc_no>", methods=["GET"])
@jwt_required()
def getrecent_transactions(acc_no):
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT trans_id, trans_type, amount, date FROM transactions WHERE acc_no = %s ORDER BY trans_id DESC",
        (acc_no,)
    )

    transactions = cursor.fetchall()
    cursor.close()

    return jsonify(transactions)


# Register
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    if user:
        cursor.close()
        return jsonify({"message": "Username already exists"})

    hashed_password = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s,%s)",
        (username, hashed_password)
    )

    db.commit()
    cursor.close()

    return jsonify({"message": "User Registered Successfully"})


# Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()
    cursor.close()

    if not user:
        return jsonify({"message": "User not found"})

    if check_password_hash(user["password"], password):

        token = create_access_token(identity=username)

        return jsonify({
            "message": "Login Successful",
            "token": token
        })

    else:
        return jsonify({"message": "Invalid Password"})


if __name__ == "__main__":
    app.run(debug=True)