import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# Database configuration
print("Database Configuration:")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")

# Firebase configuration
print("\nFirebase Configuration:")
print(f"FIREBASE_SERVICE_ACCOUNT_KEY_PATH: {os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')}")
print(f"FIREBASE_PROJECT_ID: {os.getenv('FIREBASE_PROJECT_ID')}")

# Check if Firebase service account key file exists
firebase_key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 'kasikashapp-4f72a-firebase-adminsdk-fbsvc-90d6afe7c3.json')
if os.path.exists(firebase_key_path):
    print(f"\nFirebase service account key file found at: {firebase_key_path}")
else:
    print(f"\nWARNING: Firebase service account key file not found at: {firebase_key_path}") 