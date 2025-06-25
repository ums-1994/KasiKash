import firebase_admin
from firebase_admin import credentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_firebase():
    try:
        # Initialize Firebase with the service account key
        cred = credentials.Certificate(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH'))
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False

if __name__ == "__main__":
    test_firebase() 