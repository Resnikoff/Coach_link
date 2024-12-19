from mailjet_rest import Client
import os
import hashlib
import time

api_key = '0d29c7f6bccd49aecc497d539c44a6e1'
api_secret = '97c875cb1213c0be3a7ee7e3e8bd335a'

def send_email(subject, recipient, body):
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    data = {
        'Messages': [
            {
                "From": {
                    "Email": "coachlink.donotreply@gmail.com",
                    "Name": "Coach Link"
                },
                "To": [
                    {
                        "Email": recipient
                    }
                ],
                "Subject": subject,
                "HTMLPart": body
            }
        ]
    }
    result = mailjet.send.create(data=data)
    return result.status_code




def send_reset_email(email):
    # Construct the password reset link.
    reset_link = f"http://127.0.0.1:5000/reset_password?email={email}"
    print(f"Reset Link: {reset_link}")  # Print the constructed link to verify it's correct

    # Use Mailjet to send the email
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "coachlink.donotreply@gmail.com",
                    "Name": "Coach Link"
                },
                "To": [
                    {
                        "Email": email
                    }
                ],
                "Subject": "Password Reset Request",
                "TextPart": "If you requested a password reset, click on the link below:",
                "HTMLPart": f"<p>If you requested a password reset, <a href='{reset_link}'>click here</a> to reset your password.</p>"
            }
        ]
    }
    print("Attempting to send email...")  # Printing before sending the email
    result = mailjet.send.create(data=data)

    # Print the Mailjet result for debugging
    print("Mailjet Response:", result.json())

    # Add error handling based on the result, if needed
    if result.status_code != 200:
        print("Error sending email:", result.json())
        return False
    print("Email sent successfully!")  # Printing if the email was sent successfully
    return True
