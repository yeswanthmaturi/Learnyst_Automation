import os
import re
import logging
import threading
import time
import json
import requests
from config import BOT_STATUS, add_log_message

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the Telegram bot token from environment variable
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")

# Map course shortcuts to full names
COURSE_MAP = {
    'fs1': 'Full Stack 1',
    'fs2': 'Full Stack 2',
    'fs3': 'Full Stack 3',
    'fs4': 'Full Stack 4',
    'fs5': 'Full Stack 5',
    'meta': 'Meta Interview Advance Concepts'
}

# Learnyst credentials
LEARNYST_USERNAME = os.environ.get("LEARNYST_USERNAME", "techpath.mocks@gmail.com")
LEARNYST_PASSWORD = os.environ.get("LEARNYST_PASSWORD", "Techpathai")

# External service URL
# During development, if external service unavailable, we'll simulate responses
EXTERNAL_SERVICE_URL = os.environ.get("EXTERNAL_SERVICE_URL", "http://10.0.0.77:5500")
EXTERNAL_SERVICE_API_KEY = os.environ.get("EXTERNAL_SERVICE_API_KEY", "learnyst-access-key-2025")
# Set to True during development if external service is not yet available
DEVELOPMENT_MODE = os.environ.get("DEVELOPMENT_MODE", "True").lower() == "true"

# Bot polling variables
is_polling = False
polling_thread = None

