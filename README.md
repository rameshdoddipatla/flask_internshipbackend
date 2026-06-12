# open powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

python -m venv venv

venv\scripts\activate #windows

#linux/macOS
source venv/bin/activate

pip install flask
pip install psycopg2

#to run

python app.py