import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_email_config():
    print("Checking email configuration...")
    
    # Get email configuration
    sender_email = os.getenv('MAIL_SENDER_EMAIL')
    sender_name = os.getenv('MAIL_SENDER_NAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    # Print configuration (masking the password)
    print(f"Sender Email: {sender_email}")
    print(f"Sender Name: {sender_name}")
    print(f"SMTP Password: {'*' * len(smtp_password) if smtp_password else 'Not set'}")
    
    # Check if all required variables are set
    if not all([sender_email, sender_name, smtp_password]):
        print("\nError: Some email configuration variables are missing!")
        if not sender_email:
            print("- MAIL_SENDER_EMAIL is not set")
        if not sender_name:
            print("- MAIL_SENDER_NAME is not set")
        if not smtp_password:
            print("- SMTP_PASSWORD is not set")
    else:
        print("\nAll email configuration variables are set!")

if __name__ == "__main__":
    check_email_config() 