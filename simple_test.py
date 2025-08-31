#!/usr/bin/env python3
"""
簡単なFlaskアプリケーションテスト
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'TOU Connect is running!',
        'version': '1.0.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🚀 Starting TOU Connect...")
    app.run(debug=True, host='0.0.0.0', port=5000)
