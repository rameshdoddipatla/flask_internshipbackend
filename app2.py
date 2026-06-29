from flask import Flask, request,jsonify
import psycopg2
from flask_bcrypt import Bcrypt
import jwt
import datetime

app =Flask(__name__)

bcrypt = Bcrypt(app)

#database config
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Ramesh@123"

def get_db_connection():
    return psycopg2.connect(
        host = DB_HOST,
        database = DB_NAME,
        user =DB_USER,
        password =DB_PASSWORD
    )

#CREATE STUDENT_TABLE
def create_student_table():
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
             CREATE TABLE IF NOT EXISTS users_table(
                 user_id SERIAL PRIMARY KEY,
                 username TEXT NOT NULL,
                 password TEXT NOT NULL,
                 email TEXT NOT  NULL UNIQUE
                );
""")
    connection.commit()
    cur.close()
    connection.close()

create_student_table()

SECRET_KEY ="this is my key"

def create_jwt(user_id, username):

    payload ={
        "user_id":user_id,
        "username":username,
        "exp":datetime.datetime.utcnow()+ datetime.timedelta(minutes=10)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


@app.route('/signup', methods = ['POST'])
def signup():

    username =request.json["username"]
    email =request.json["email"]
    password =request.json["password"]

    if not username or not email or not password:
        return jsonify({"error":"All fields required"}),400


    
    hashed_passsword = bcrypt.generate_password_hash(password).decode("utf-8")
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
         INSERT INTO users_table(username,email,password) VALUES(%s,%s,%s)
                returning user_id
""",(username,email,hashed_passsword))
    user_id = cur.fetchone()[0]
    connection.commit()
    cur.close()
    connection.close()

    token = create_jwt(user_id,username)
    return jsonify({"message":"signup successful",
                    "token": token})

@app.route('/login' , methods =['POST'])
def login():
    username = request.json["username"]
    email = request.json['email']
    password = request.json['password'] 
    
    if not username or not email  or not password:
        return jsonify({"error":"All fields are required"}),400
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
              select user_id, username,password from users_table
                where email = %s
""",(email,))
    user = cur.fetchone()
    user_id = user[0]
    connection.commit()
    cur.close()
    connection.close()
    if not user:
        return jsonify({"error":"user not found"})
    user_id , username, hashed_password = user

    if not bcrypt.check_password_hash(hashed_password,password):
        return jsonify({"error":"invalid password"}),401
    
    token = create_jwt(user_id, username)
    return jsonify({
        "message":"login successful",
        "user":{
            "user_id":user_id,
            "username":username,
            "email":email,
            "token":token
        }
    }),200


if __name__ == "__main__":
    app.run(debug=True)