#!/usr/bin/env python3
import os
import json

# Create backend API server (Express.js)
api_server_code = '''const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

const products = [
  { id: 1, name: 'MARKER_PRODUCT_LAPTOP', price: 999.99, stock: 5 },
  { id: 2, name: 'MARKER_PRODUCT_MOUSE', price: 29.99, stock: 15 },
  { id: 3, name: 'MARKER_PRODUCT_KEYBOARD', price: 79.99, stock: 8 }
];

let cart = [];

app.get('/api/products', (req, res) => {
  res.json(products);
});

app.post('/api/cart/add', (req, res) => {
  const { productId, quantity } = req.body;
  const product = products.find(p => p.id === productId);
  if (product && product.stock >= quantity) {
    cart.push({ ...product, quantity });
    product.stock -= quantity;
    res.json({ success: true, message: 'MARKER_CART_ADDED' });
  } else {
    res.status(400).json({ success: false, message: 'Insufficient stock' });
  }
});

app.get('/api/cart', (req, res) => {
  res.json(cart);
});

app.listen(3001, () => console.log('Product API running on port 3001'));
''';

with open('product_api.js', 'w') as f:
    f.write(api_server_code)

# Create payment service (Python Flask)
payment_service_code = '''from flask import Flask, request, jsonify
import json
import time
import random

app = Flask(__name__)

payment_logs = []

@app.route('/api/process-payment', methods=['POST'])
def process_payment():
    data = request.json
    # Simulate processing time
    time.sleep(2)
    
    transaction_id = f"MARKER_TXN_{random.randint(10000, 99999)}"
    
    log_entry = {
        'transaction_id': transaction_id,
        'amount': data.get('amount'),
        'status': 'MARKER_PAYMENT_SUCCESS',
        'card_last_four': data.get('card_number', '')[-4:] if data.get('card_number') else '0000'
    }
    
    payment_logs.append(log_entry)
    print(f"PAYMENT_LOG: {json.dumps(log_entry)}")
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'message': 'MARKER_PAYMENT_PROCESSED'
    })

@app.route('/api/payment-logs', methods=['GET'])
def get_logs():
    return jsonify(payment_logs)

if __name__ == '__main__':
    app.run(port=3002, debug=True)
'''

with open('payment_service.py', 'w') as f:
    f.write(payment_service_code)

# Create React frontend structure
os.makedirs('frontend', exist_ok=True)

package_json = {
    "name": "ecommerce-frontend",
    "version": "1.0.0",
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "axios": "^1.6.0"
    },
    "scripts": {
        "start": "python -m http.server 3000",
        "build": "echo 'Build complete'"
    }
}

