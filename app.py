from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)


#database connection details
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "Ramesh@123"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def create_student_table():
    connection = get_db_connection()
    cur = connection.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_table (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            grade TEXT NOT NULL
        )
    """)

    connection.commit()
    cur.close()
    connection.close()

    print("student_table created successfully!")

# Call function here
create_student_table()

@app.route("/send_data", methods=["POST"])
def send_data():
    name = request.json['name']
    age = request.json['age']
    grade = request.json['grade']
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("INSERT INTO student_table (name, age, grade) VALUES (%s, %s, %s)", (name, age, grade))
    connection.commit()
    cur.close()
    connection.close()  
    return jsonify({"message": "Data inserted successfully!"}), 201


@app.route("/get_data", methods=["GET"])
def get_data():
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("SELECT * FROM student_table")
    data = cur.fetchone()
    cur.close()
    connection.close()
    return jsonify({
        "id": data[0],
        "name": data[1],
        "age": data[2],
        "grade": data[3]
    }) ,200


@app.route("/put_data", methods=["PUT"])
def put_data():
    id = request.json['id']
    name = request.json['name']
    age = request.json['age']
    grade = request.json['grade']
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("UPDATE student_table SET name=%s, age=%s, grade=%s WHERE id=%s", (name, age, grade, id))
    connection.commit()
    cur.close()
    connection.close()  
    return jsonify({"message": "Data updated successfully!"}), 200    

@app.route('/')
def home():
    return "flasking is ruuing"
   

if __name__ == "__main__":
    app.run(debug=True)