from flask import Flask, request,jsonify
import psycopg2
from flask_bcrypt import Bcrypt

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
             CREATE TABLE IF NOT EXISTS client_table(
                 user_id SERIAL PRIMARY KEY,
                 username TEXT NOT NULL,
                 password TEXT NOT NULL,
                 email TEXT NOT  NULL UNIQUE,
                phone_number TEXT NOT NULL,
                college_name TEXT NOT NULL
                );
""")
    connection.commit()
    cur.close()
    connection.close()

create_student_table()

@app.route('/signup', methods = ['POST'])
def signup():

    username =request.json["username"]
    email =request.json["email"]
    password =request.json["password"]
    phone_number =request.json["phone_number"]
    college_name =request.json["college_name"]

    
    hashed_passsword = bcrypt.generate_password_hash(password).decode("utf-8")
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
         INSERT INTO client_table(username,email,password,phone_number,college_name) VALUES(%s,%s,%s,%s,%s)
""",(username,email,hashed_passsword,phone_number,college_name))
    connection.commit()
    cur.close()
    connection.close()
    return jsonify({"message":"signup successfully"})

@app.route('/login' , methods =['POST'])
def login():
    username =request.json['username']
    email = request.json['email']
    password = request.json['password'] 
    
    if not username  or not email:
        return jsonify({"error":"All fields are required"}),400
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
              select user_id, username,password,college_name from client_table
                where email = %s
""",(email,))
    user = cur.fetchone()
    cur.close()
    connection.close()
    if not user:
        return jsonify({"error":"user not found"})
    user_id , username, hashed_password, college_name = user

    if not bcrypt.check_password_hash(hashed_password,password):
        return jsonify({"error":"invalid password"}),401
    return jsonify({
        "message":"login successful",
        "user":{
            "user_id":user_id,
            "username":username,
            "email":email,
            "college_name":college_name
        }
    })


if __name__ == "__main__":
    app.run(debug=True)

