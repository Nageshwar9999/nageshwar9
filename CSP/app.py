import secrets  # For generating a secure random key
from flask import Flask, request, render_template, flash, redirect, url_for
import os
from twilio.rest import Client  # Twilio library import

# Initialize Flask app
app = Flask(__name__)

# Set Flask secret key (For session handling)
app.secret_key = secrets.token_hex(16)  # Generates a 32-character hex key

# Twilio credentials loaded from environment variables
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Dictionary to store phone numbers by city
city_phone_dict = {"nandivada": ["+919392118117"]}

# Function to add a phone number to the dictionary
def add_phone_number(city, phone_number):
    city = city.strip().lower()  # Standardize the city name to lowercase
    if city not in city_phone_dict:
        city_phone_dict[city] = []
    city_phone_dict[city].append(phone_number.strip())

# Function to send SMS via Twilio API using Twilio's Python SDK
def send_sms_via_twilio(account_sid, auth_token, from_number, message_body, to_number):
    try:
        # Create a Twilio client
        client = Client(account_sid, auth_token)

        # Send the SMS
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )

        # Check if the message was sent successfully
        if message.sid:
            print(f"Message sent successfully to {to_number}")
            return True
        else:
            print(f"Failed to send message to {to_number}")
            return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# Route to handle main functionality
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get('add_phone') == '1':  # Add phone number functionality
            city = request.form.get('city', '').strip()
            phone_number = request.form.get('phone_number', '').strip()

            if city and phone_number:
                add_phone_number(city, phone_number)
                flash(f"Phone number {phone_number} added to {city}.", "success")
            else:
                flash("Invalid city or phone number.", "danger")
        else:
            # Handle sending SMS to the selected city
            message_body = request.form.get('message', '').strip()
            city = request.form.get('city', '').strip()

            # Retrieve phone numbers for the selected city from the dictionary
            phone_numbers = city_phone_dict.get(city.strip().lower(), [])

            if phone_numbers and message_body:
                for to_number in phone_numbers:
                    success = send_sms_via_twilio(
                        TWILIO_ACCOUNT_SID,
                        TWILIO_AUTH_TOKEN,
                        TWILIO_PHONE_NUMBER,
                        message_body,
                        to_number
                    )
                    if not success:
                        flash(f"Failed to send message to {to_number}.", "danger")
                flash(f"Message sent to {len(phone_numbers)} numbers in {city}.", "success")
            else:
                flash(f"No users found in {city} or missing message.", "warning")

        return redirect(url_for('index'))

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
