import os
from flask import Flask
from rewards import rewards_bp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# Register the rewards blueprint with a url_prefix
app.register_blueprint(rewards_bp, url_prefix='/rewards')

@app.route('/')
def home():
    return "Welcome to KasiKash Stokvel!"

if __name__ == '__main__':
    app.run(debug=True) 