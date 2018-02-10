from decimal import Decimal
import os

API_SECRET = os.environ.get('GDAX_API_SECRET', None)
API_KEY = os.environ.get('GDAX_API_API_KEY', None)
API_PASSPHRASE = os.environ.get('GDAX_API_PASSPHRASE', None)

RISK_PER_TRADE = '0.1'
PRODUCTS = ['BTC-USD','ETH-USD','ETH-BTC']

