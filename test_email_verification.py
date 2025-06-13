import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the send_email_verification function from main.py
sys.path.append('.')
from main import send_email_verification

def test_email_verification():
    """Test the email verification function"""
    
    print("Testing Email Verification Function...")
    print("=" * 50)
    
    # Test email configuration
    sender_email = os.getenv("MAIL_SENDER_EMAIL")
    sender_name = os.getenv("MAIL_SENDER_NAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    print(f"Sender Email: {sender_email}")
    print(f"Sender Name: {sender_name}")
    print(f"SMTP Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    
    if not all([sender_email, sender_name, smtp_password]):
        print("❌ ERROR: Missing required environment variables!")
        return False
    
    # Test with a dummy verification link
    test_email = sender_email  # Send to yourself for testing
    test_verification_link = "https://example.com/verify?token=test123"
    
    print(f"\nSending test verification email to: {test_email}")
    print(f"Verification link: {test_verification_link}")
    
    # Call the actual function from main.py
    result = send_email_verification(test_email, test_verification_link)
    
    if result:
        print("✅ Email verification function working correctly!")
        print(f"Check your inbox at {test_email} for the verification email")
        return True
    else:
        print("❌ Email verification function failed!")
        return False

if __name__ == "__main__":
    test_email_verification() 