import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email():
    try:
        # Get email configuration from environment variables
        sender_email = os.getenv('MAIL_SENDER_EMAIL')
        sender_name = os.getenv('MAIL_SENDER_NAME')
        smtp_password = os.getenv('SMTP_PASSWORD')

        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = sender_email  # Send to yourself for testing
        msg['Subject'] = "KasiKash Email Test"

        body = "This is a test email from KasiKash App. If you receive this, your email configuration is working correctly!"
        msg.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, smtp_password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, sender_email, text)
        server.quit()

        print("Test email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending test email: {e}")
        return False

if __name__ == "__main__":
    test_email() 