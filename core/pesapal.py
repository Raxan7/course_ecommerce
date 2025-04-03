import requests
import json
from django.conf import settings
from datetime import datetime

class PesaPal:
    def __init__(self):
        self.consumer_key = settings.PESAPAL_CONSUMER_KEY
        self.consumer_secret = settings.PESAPAL_CONSUMER_SECRET
        self.api_endpoint = settings.PESAPAL_API_ENDPOINT
    
    def _get_auth_token(self):
        """Get authentication token from PesaPal"""
        url = f"{self.api_endpoint}/api/Auth/RequestToken"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data = {
            'consumer_key': self.consumer_key,
            'consumer_secret': self.consumer_secret
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json().get('token')
        except requests.RequestException as e:
            print(f"Error getting PesaPal token: {str(e)}")
            return None
    
    def register_ipn_url(self):
        """Register IPN URL with PesaPal"""
        token = self._get_auth_token()
        if not token:
            return None
            
        url = f"{self.api_endpoint}/api/URLSetup/RegisterIPN"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data = {
            'url': settings.PESAPAL_IPN_URL,
            'ipn_notification_type': 'POST'
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json().get('ipn_id')
        except requests.RequestException as e:
            print(f"Error registering IPN URL: {str(e)}")
            return None
    
    def submit_order_request(self, order_details):
        """
        Submit order to PesaPal following API 3.0 JSON specifications
        """
        token = self._get_auth_token()
        if not token:
            return None
            
        url = f"{self.api_endpoint}/api/Transactions/SubmitOrderRequest"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Convert amount to float as required by PesaPal
        order_details['amount'] = float(order_details['amount'])
        
        try:
            response = requests.post(url, json=order_details, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error submitting order to PesaPal: {str(e)}")
            print(f"Request data: {json.dumps(order_details, indent=2)}")
            return None
    
    def get_transaction_status(self, order_tracking_id):
        """Check transaction status"""
        token = self._get_auth_token()
        if not token:
            return None
            
        url = f"{self.api_endpoint}/api/Transactions/GetTransactionStatus?orderTrackingId={order_tracking_id}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting transaction status: {str(e)}")
            return None