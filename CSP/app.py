from flask import Flask, request, render_template

app = Flask(__name__)

# Dictionary to store phone numbers by city
phone_book = {
    "nandivada": ["9392118117"],
    "Delhi": ["9812345678", "9123123123"]
}

# Function to get phone numbers by city
def get_phone_numbers_by_city(city):
    return [f'+91{num}' for num in phone_book.get(city, [])]

# Function to add a phone number to a city
def add_phone_number(city, phone_number):
    if city in phone_book:
        phone_book[city].append(phone_number)
    else:
        phone_book[city] = [phone_number]

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        if 'add_phone' in request.form:
            # Handle adding a phone number
            city = request.form['city']
            phone_number = request.form['phone_number']
            add_phone_number(city, phone_number)
            message = f"Phone number {phone_number} added to {city}."
        else:
            # Handle sending SMS
            account_sid = request.form['account_sid']
            auth_token = request.form['auth_token']
            message_body = request.form['message']
            city = request.form['city']

            # Hardcoded Twilio From Number
            from_number = '+12057379758'

            # Retrieve phone numbers for the given city
            phone_numbers = get_phone_numbers_by_city(city)

            # Send the message to all retrieved phone numbers using Twilio API
            if phone_numbers:
                for to_number in phone_numbers:
                    response = send_sms_via_curl(account_sid, auth_token, from_number, message_body, to_number)
                message = f'Message sent to {len(phone_numbers)} numbers in {city}.'
            else:
                message = f'No users found in {city}.'

    return render_template('index.html', message=message)

# Function to send SMS via Twilio API
def send_sms_via_curl(account_sid, auth_token, from_number, message_body, to_number):
    import requests
    twilio_url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
    data = {
        'To': to_number,
        'From': from_number,
        'Body': message_body
    }

    # Make a POST request to Twilio API with URL-encoded data
    response = requests.post(
        twilio_url,
        data=data,
        auth=(account_sid, auth_token)
    )

    if response.status_code == 201:
        print(f"Message sent to {to_number}")
    else:
        print(f"Failed to send message to {to_number}: {response.text}")

    return response

if __name__ == '__main__':
    app.run(debug=True)