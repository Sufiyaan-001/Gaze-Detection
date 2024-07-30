# app.py

from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/runcode', methods=['POST'])
def run_code():
    subprocess.Popen(['python', 'main.py'])  # Change 'your_script.py' to the filename of your Python script
    return 'Code execution started.'

if __name__ == '__main__':
    app.run(debug=True)
