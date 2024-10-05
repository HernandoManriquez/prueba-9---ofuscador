from flask import Flask, render_template, jsonify
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('index.html', current_time=current_time)

@app.route('/get_time')
def get_time():
    return jsonify(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)