from flask import Flask, request, render_template
from twilio.rest import Client
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Your Twilio credentials
account_sid = 'ACb3c8c957e0c4ecd6c8c2224cd5a6d472'
auth_token = '0dd22d2284e5dbbda09f3b28635d57de'
client = Client(account_sid, auth_token)

# MySQL connection setup
def get_mysql_connection():
    return mysql.connector.connect(
        host='localhost',        # Change if your MySQL server is not on localhost
        user='root',             # MySQL username (default in XAMPP is 'root')
        password='',             # MySQL password (default in XAMPP is empty for root)
        database='22544'         # Your MySQL database name
    )

# Function to get phone numbers by city
def get_phone_numbers_by_city(city):
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT phno FROM csp WHERE address = %s", (city,))
        phone_numbers = cursor.fetchall()
        return [number[0] for number in phone_numbers]
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message_body = request.form['message']
        city = request.form['city']

        # Retrieve phone numbers for the given city
        phone_numbers = get_phone_numbers_by_city(city)

        # Send the message to all retrieved phone numbers
        if phone_numbers:
            for to_number in phone_numbers:
                message = client.messages.create(
                    body=message_body,
                    from_='+12057379758',  # Your Twilio number
                    to=to_number
                )
            return f'Message sent to {len(phone_numbers)} numbers in {city}.'
        else:
            return f'No users found in {city}.'

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
