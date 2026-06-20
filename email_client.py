import os
from imap_tools import MailBox, AND
from dotenv import load_dotenv

load_dotenv()

def get_unread_emails_from_allowed_senders():
    """
    Connects to the IMAP server and fetches unread emails from allowed senders.
    Returns a list of email body texts.
    """
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    imap_server = os.getenv("IMAP_SERVER")
    
    allowed_senders_str = os.getenv("ALLOWED_SENDERS", "")
    allowed_senders = [s.strip() for s in allowed_senders_str.split(",") if s.strip()]

    if not allowed_senders:
        print("Warning: No allowed senders configured.")
        return []

    processed_emails = []

    try:
        # Connect to the mailbox
        with MailBox(imap_server).login(email_user, email_pass) as mailbox:
            # Look for UNSEEN (unread) emails
            for msg in mailbox.fetch(AND(seen=False)):
                sender = msg.from_
                
                # Check if the sender is in our allowed list
                if any(allowed.lower() in sender.lower() for allowed in allowed_senders):
                    print(f"Found new email from allowed sender: {sender}")
                    
                    # Prefer text body over HTML body
                    body = msg.text if msg.text else msg.html
                    
                    if body:
                        processed_emails.append({
                            "subject": msg.subject,
                            "sender": sender,
                            "body": body
                        })
                    
                    # By default, imap-tools marks fetched emails as SEEN.
                    # If you want to keep them unread for testing, you could 
                    # use `mailbox.fetch(AND(seen=False), mark_seen=False)`
                else:
                    # Optional: Mark as unread again if we didn't process it, 
                    # though usually we ignore them or process them separately.
                    pass
                    
    except Exception as e:
        print(f"Error fetching emails: {e}")
        
    return processed_emails

if __name__ == "__main__":
    # For testing the email client independently
    emails = get_unread_emails_from_allowed_senders()
    for e in emails:
        print(f"Subject: {e['subject']}")
        print(f"Body snippet: {e['body'][:100]}...")