def send_telegram_message(chat_id, text):
    """Send a message via Telegram API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        add_log_message(f"Error sending Telegram message: {e}")
        return None

def process_message(message):
    """Process a message from Telegram."""
    chat_id = message.get('chat', {}).get('id')
    message_text = message.get('text', '')

    # Check if message mentions @LearnystBot
    if '@LearnystBot' not in message_text:
        return

    # Log the received command
    logger.info(f"Received command: {message_text}")
    add_log_message(f"Received command: {message_text}")

    # Send initial response
    send_telegram_message(
        chat_id, 
        "Processing your request... connecting to service..."
    )
    add_log_message("Connecting to external automation service")

    # Process the command
    try:
        # Case 1: Give access to existing user
        access_pattern = r'@LearnystBot\s+(\S+@\S+)\s+access\s+(\w+)'
        access_match = re.search(access_pattern, message_text)
        
        if access_match:
            email = access_match.group(1)
            course_code = access_match.group(2).lower()
            
            if course_code not in COURSE_MAP:
                send_telegram_message(
                    chat_id,
                    f"Invalid course code. Available codes: {', '.join(COURSE_MAP.keys())}"
                )
                return
                
            course_name = COURSE_MAP[course_code]
            
            send_telegram_message(
                chat_id,
                f"Processing request to give access to {email} for {course_name}..."
            )
            
            # Process the request using the external service
            def give_access_task():
                try:
                    # Prepare the request data
                    data = {
                        "action": "give_access",
                        "email": email,
                        "course_name": course_name,
                        "learnyst_username": LEARNYST_USERNAME,
                        "learnyst_password": LEARNYST_PASSWORD,
                        "api_key": EXTERNAL_SERVICE_API_KEY
                    }
                    
                    # Send the request to the external service
                    response = requests.post(
                        f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
                        json=data,
                        headers={"Content-Type": "application/json"},
                        timeout=180  # 3 minutes timeout for automation
                    )
                    
                    # Process the response
                    if response.status_code == 200:
                        result = response.json()
                        message = result.get("message", "Access granted successfully")
                        send_telegram_message(chat_id, message)
                        add_log_message(message)
                    else:
                        error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(
                            chat_id,
                            f"Failed to give access: Service returned error {response.status_code}"
                        )
                except Exception as e:
                    error_msg = f"Error in give_access task: {str(e)}"
                    logger.error(error_msg)
                    add_log_message(error_msg)
                    send_telegram_message(chat_id, f"Error: {str(e)}")
                
            # Run in a thread to avoid blocking
            thread = threading.Thread(target=give_access_task)
            thread.daemon = True
            thread.start()
            return
        
        # Case 2: Enroll new user
        enroll_pattern = r'@LearnystBot\s+(\S+@\S+)\s+(.+?)\s+(?:access|enroll)\s+(\w+)'
        enroll_match = re.search(enroll_pattern, message_text)
        
        if enroll_match:
            email = enroll_match.group(1)
            full_name = enroll_match.group(2)
            course_code = enroll_match.group(3).lower()
            
            if course_code not in COURSE_MAP:
                send_telegram_message(
                    chat_id,
                    f"Invalid course code. Available codes: {', '.join(COURSE_MAP.keys())}"
                )
                return
                
            course_name = COURSE_MAP[course_code]
            
            send_telegram_message(
                chat_id,
                f"Processing request to enroll {full_name} ({email}) to {course_name}..."
            )
            
            # Process the request using the external service
            def enroll_user_task():
                try:
                    # Prepare the request data
                    data = {
                        "action": "enroll_user",
                        "email": email,
                        "full_name": full_name,
                        "course_name": course_name,
                        "learnyst_username": LEARNYST_USERNAME,
                        "learnyst_password": LEARNYST_PASSWORD,
                        "api_key": EXTERNAL_SERVICE_API_KEY
                    }
                    
                    # Send the request to the external service
                    response = requests.post(
                        f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
                        json=data,
                        headers={"Content-Type": "application/json"},
                        timeout=180  # 3 minutes timeout for automation
                    )
                    
                    # Process the response
                    if response.status_code == 200:
                        result = response.json()
                        message = result.get("message", "User enrolled successfully")
                        send_telegram_message(chat_id, message)
                        add_log_message(message)
                    else:
                        error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(
                            chat_id,
                            f"Failed to enroll user: Service returned error {response.status_code}"
                        )
                except Exception as e:
                    error_msg = f"Error in enroll_user task: {str(e)}"
                    logger.error(error_msg)
                    add_log_message(error_msg)
                    send_telegram_message(chat_id, f"Error: {str(e)}")
                
            # Run in a thread to avoid blocking
            thread = threading.Thread(target=enroll_user_task)
            thread.daemon = True
            thread.start()
            return
        
        # Case 3: Suspend user
        suspend_pattern = r'@LearnystBot\s+(\S+@\S+|\S+)\s+suspend'
        suspend_match = re.search(suspend_pattern, message_text)
        
        if suspend_match:
            user_identifier = suspend_match.group(1)
            
            send_telegram_message(
                chat_id,
                f"Processing request to suspend user {user_identifier}..."
            )
            
            # Process the request using the external service
            def suspend_user_task():
                try:
                    # Prepare the request data
                    data = {
                        "action": "suspend_user",
                        "user_identifier": user_identifier,
                        "learnyst_username": LEARNYST_USERNAME,
                        "learnyst_password": LEARNYST_PASSWORD,
                        "api_key": EXTERNAL_SERVICE_API_KEY
                    }
                    
                    # Send the request to the external service
                    response = requests.post(
                        f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
                        json=data,
                        headers={"Content-Type": "application/json"},
                        timeout=180  # 3 minutes timeout for automation
                    )
                    
                    # Process the response
                    if response.status_code == 200:
                        result = response.json()
                        message = result.get("message", "User suspended successfully")
                        send_telegram_message(chat_id, message)
                        add_log_message(message)
                    else:
                        error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(
                            chat_id,
                            f"Failed to suspend user: Service returned error {response.status_code}"
                        )
                except Exception as e:
                    error_msg = f"Error in suspend_user task: {str(e)}"
                    logger.error(error_msg)
                    add_log_message(error_msg)
                    send_telegram_message(chat_id, f"Error: {str(e)}")
                
            # Run in a thread to avoid blocking
            thread = threading.Thread(target=suspend_user_task)
            thread.daemon = True
            thread.start()
            return
        
        # Case 4: Delete user
        delete_pattern = r'@LearnystBot\s+(\S+@\S+|\S+)\s+delete'
        delete_match = re.search(delete_pattern, message_text)
        
        if delete_match:
            user_identifier = delete_match.group(1)
            
            send_telegram_message(
                chat_id,
                f"Processing request to delete user {user_identifier}..."
            )
            
            # Process the request using the external service
            def delete_user_task():
                try:
                    # Prepare the request data
                    data = {
                        "action": "delete_user",
                        "user_identifier": user_identifier,
                        "learnyst_username": LEARNYST_USERNAME,
                        "learnyst_password": LEARNYST_PASSWORD,
                        "api_key": EXTERNAL_SERVICE_API_KEY
                    }
                    
                    # Send the request to the external service
                    response = requests.post(
                        f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
                        json=data,
                        headers={"Content-Type": "application/json"},
                        timeout=180  # 3 minutes timeout for automation
                    )
                    
                    # Process the response
                    if response.status_code == 200:
                        result = response.json()
                        message = result.get("message", "User deleted successfully")
                        send_telegram_message(chat_id, message)
                        add_log_message(message)
                    else:
                        error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(
                            chat_id,
                            f"Failed to delete user: Service returned error {response.status_code}"
                        )
                except Exception as e:
                    error_msg = f"Error in delete_user task: {str(e)}"
                    logger.error(error_msg)
                    add_log_message(error_msg)
                    send_telegram_message(chat_id, f"Error: {str(e)}")
                
            # Run in a thread to avoid blocking
            thread = threading.Thread(target=delete_user_task)
            thread.daemon = True
            thread.start()
            return
        
        # If no pattern matches
        send_telegram_message(
            chat_id,
            "Command not recognized. Please use one of the following formats:\n"
            "- @LearnystBot [email] access [course_code]\n"
            "- @LearnystBot [email] [full_name] enroll [course_code]\n"
            "- @LearnystBot [email] suspend\n"
            "- @LearnystBot [email] delete"
        )
        
    except Exception as e:
        error_message = f"Error processing command: {str(e)}"
        logger.error(error_message)
        add_log_message(error_message)
        send_telegram_message(chat_id, f"An error occurred: {str(e)}")

def polling_thread_function():
    """Function to poll for new messages from Telegram."""
    global is_polling
    last_update_id = 0
    
    while is_polling:
        try:
            # Get updates from Telegram
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {
                "offset": last_update_id + 1,
                "timeout": 30
            }
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data["ok"] and data["result"]:
                    updates = data["result"]
                    for update in updates:
                        # Update the last update ID
                        if update["update_id"] > last_update_id:
                            last_update_id = update["update_id"]
                        
                        # Process the message
                        if "message" in update:
                            process_message(update["message"])
            else:
                logger.error(f"Error polling Telegram: {response.status_code}, {response.text}")
                add_log_message(f"Error polling Telegram: {response.status_code}, {response.text}")
                
            # Sleep briefly to avoid hitting rate limits
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in polling thread: {str(e)}")
            add_log_message(f"Error in polling thread: {str(e)}")
            time.sleep(5)  # Wait a bit longer if there's an error

def start_bot():
    """Start the Telegram bot."""
    global is_polling, polling_thread
    
    # If the bot is already running, don't start it again
    if BOT_STATUS.get('status') == 'Active' and is_polling:
        add_log_message("Bot is already running")
        return False
        
    try:
        BOT_STATUS['status'] = 'Starting'
        add_log_message("Starting bot...")
        
        # Test the Telegram token
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url)
        
        if response.status_code != 200:
            error_message = f"Invalid Telegram bot token: {response.status_code}, {response.text}"
            logger.error(error_message)
            add_log_message(error_message)
            BOT_STATUS['status'] = 'Error'
            return False
        
        # Start the polling thread
        is_polling = True
        polling_thread = threading.Thread(target=polling_thread_function)
        polling_thread.daemon = True
        polling_thread.start()
        
        BOT_STATUS['status'] = 'Active'
        add_log_message("Bot is now active and listening for commands.")
        return True
        
    except Exception as e:
        BOT_STATUS['status'] = 'Error'
        error_message = f"Error starting bot: {str(e)}"
        logger.error(error_message)
        add_log_message(error_message)
        return False
        
def stop_bot():
    """Stop the Telegram bot."""
    global is_polling, polling_thread
    
    if not is_polling:
        add_log_message("No bot instance running to stop")
        return False
        
    try:
        BOT_STATUS['status'] = 'Stopping'
        add_log_message("Stopping the Telegram bot...")
        
        # Stop the polling thread
        is_polling = False
        
        # Wait for the polling thread to finish
        if polling_thread:
            polling_thread.join(timeout=5)
            
        BOT_STATUS['status'] = 'Inactive'
        add_log_message("Bot has been stopped")
        return True
        
    except Exception as e:
        error_message = f"Error stopping bot: {str(e)}"
        logger.error(error_message)
        add_log_message(error_message)
        BOT_STATUS['status'] = 'Error'
        return False