with open('frontend/package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

# Create simple HTML frontend with embedded JS
frontend_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MARKER_ECOMMERCE_TITLE</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .product { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
        .cart-item { background: #f5f5f5; padding: 5px; margin: 5px 0; }
        .loading { color: blue; font-weight: bold; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        button { padding: 10px; margin: 5px; cursor: pointer; }
        input { padding: 5px; margin: 5px; }
        #checkout-form { background: #f9f9f9; padding: 20px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>E-Commerce Store</h1>
    
    <div id="products-section">
        <h2>Products</h2>
        <div id="products-list">Loading products...</div>
    </div>
    
    <div id="cart-section">
        <h2>Shopping Cart</h2>
        <div id="cart-items"></div>
        <div id="cart-total"></div>
        <button id="checkout-btn" onclick="showCheckout()" style="display:none;">Proceed to Checkout</button>
    </div>
    
    <div id="checkout-form" style="display:none;">
        <h2>Checkout</h2>
        <div id="checkout-status"></div>
        <input type="text" id="card-number" placeholder="Card Number (1234-5678-9012-3456)" value="1234567890123456">
        <input type="text" id="cardholder-name" placeholder="Cardholder Name" value="MARKER_CARDHOLDER">
        <input type="text" id="cvv" placeholder="CVV" value="123">
        <button id="pay-btn" onclick="processPayment()">Pay Now</button>
    </div>
    
    <div id="order-confirmation" style="display:none;">
        <h2>MARKER_ORDER_CONFIRMED</h2>
        <div id="confirmation-details"></div>
    </div>
    
    <script>
        let products = [];
        let cart = [];
        
        async function loadProducts() {
            try {
                const response = await fetch('http://localhost:3001/api/products');
                products = await response.json();
                displayProducts();
            } catch (error) {
                document.getElementById('products-list').innerHTML = 'Error loading products';
            }
        }
        
        function displayProducts() {
            const container = document.getElementById('products-list');
            container.innerHTML = products.map(product => `
                <div class="product">
                    <h3>${product.name}</h3>
                    <p>Price: $${product.price}</p>
                    <p>Stock: ${product.stock}</p>
                    <button onclick="addToCart(${product.id})" ${product.stock === 0 ? 'disabled' : ''}>
                        Add to Cart
                    </button>
                </div>
            `).join('');
        }
        
        async function addToCart(productId) {
            try {
                const response = await fetch('http://localhost:3001/api/cart/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ productId, quantity: 1 })
                });
                const result = await response.json();
                if (result.success) {
                    await loadCart();
                    await loadProducts(); // Refresh to show updated stock
                }
            } catch (error) {
                console.error('Error adding to cart:', error);
            }
        }
        
        async function loadCart() {
            try {
                const response = await fetch('http://localhost:3001/api/cart');
                cart = await response.json();
                displayCart();
            } catch (error) {
                console.error('Error loading cart:', error);
            }
        }
        
        function displayCart() {
            const container = document.getElementById('cart-items');
            const totalEl = document.getElementById('cart-total');
            const checkoutBtn = document.getElementById('checkout-btn');
            
            if (cart.length === 0) {
                container.innerHTML = 'Cart is empty';
                totalEl.innerHTML = '';
                checkoutBtn.style.display = 'none';
                return;
            }
            
            container.innerHTML = cart.map(item => `
                <div class="cart-item">
                    ${item.name} - $${item.price} x ${item.quantity}
                </div>
            `).join('');
            
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            totalEl.innerHTML = `<strong>Total: $${total.toFixed(2)}</strong>`;
            checkoutBtn.style.display = 'block';
        }
        
        function showCheckout() {
            document.getElementById('checkout-form').style.display = 'block';
        }
        
        async function processPayment() {
            const statusEl = document.getElementById('checkout-status');
            const payBtn = document.getElementById('pay-btn');
            
            statusEl.innerHTML = '<div class="loading">MARKER_PROCESSING_PAYMENT</div>';
            payBtn.disabled = true;
            
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            const cardNumber = document.getElementById('card-number').value;
            const cardholderName = document.getElementById('cardholder-name').value;
            
            try {
                const response = await fetch('http://localhost:3002/api/process-payment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        amount: total,
                        card_number: cardNumber,
                        cardholder_name: cardholderName
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusEl.innerHTML = '<div class="success">Payment successful!</div>';
                    showOrderConfirmation(result.transaction_id, total);
                } else {
                    statusEl.innerHTML = '<div class="error">Payment failed</div>';
                }
            } catch (error) {
                statusEl.innerHTML = '<div class="error">Payment processing error</div>';
            }
            
            payBtn.disabled = false;
        }
        
        function showOrderConfirmation(transactionId, total) {
            document.getElementById('order-confirmation').style.display = 'block';
            document.getElementById('confirmation-details').innerHTML = `
                <p>Transaction ID: ${transactionId}</p>
                <p>Total Paid: $${total.toFixed(2)}</p>
                <p>MARKER_THANK_YOU_MESSAGE</p>
            `;
        }
        
        // Initialize
        loadProducts();
        loadCart();
    </script>
</body>
</html>'''

with open('frontend/index.html', 'w') as f:
    f.write(frontend_html)

print('Generated e-commerce test application files')