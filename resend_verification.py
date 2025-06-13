import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK only if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "kasikashapp-4f72a-firebase-adminsdk-fbsvc-b3a75155f2.json"))
    firebase_admin.initialize_app(cred)

def send_email_verification(to_email, verification_link):
    sender_email = os.getenv("MAIL_SENDER_EMAIL")
    sender_name = os.getenv("MAIL_SENDER_NAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not sender_email:
        print("Error: MAIL_SENDER_EMAIL not found in environment variables.")
        return False
    if not smtp_password:
        print("Error: SMTP_PASSWORD not found in environment variables.")
        return False

    subject = "Verify your email for KasiKash App"
    html_content = f"""
    <html>
    <body>
        <p>Hello,</p>
        <p>Thank you for registering with KasiKash App!</p>
        <p>Please click on the link below to verify your email address:</p>
        <p><a href=\"{verification_link}\">{verification_link}</a></p>
        <p>If you did not register for an account, please ignore this email.</p>
        <p>Thanks,</p>
        <p>The KasiKash App Team</p>
    </body>
    </html>
    """

    message = MIMEMultipart()
    message['From'] = f"{sender_name} <{sender_email}>"
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, smtp_password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"Verification email sent successfully to {to_email} via Gmail SMTP!")
        return True
    except Exception as e:
        print(f"Error sending verification email to {to_email} via Gmail SMTP: {e}")
        return False

def resend_verification_email(email):
    """Resend verification email for a user"""
    
    print(f"Attempting to resend verification email to: {email}")
    
    try:
        # Get user from Firebase
        user = auth.get_user_by_email(email)
        print(f"Found user: {user.uid}")
        print(f"Email verified: {user.email_verified}")
        
        if user.email_verified:
            print("✅ User email is already verified!")
            return True
        
        # Generate new verification link
        verification_link = auth.generate_email_verification_link(email)
        print(f"Generated verification link: {verification_link}")
        
        # Send verification email
        if send_email_verification(email, verification_link):
            print("✅ Verification email sent successfully!")
            print(f"Please check your inbox at {email}")
            return True
        else:
            print("❌ Failed to send verification email")
            return False
            
    except auth.UserNotFoundError:
        print(f"❌ User with email {email} not found in Firebase")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    email = "umsibanda.1994@gmail.com"  # Your email address
    print("Resending Verification Email...")
    print("=" * 50)
    resend_verification_email(email) 