import smtplib
import imaplib
import email
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailAutomation:
    def __init__(self, email_address, email_password, 
                 imap_server='imap.gmail.com', 
                 smtp_server='smtp.gmail.com'):
        self.email_address = email_address
        self.email_password = email_password
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self.imap_port = 993
        self.smtp_port = 587

    def send_email(self, recipient_email, subject, body):
        """
        Send an email using SMTP
        """
        try:
            # Set up the SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)

            # Create the email
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send the email
            server.sendmail(self.email_address, recipient_email, msg.as_string())
            server.quit()

            return True, "Email sent successfully"
        except Exception as e:
            print(f"SMTP Email sending error: {e}")
            return False, str(e)

    def fetch_recent_emails(self, search_criteria='UNSEEN', limit=5):
        """
        Fetch recent emails using IMAP
        """
        try:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select('inbox')

            # Search for emails
            _, search_data = mail.search(None, search_criteria)
            email_ids = search_data[0].split()

            emails = []
            # Fetch last 'limit' emails
            for email_id in email_ids[-limit:]:
                _, msg_data = mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                # Extract email details
                subject = email_message['Subject']
                sender = email_message['From']
                body = self._get_email_body(email_message)

                emails.append({
                    'id': email_id,
                    'subject': subject,
                    'sender': sender,
                    'body': body
                })

            mail.close()
            mail.logout()

            return emails
        except Exception as e:
            print(f"IMAP Email fetching error: {e}")
            return []

    def _get_email_body(self, email_message):
        """
        Extract email body from a multipart email
        """
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()
        return body

    def get_recipe_ingredients(self, food_type, api_key, 
                                cuisine=None, 
                                diet=None, 
                                meal_type=None, 
                                include_ingredients=None, 
                                exclude_ingredients=None, 
                                max_ready_time=None):
        """
        Fetch ingredients for a specific food type using Spoonacular API with advanced filtering
        """
        url = 'https://api.spoonacular.com/recipes/complexSearch'
        
        # Prepare query parameters
        params = {
            'query': food_type,
            'apiKey': api_key,
            'number': 1,
            'addRecipeInformation': True,
            'fillIngredients': True
        }

        # Add optional filters
        if cuisine:
            params['cuisine'] = cuisine
        if diet:
            params['diet'] = diet
        if meal_type:
            params['type'] = meal_type
        if include_ingredients:
            params['includeIngredients'] = ','.join(include_ingredients)
        if exclude_ingredients:
            params['excludeIngredients'] = ','.join(exclude_ingredients)
        if max_ready_time:
            params['maxReadyTime'] = max_ready_time

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['results']:
                ingredients = [ingredient['original'] for ingredient in data['results'][0]['extendedIngredients']]
                return ingredients
            else:
                return []
        except Exception as e:
            print(f"API Error: {e}")
            return []