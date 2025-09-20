"""
Flask web server for PurdueAI chatbot
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import sys
from main import PurdueAI

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)

# Initialize PurdueAI
try:
    ai = PurdueAI()
    print("✅ PurdueAI initialized successfully")
except Exception as e:
    print(f"❌ Error initializing PurdueAI: {e}")
    ai = None

@app.route('/')
def index():
    """Serve the homepage"""
    return app.send_static_file('homepage.html')

@app.route('/chat')
def chat_interface():
    """Serve the chat interface"""
    return app.send_static_file('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        if not ai:
            return jsonify({
                'error': 'PurdueAI not initialized. Please check your API keys.'
            }), 500
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'error': 'Message cannot be empty'
            }), 400
        
        # Get response from PurdueAI
        response = ai.chat(message)
        
        return jsonify({
            'response': response
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'purdueai_initialized': ai is not None
    })

if __name__ == '__main__':
    # Check if API keys are set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: Please set your OPENAI_API_KEY in the .env file")
        print("Create a .env file with: OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    if not os.getenv('GOOGLE_MAPS_API_KEY'):
        print("❌ Error: Please set your GOOGLE_MAPS_API_KEY in the .env file")
        print("Add to .env file: GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here")
        sys.exit(1)
    
    print("🚀 Starting PurdueAI Web Server...")
    print("📱 Open your browser and go to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
