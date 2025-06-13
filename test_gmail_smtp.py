import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gmail_smtp():
    """Test Gmail SMTP configuration"""
    
    # Get environment variables
    sender_email = os.getenv("MAIL_SENDER_EMAIL")
    sender_name = os.getenv("MAIL_SENDER_NAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    print(f"Sender Email: {sender_email}")
    print(f"Sender Name: {sender_name}")
    print(f"SMTP Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    
    if not all([sender_email, sender_name, smtp_password]):
        print("ERROR: Missing required environment variables!")
        return False
    
    # Test email configuration
    subject = "Test Email from KasiKash App"
    html_content = """
    <html>
    <body>
        <h2>Test Email</h2>
        <p>This is a test email to verify Gmail SMTP configuration.</p>
        <p>If you receive this email, your Gmail SMTP setup is working correctly!</p>
        <p>Thanks,<br>The KasiKash App Team</p>
    </body>
    </html>
    """
    
    message = MIMEMultipart()
    message['From'] = f"{sender_name} <{sender_email}>"
    message['To'] = sender_email  # Send to yourself for testing
    message['Subject'] = subject
    message.attach(MIMEText(html_content, 'html'))
    
    try:
        print("Attempting to connect to Gmail SMTP...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("Connected to Gmail SMTP server")
            print("Attempting to login...")
            server.login(sender_email, smtp_password)
            print("Login successful!")
            
            print("Sending test email...")
            server.sendmail(sender_email, sender_email, message.as_string())
            print("✅ Test email sent successfully!")
            print(f"Check your inbox at {sender_email}")
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("Please check your app password and make sure 2FA is enabled.")
        return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

if __name__ == "__main__":
    print("Testing Gmail SMTP Configuration...")
    print("=" * 50)
    test_gmail_smtp() 