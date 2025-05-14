import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from learnyst_automation import LearnystAutomation
from waitress import serve

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('automation_service.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# API key for authentication
API_KEY = os.environ.get("API_KEY", "your-api-key")

# LearnystAutomation instance pool
# We'll keep track of a single instance to reuse
automation_instance = None
last_used_time = None

# Maximum idle time before closing browser (30 minutes)
MAX_IDLE_TIME = 30 * 60  # seconds


async def get_automation_instance(username, password):
    """Get or create a LearnystAutomation instance."""
    global automation_instance, last_used_time
    
    # Check if we have an active instance
    if automation_instance is not None:
        # Check if the browser is still active
        try:
            # Try a simple action to check if browser is still responsive
            if not await automation_instance._check_if_logged_in():
                logger.info("Browser session expired, creating new instance")
                await automation_instance.close()
                automation_instance = None
            else:
                logger.info("Reusing existing browser instance")
        except Exception as e:
            logger.error(f"Error checking browser status: {e}")
            try:
                await automation_instance.close()
            except:
                pass
            automation_instance = None
    
    # Create new instance if needed
    if automation_instance is None:
        try:
            logger.info("Creating new LearnystAutomation instance")
            automation_instance = LearnystAutomation(username, password)
            await automation_instance.initialize()
        except Exception as e:
            logger.error(f"Error creating automation instance: {e}")
            automation_instance = None
            raise
    
    # Update last used time
    last_used_time = datetime.now()
    
    return automation_instance


async def cleanup_check():
    """Check if automation instance should be cleaned up due to inactivity."""
    global automation_instance, last_used_time
    
    if automation_instance is not None and last_used_time is not None:
        idle_time = (datetime.now() - last_used_time).total_seconds()
        
        if idle_time > MAX_IDLE_TIME:
            logger.info(f"Closing browser after {idle_time:.1f} seconds of inactivity")
            try:
                await automation_instance.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            
            automation_instance = None
            last_used_time = None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Learnyst automation service is running',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/learnyst/execute', methods=['POST'])
async def execute_learnyst_action():
    """Execute a Learnyst automation action."""
    # Verify API key
    api_key = request.json.get('api_key')
    if api_key != API_KEY:
        logger.warning("Invalid API key used")
        return jsonify({
            'success': False,
            'message': 'Invalid API key'
        }), 403
    
    # Get action type
    action = request.json.get('action')
    if not action:
        return jsonify({
            'success': False,
            'message': 'Missing action parameter'
        }), 400
    
    # Get Learnyst credentials
    learnyst_username = request.json.get('learnyst_username')
    learnyst_password = request.json.get('learnyst_password')
    
    if not learnyst_username or not learnyst_password:
        return jsonify({
            'success': False,
            'message': 'Missing Learnyst credentials'
        }), 400
    
    # Execute the requested action
    try:
        # Get automation instance
        automation = await get_automation_instance(learnyst_username, learnyst_password)
        
        result_message = ""
        
        # Execute action based on type
        if action == 'give_access':
            email = request.json.get('email')
            course_name = request.json.get('course_name')
            
            if not email or not course_name:
                return jsonify({
                    'success': False,
                    'message': 'Missing required parameters: email and course_name'
                }), 400
            
            logger.info(f"Executing give_access for {email} to {course_name}")
            result_message = await automation.give_access(email, course_name)
        
        elif action == 'enroll_user':
            email = request.json.get('email')
            full_name = request.json.get('full_name')
            course_name = request.json.get('course_name')
            
            if not email or not full_name or not course_name:
                return jsonify({
                    'success': False,
                    'message': 'Missing required parameters: email, full_name, and course_name'
                }), 400
            
            logger.info(f"Executing enroll_user for {full_name} ({email}) to {course_name}")
            result_message = await automation.enroll_user(email, full_name, course_name)
        
        elif action == 'suspend_user':
            user_identifier = request.json.get('user_identifier')
            
            if not user_identifier:
                return jsonify({
                    'success': False,
                    'message': 'Missing required parameter: user_identifier'
                }), 400
            
            logger.info(f"Executing suspend_user for {user_identifier}")
            result_message = await automation.suspend_user(user_identifier)
        
        elif action == 'delete_user':
            user_identifier = request.json.get('user_identifier')
            
            if not user_identifier:
                return jsonify({
                    'success': False,
                    'message': 'Missing required parameter: user_identifier'
                }), 400
            
            logger.info(f"Executing delete_user for {user_identifier}")
            result_message = await automation.delete_user(user_identifier)
        
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown action: {action}'
            }), 400
        
        # Schedule cleanup check for later
        asyncio.create_task(cleanup_check())
        
        return jsonify({
            'success': True,
            'message': result_message
        })
        
    except Exception as e:
        logger.error(f"Error executing action {action}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


# Handle asyncio in Flask
def async_route(route_function):
    """Decorator to convert an async route to a regular route."""
    @app.route(route_function.__name__, methods=['GET', 'POST'])
    def route_wrapper(*args, **kwargs):
        return asyncio.run(route_function(*args, **kwargs))
    return route_wrapper


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5500))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Learnyst automation service on {host}:{port}")
    
    # Use waitress for production-ready WSGI server
    serve(app, host=host, port=port)