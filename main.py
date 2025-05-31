import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from bot import start_bot, stop_bot
import threading
from config import BOT_STATUS, LOG_MESSAGES
import config
from dotenv import load_dotenv
from browser_agent_runner import run_browser_agent

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')
app.secret_key = os.getenv('SESSION_SECRET', 'dev')
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def index():
    """Render the monitoring dashboard."""
    return render_template('index.html', 
                          status=BOT_STATUS.get('status', 'Inactive'),
                          logs=LOG_MESSAGES)

@app.route('/api/status')
def status():
    """Get the current status of the bot."""
    return jsonify({
        'status': 'healthy',
        'bot_status': BOT_STATUS.get('status', 'Inactive')
    })

@app.route('/api/start_bot', methods=['POST'])
def start_bot_api():
    """Start the Telegram bot."""
    if BOT_STATUS.get('status') == 'Active':
        return jsonify({'status': 'Bot is already running'})
    
    # Start the bot in a separate thread
    threading.Thread(target=start_bot).start()
    return jsonify({'status': 'Bot started'})

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot_api():
    """Stop the Telegram bot."""
    if BOT_STATUS.get('status') != 'Active':
        return jsonify({'status': 'Bot is not running'})
    
    # Use the stop_bot function from bot.py
    result = stop_bot()
    
    if result:
        return jsonify({'status': 'Bot has been stopped'})
    else:
        return jsonify({'status': 'Failed to stop the bot, check logs for details'})

@app.route('/health')
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'ok',
        'bot_status': BOT_STATUS.get('status', 'Inactive'),
        'message': 'Dashboard is running'
    })

@app.route('/dashboard')
def dashboard():
    """Alternative route for dashboard."""
    return render_template('index.html', 
                          status=BOT_STATUS.get('status', 'Inactive'),
                          logs=LOG_MESSAGES)
                          
@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files directly."""
    return app.send_static_file(f'css/{filename}')

@app.route('/api/test_browser_use', methods=['POST'])
def test_browser_use():
    """Test endpoint for browser-use automation."""
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({'error': 'No prompt specified'}), 400
        
    try:
        result = run_browser_agent(prompt)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_flask():
    """Start the Flask server."""
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start the Flask application
    start_flask()
else:
    # Auto-start the bot when running with Gunicorn
    if BOT_STATUS.get('status') != 'Active':
        threading.Thread(target=start_bot).start()
        print("Bot auto-started on application launch")
