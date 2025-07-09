from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return "Hello, world!"

if __name__ == '__main__':
    print("About to start minimal app...")
    socketio.run(app, host='0.0.0.0', port=5001) 