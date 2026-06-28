import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load env variables if they exist (for standalone execution)
load_dotenv(override=True)

def send_gmail(recipient_email, subject, body_text, attachment_paths=None, sender_email=None, app_password=None):
    """
    Sends an email via Gmail SMTP using SSL.
    
    Args:
        recipient_email (str): Target email address.
        subject (str): Email subject.
        body_text (str): Body content of the email.
        attachment_paths (list): List of absolute file paths to attach.
        sender_email (str): Override for GMAIL_SENDER env var.
        app_password (str): Override for GMAIL_APP_PASS env var.
        
    Returns:
        tuple: (success (bool), status_message (str))
    """
    # Pull and thoroughly sanitize environment values
    gmail_sender = (sender_email or os.getenv("GMAIL_SENDER", "")).strip().replace('"', '').replace("'", "")
    gmail_app_pass = (app_password or os.getenv("GMAIL_APP_PASS", "")).strip().replace('"', '').replace("'", "").replace(" ", "")
    
    if not gmail_sender or not gmail_app_pass:
        err_msg = "Missing email configuration: GMAIL_SENDER or GMAIL_APP_PASS. Please set them in your environment or Settings."
        print(err_msg)
        return False, err_msg
        
    # Ensure addresses and subject lines are completely free of quotes or raw trailing characters
    clean_sender = str(gmail_sender).strip().replace('"', '').replace("'", "")
    clean_receiver = str(recipient_email).strip().replace('"', '').replace("'", "")
    clean_subject = str(subject).strip().replace('\n', '').replace('\r', '').replace('"', '').replace("'", "")
    
    # Build the email headers complying with RFC 5321
    msg = MIMEMultipart()
    msg['From'] = clean_sender
    msg['To'] = clean_receiver
    msg['Subject'] = clean_subject
    
    # Attach your AI-generated message body cleanly
    msg.attach(MIMEText(body_text, 'plain'))
    
    # Handle attachments
    if attachment_paths:
        for path in attachment_paths:
            if not os.path.exists(path):
                print(f"Attachment file not found: {path}")
                continue
                
            filename = os.path.basename(path)
            try:
                with open(path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{filename}"'
                    )
                    msg.attach(part)
            except Exception as e:
                err_msg = f"Failed to attach file {filename}: {str(e)}"
                print(err_msg)
                return False, err_msg
                
    try:
        # Establish a secure connection with Gmail SMTP server using SSL on port 465
        print(f"Connecting to Gmail SMTP server for {clean_receiver}...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(clean_sender, gmail_app_pass)
            # Pass the sanitized strings directly to your active server connection
            server.sendmail(clean_sender, [clean_receiver], msg.as_string())
            
        print("Email sent successfully!")
        return True, "Email sent successfully!"
    except smtplib.SMTPAuthenticationError:
        err_msg = "Gmail Authentication Failed: Please verify GMAIL_SENDER and GMAIL_APP_PASS (ensure it is a 16-character App Password, not a normal password)."
        print(err_msg)
        return False, err_msg
    except Exception as e:
        tb = traceback.format_exc()
        err_msg = f"SMTP Error occurred: {str(e)}\n{tb}"
        print(err_msg)
        return False, f"SMTP Error occurred: {str(e)}"

if __name__ == "__main__":
    # Test stub
    print("Testing mailer configuration load...")
    sender = os.environ.get("GMAIL_SENDER")
    password = os.environ.get("GMAIL_APP_PASS")
    print(f"GMAIL_SENDER configured: {bool(sender)}")
    print(f"GMAIL_APP_PASS configured: {bool(password)}")
