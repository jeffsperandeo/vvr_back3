from flask import Flask, jsonify, render_template_string
import requests
import os
import base64
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Environment variables
TEKMETRICS_API_URL = os.getenv('TEKMETRICS_API_BASE_URL', 'https://shop.tekmetric.com/api/v1')
SHOP_ID = os.getenv('SHOP_ID')
CLIENT_ID = os.getenv('TEKMETRICS_CLIENT_ID')
CLIENT_SECRET = os.getenv('TEKMETRICS_CLIENT_SECRET')
TOKEN_URL = f'{TEKMETRICS_API_URL}/oauth/token'

# Log loaded environment variables
logging.debug(f'TEKMETRICS_API_URL: {TEKMETRICS_API_URL}')
logging.debug(f'SHOP_ID: {SHOP_ID}')
logging.debug(f'CLIENT_ID: {CLIENT_ID}')
logging.debug(f'CLIENT_SECRET: {CLIENT_SECRET}')

if not SHOP_ID:
    logging.error('SHOP_ID environment variable is not set. Please set it in your .env file.')
    raise ValueError("SHOP_ID environment variable is not set. Please set it in your .env file.")

def get_access_token():
    auth_header = f'{CLIENT_ID}:{CLIENT_SECRET}'.encode('ascii')
    base64_bytes = base64.b64encode(auth_header)
    base64_auth = base64_bytes.decode('ascii')

    headers = {
        'Authorization': f'Basic {base64_auth}',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }
    data = {
        'grant_type': 'client_credentials'
    }

    logging.debug(f'Authorization Header: Basic {base64_auth}')
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    logging.debug(f'Token response: {response.text}')

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        logging.error('Failed to obtain access token')
        return None

def fetch_data(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f'Failed to fetch data from {url}: {response.text}')
        return None

@app.route('/')
def home():
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'Failed to obtain access token'}), 500

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    customer_id = 5424529  # Jeff Sperandeo's ID

    # Fetch customer data
    customer_url = f'{TEKMETRICS_API_URL}/customers/{customer_id}?shop={SHOP_ID}'
    logging.debug(f'Fetching customer data from {customer_url}')
    customer_data = fetch_data(customer_url, headers)

    # Fetch repair orders for the customer
    repair_orders_url = f'{TEKMETRICS_API_URL}/repair-orders?shop={SHOP_ID}&customerId={customer_id}'
    logging.debug(f'Fetching repair orders from {repair_orders_url}')
    repair_orders = fetch_data(repair_orders_url, headers)

    dashboard_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Home Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f8f9fa; color: #343a40; margin: 0; padding: 0; }
            header { background-color: #007bff; color: white; padding: 1em; text-align: center; }
            h1, h2, p { margin: 0.5em 0; }
            .container { max-width: 800px; margin: 2em auto; padding: 1em; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            .section { margin-bottom: 1.5em; }
            ul { list-style-type: none; padding: 0; }
            li { background: #f1f3f5; margin-bottom: 0.5em; padding: 0.5em; border-radius: 0.25em; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 0.75em; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #007bff; color: white; }
        </style>
    </head>
    <body>
        <header>
            <h1>Home Dashboard</h1>
        </header>
        <div class="container">
            <div class="section">
                <h2>Customer Details</h2>
                <ul>
                    <li>Name: {{ customer.firstName }} {{ customer.lastName }}</li>
                    <li>ID: {{ customer.id }}</li>
                    <li>Email: {{ customer.email }}</li>
                    <li>Phone: {{ customer.phone | map(attribute='number') | join(', ') }}</li>
                    <li>Address: {{ customer.address.fullAddress }}</li>
                    <li>Notes: {{ customer.notes }}</li>
                </ul>
            </div>
            <div class="section">
                <h2>Repair Orders</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Order #</th>
                            <th>Status</th>
                            <th>Labor Sales</th>
                            <th>Parts Sales</th>
                            <th>Fees</th>
                            <th>Total Sales</th>
                            <th>Jobs</th>
                            <th>Customer Concerns</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for order in repair_orders %}
                        <tr>
                            <td>{{ order.repairOrderNumber }}</td>
                            <td>{{ order.repairOrderStatus.name }}</td>
                            <td>{{ order.laborSales }}</td>
                            <td>{{ order.partsSales }}</td>
                            <td>{{ order.fees | map(attribute='total') | join(', ') }}</td>
                            <td>{{ order.totalSales }}</td>
                            <td>{{ order.jobs | map(attribute='name') | join(', ') }}</td>
                            <td>{{ order.customerConcerns | map(attribute='concern') | join(', ') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <div class="section">
                <h2>Notifications</h2>
                <!-- Implement notifications logic here -->
                <p>No notifications at this time.</p>
            </div>
        </div>
    </body>
    </html>
    '''

    return render_template_string(
        dashboard_template,
        customer=customer_data if customer_data else {},
        repair_orders=repair_orders['content'] if repair_orders else []
    )

@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'Failed to obtain access token'}), 500

    customer_url = f'{TEKMETRICS_API_URL}/customers/{customer_id}?shop={SHOP_ID}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    customer_response = requests.get(customer_url, headers=headers)

    if customer_response.status_code != 200:
        return jsonify({'error': 'Customer not found'}), customer_response.status_code

    customer_data = customer_response.json()

    repair_orders_url = f'{TEKMETRICS_API_URL}/repair-orders?shop={SHOP_ID}&customerId={customer_id}'
    repair_orders_response = requests.get(repair_orders_url, headers=headers)
    
    logging.debug(f'Repair Orders Response Status: {repair_orders_response.status_code}')
    logging.debug(f'Repair Orders Response Text: {repair_orders_response.text}')

    if repair_orders_response.status_code != 200:
        return jsonify({'error': 'Error fetching repair orders', 'details': repair_orders_response.text}), repair_orders_response.status_code

    repair_orders_data = repair_orders_response.json()

    customer_repair_orders = [
        order for order in repair_orders_data.get('content', []) if order['customerId'] == customer_id
    ]

    return jsonify({
        'customer': customer_data,
        'repair_orders': customer_repair_orders
    })

if __name__ == '__main__':
    app.run(port=int(os.getenv("PORT", 3001)), debug=True)
