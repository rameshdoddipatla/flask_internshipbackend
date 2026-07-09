from flask import Flask, request,jsonify,render_template
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
DB_PASSWORD = "1616"

def get_db_connection():
    return psycopg2.connect(
        host = DB_HOST,
        database = DB_NAME,
        user =DB_USER,
        password =DB_PASSWORD
    )

#CREATE STUDENT_TABLE
def create_users_table():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_db(
            user_id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
    """)
    connection.commit()
    cursor.close()
    connection.close()


# CREATE NOTE TABLE
def create_note_table():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS note(
            note_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users_db(user_id),
            title TEXT NOT NULL,
            discription TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    connection.commit()
    cursor.close()
    connection.close()


create_users_table()
create_note_table()




@app.route("/")
def home():
    return render_template("login.html")

@app.route("/signup_page")
def signup_page():
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


SECRET_KEY = " this is mmy kleeeey"

def create_jwt(user_id, username):

    payload ={
        "user_id":user_id,
        "username":username,
        "exp": datetime.datetime.utcnow()+ datetime.timedelta(minutes=10)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


# VERIFY JWT
def verify_jwt(token):

    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data

    except:
        return None

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
         INSERT INTO users_db(username,email,password) VALUES(%s,%s,%s)
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
    email = request.json['email']
    password = request.json['password'] #praveen123
    
    if not email  or not password:
        return jsonify({"error":"All fields are required"}),400
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
              select user_id, username,password from users_db
                where email = %s
""",(email,))
    user = cur.fetchone()
    cur.close()
    connection.close() 
    if not user:
        return jsonify({"error":"user not found"})
    user_id , username, hashed_password = user

    if not bcrypt.check_password_hash(hashed_password,password):# (already hashed password from database,plan text that comes from client)
        return jsonify({"error":"invalid password"}),401
    token =  create_jwt(user_id, username)
    return jsonify({
        "message":"login successful",
        "token": token,
        "user":{
            "user_id":user_id,
            "username":username,
            "email":email
        }
    })




# CREATE NOTE
@app.route("/create_note", methods=['POST'])
def create_note():
    token = request.headers.get("Authorization")
    print(token)
    if not token:
        return jsonify({"error": "Token required"}), 401
    user_data = verify_jwt(token)
    if user_data is None:
        return jsonify({"error": "Invalid or expired token"}), 401
    userid = user_data["user_id"]
    username = user_data["username"]
    title = request.json.get('title')
    description = request.json.get('description')
    if not title or not description:
        return jsonify({"error": "All fields required"}), 400
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        insert into note(user_id,title,discription)
        VALUES(%s,%s,%s);
    """, (userid, title, description))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({
        "message": "Note creation successfull..",
        "user_id": userid,
        "username":username
    }), 201


@app.route("/get_note", methods=['GET'])
def get_note():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token required"}), 401
    user_data = verify_jwt(token)
    if user_data is None:
        return jsonify({"error": "Invalid or expired token"}), 401
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
       select note_id,title,discription ,created_at from note
                where user_id=%s;
""",(user_data["user_id"],))
    notes =cur.fetchall()
    cur.close()
    connection.close()
    return jsonify({
        "user_id":user_data["user_id"],
        "username":user_data["username"],
        "notes":[{
            "note_id":note[0],
            "title":note[1],
            "discription":note[2],
            "created_at":note[3]
        }
         for note in notes
        ]
    })

@app.route("/update_note/<int:note_id>", methods=['PUT'])
def update_note(note_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token required"}), 401
    user_data = verify_jwt(token)
    if user_data is None:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    title = request.json['title']
    discription = request.json['discription']
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
       select * from note
            where note_id=%s and user_id= %s
""", (note_id,user_data["user_id"]))
    note = cur.fetchone()

    if not note :
        return jsonify({"error":"note not found"}),404
    
    cur.execute("""
         update note set title = %s, discription =%s
                where note_id = %s;
""",(title,discription,note_id))
    connection.commit()
    cur.close()
    connection.close()
    return jsonify({
        "message":"note updated sucessfully"
    }),200

@app.route("/delete_note/<int:note_id>", methods=['DELETE'])
def delete_note(note_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token required"}), 401
    user_data = verify_jwt(token)
    if user_data is None:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("""
       select * from note
            where note_id=%s and user_id= %s
""", (note_id,user_data["user_id"]))
    note = cur.fetchone()

    if not note :
        return jsonify({"error":"note not found"}),404
    cur.execute("""
      delete from note 
                where note_id =%s
""",(note_id,))
    connection.commit()
    cur.close()
    connection.close()
    return jsonify({
        "message":"note deleted successfully"
    }),200







if __name__ == "__main__":
    app.run(debug=True)