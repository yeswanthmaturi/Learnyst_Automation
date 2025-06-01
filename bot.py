import os
from dotenv import load_dotenv
import re
import logging
import threading
import time
import json
import requests
import random
from queue import Queue
from config import BOT_STATUS, add_log_message
from browser_agent_runner import run_browser_agent
from telegram import Update
from telegram.ext import CallbackContext

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the Telegram bot token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print("Loaded Telegram token:", TELEGRAM_BOT_TOKEN)

# Map course shortcuts to full names
COURSE_MAP = {
    'fs1': 'Full Stack 1',
    'fs2': 'Full Stack 2',
    'fs3': 'Full Stack 3',
    'fs4': 'Full Stack 4',
    'fs5': 'Full Stack 5',
    'meta': 'Meta Interview Advance Concepts',
    'own': 'Ownership'
}

# Learnyst credentials
LEARNYST_EMAILS = [email.strip() for email in os.getenv("LEARNYST_USERNAME", "").split(",")]
LEARNYST_PASSWORD = os.getenv("LEARNYST_PASSWORD")

# Bot polling variables
is_polling = False
polling_thread = None

# Queue management
command_queue = Queue()
is_processing = False
last_task_time = 0
TASK_DELAY = 180  # 3 minutes in seconds

def get_random_learnyst_email():
    """Get a random Learnyst admin email for login."""
    if not LEARNYST_EMAILS:
        raise ValueError("No Learnyst emails configured in environment variables")
    return random.choice(LEARNYST_EMAILS)

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

def process_queued_commands():
    """Process commands in the queue with delay between tasks."""
    global is_processing, last_task_time
    
    while not command_queue.empty():
        if is_processing:
            time.sleep(1)
            continue
            
        # Check if enough time has passed since last task
        current_time = time.time()
        if current_time - last_task_time < TASK_DELAY:
            time.sleep(1)
            continue
            
        is_processing = True
        command_data = command_queue.get()
        
        try:
            chat_id = command_data['chat_id']
            message_text = command_data['message_text']
            
            # Process the command
            process_command(chat_id, message_text)
            
            # Update last task time
            last_task_time = time.time()
            
        except Exception as e:
            error_msg = f"Error processing queued command: {str(e)}"
            logger.error(error_msg)
            add_log_message(error_msg)
            if 'chat_id' in command_data:
                send_telegram_message(command_data['chat_id'], f"Error: {str(e)}")
                
        finally:
            is_processing = False
            command_queue.task_done()

def process_command(chat_id, message_text):
    """Process a single command with retry logic."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            send_telegram_message(chat_id, "Processing your request... connecting to browser agent...")
            add_log_message("Connecting to browser agent")

            # --- Give Access ---
            access_pattern = r'@LearnystBot\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+access\s+(\w+)'
            access_match = re.fullmatch(access_pattern, message_text.strip())
            if access_match:
                email = access_match.group(1).strip()
                course_code = access_match.group(2).lower().strip()
                course_name = COURSE_MAP.get(course_code)
                if not course_name:
                    send_telegram_message(chat_id, f"Invalid course code. Available codes: {', '.join(COURSE_MAP.keys())}")
                    return
                send_telegram_message(chat_id, f"Processing request to give access to {email} for {course_name}...")
                def give_access_task():
                    try:
                        admin_email = get_random_learnyst_email()
                        prompt = (f"Go to https://techpathai.learnyst.com/admin and log in using the following credentials: "
                                  f"Username – {admin_email}, Password – {LEARNYST_PASSWORD}. "
                                  f"After logging in, navigate to the 'Users' tab in the top menu, then select 'Learners' from the dropdown. "
                                  f"Locate the search bar labelled 'Search by Email (alt+k)' , which is positioned directly beneath the 'All Learners' heading to find the learner with the email '{email}' and click on their profile. "
                                  f"In the learner's profile page, click the 'Add Product' button at the top right. "
                                  f"In the form that appears, open the 'Select Product' dropdown and search for '{course_name}' and select '{course_name}' element. "
                                  f"And just click 'Save & Next' button. "
                                  f"On the following screen, locate the row labeled 'Base plan' and click the small circle (radio button) next to it and click 'Add Offline Payment'. "
                                  f"In the popup, Just remove the default text in the 'Remarks' section and enter 'Plan added by admin today', then click 'Save'. "
                                  f"This completes the process of assigning the course, just return the message 'Access granted successfully'.")
                        try:
                            result = run_browser_agent(prompt)
                            # Check both result and logs for success indicators
                            if isinstance(result, str):
                                agent_output = result
                            else:
                                agent_output = str(result)
                            
                            # Log the full agent output for debugging
                            add_log_message(f"Full agent output: {agent_output}")
                            
                            if "successfully" in agent_output.lower():
                                send_telegram_message(chat_id, f"✅ Successfully granted access to {course_name} for {email}")
                                return True
                            else:
                                send_telegram_message(chat_id, result)
                                return False
                            add_log_message(result)
                        except Exception as e:
                            error_msg = f"Browser agent error (give_access): {str(e)}"
                            logger.error(error_msg)
                            add_log_message(error_msg)
                            send_telegram_message(chat_id, f"Error: {str(e)}")
                            return False
                    except Exception as e:
                        error_msg = f"Error in give_access task: {str(e)}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(chat_id, f"Error: {str(e)}")
                        return False
                success = give_access_task()
                if success:
                    return True
                retry_count += 1
                if retry_count < max_retries:
                    send_telegram_message(chat_id, f"Retrying command in 3 minutes... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(TASK_DELAY)
                continue

            # --- Enroll New User ---
            enroll_pattern = r'@LearnystBot\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+\(([^)]+)\)\s+enroll\s+(\w+)'
            enroll_match = re.fullmatch(enroll_pattern, message_text.strip())
            if enroll_match:
                email = enroll_match.group(1).strip()
                full_name = enroll_match.group(2).strip()
                course_code = enroll_match.group(3).lower().strip()
                course_name = COURSE_MAP.get(course_code)
                if not course_name:
                    send_telegram_message(chat_id, f"Invalid course code. Available codes: {', '.join(COURSE_MAP.keys())}")
                    return
                send_telegram_message(chat_id, f"Processing request to enroll {full_name} ({email}) to {course_name}...")
                def enroll_user_task():
                    try:
                        admin_email = get_random_learnyst_email()
                        prompt = (f"Go to https://techpathai.learnyst.com/admin and login with "
                                  f"Username – {admin_email}, Password – {LEARNYST_PASSWORD}. "
                                  f"After logging in, navigate to the 'Users' tab in the top menu, then select 'Learners' from the dropdown. "
                                  f"Click the '+Add' button to add a new learner. "
                                  f"In the form that appears, fill in the Learner Email ID field using '{email}', "
                                  f"and fill in the Learner Full Name field using '{full_name}'. "
                                  f"Navigate to the 'Product' dropdown, and press enter. "
                                  f"Then click the 'Add New Learner' button."
                                  f"This completes the process of enrolling the learner, just return the message 'Learner enrolled successfully'.")
                        try:
                            result = run_browser_agent(prompt)
                            # Check both result and logs for success indicators
                            if isinstance(result, str):
                                agent_output = result
                            else:
                                agent_output = str(result)
                            
                            # Log the full agent output for debugging
                            add_log_message(f"Full agent output: {agent_output}")
                            
                            if "successfully" in agent_output:
                                send_telegram_message(chat_id, f"✅ Successfully enrolled {full_name} ({email}) with access to {course_name}")
                                return True
                            else:
                                send_telegram_message(chat_id, result)
                                return False
                            add_log_message(result)
                        except Exception as e:
                            error_msg = f"Browser agent error (enroll): {str(e)}"
                            logger.error(error_msg)
                            add_log_message(error_msg)
                            send_telegram_message(chat_id, f"Error: {str(e)}")
                            return False
                    except Exception as e:
                        error_msg = f"Error in enroll_user task: {str(e)}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(chat_id, f"Error: {str(e)}")
                        return False
                success = enroll_user_task()
                if success:
                    return True
                retry_count += 1
                if retry_count < max_retries:
                    send_telegram_message(chat_id, f"Retrying command in 3 minutes... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(TASK_DELAY)
                continue

            # --- Suspend User ---
            suspend_pattern = r'@LearnystBot\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+suspend'
            suspend_match = re.fullmatch(suspend_pattern, message_text.strip())
            if suspend_match:
                email = suspend_match.group(1).strip()
                send_telegram_message(chat_id, f"Processing request to suspend user {email}...")
                def suspend_user_task():
                    try:
                        admin_email = get_random_learnyst_email()
                        prompt = (f"Go to https://techpathai.learnyst.com/admin and log in using "
                                  f"Username – {admin_email}, Password – {LEARNYST_PASSWORD}. "
                                  f"After logging in, navigate to the 'Users' tab in the top menu and select 'Learners' from the dropdown. "
                                  f"Locate the search bar labelled 'Search by Email (alt+k)' , which is positioned directly beneath the 'All Learners' heading to find the learner with the email '{email}'. "
                                  f"Once the learner is located, click on their profile. "
                                  f"Then, click on 'More' dropdown and select 'Settings'. "
                                  f"On the settings page, click 'Suspend Learner Account' from the left-hand sidebar. "
                                  f"On the suspension screen, click the 'Suspend' button and then confirm by clicking 'Suspend' again at the bottom of the screen."
                                  f"This completes the process of suspending the learner, just return the message 'Learner suspended successfully'.")
                        try:
                            result = run_browser_agent(prompt)
                            # Check both result and logs for success indicators
                            if isinstance(result, str):
                                agent_output = result
                            else:
                                agent_output = str(result)
                            
                            # Log the full agent output for debugging
                            add_log_message(f"Full agent output: {agent_output}")
                            
                            if "successfully" in agent_output:
                                send_telegram_message(chat_id, f"✅ Successfully suspended user: {email}")
                                return True
                            else:
                                send_telegram_message(chat_id, result)
                                return False
                            add_log_message(result)
                        except Exception as e:
                            error_msg = f"Browser agent error (suspend): {str(e)}"
                            logger.error(error_msg)
                            add_log_message(error_msg)
                            send_telegram_message(chat_id, f"Error: {str(e)}")
                            return False
                    except Exception as e:
                        error_msg = f"Error in suspend_user task: {str(e)}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(chat_id, f"Error: {str(e)}")
                        return False
                success = suspend_user_task()
                if success:
                    return True
                retry_count += 1
                if retry_count < max_retries:
                    send_telegram_message(chat_id, f"Retrying command in 3 minutes... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(TASK_DELAY)
                continue

            # --- Delete User ---
            delete_pattern = r'@LearnystBot\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+delete'
            delete_match = re.fullmatch(delete_pattern, message_text.strip())
            if delete_match:
                email = delete_match.group(1).strip()
                send_telegram_message(chat_id, f"Processing request to delete user {email}...")
                def delete_user_task():
                    try:
                        admin_email = get_random_learnyst_email()
                        prompt = (f"Go to https://techpathai.learnyst.com/admin and log in using "
                                  f"Username – {admin_email}, Password – {LEARNYST_PASSWORD}. "
                                  f"After logging in, navigate to the 'Users' tab in the top menu and select 'Learners' from the dropdown. "
                                  f"Locate the search bar labelled 'Search by Email (alt+k)' , which is positioned directly beneath the 'All Learners' heading to find the learner with the email '{email}'. "
                                  f"Once the learner is located, click on their profile. "
                                  f"Then, click on 'More' dropdown and select 'Settings'. "
                                  f"On the settings page, click 'Delete Learner Account' from the left-hand sidebar. "
                                  f"On the screen, click the 'Delete' button to complete the process."
                                  f"This will complete the process of deleting the learner, just return the message 'Learner deleted successfully'.")
                        try:
                            result = run_browser_agent(prompt)
                            # Check both result and logs for success indicators
                            if isinstance(result, str):
                                agent_output = result
                            else:
                                agent_output = str(result)
                            
                            # Log the full agent output for debugging
                            add_log_message(f"Full agent output: {agent_output}")
                            
                            if "successfully" in agent_output:
                                send_telegram_message(chat_id, f"✅ Successfully deleted user: {email}")
                                return True
                            else:
                                send_telegram_message(chat_id, result)
                                return False
                            add_log_message(result)
                        except Exception as e:
                            error_msg = f"Browser agent error (delete): {str(e)}"
                            logger.error(error_msg)
                            add_log_message(error_msg)
                            send_telegram_message(chat_id, f"Error: {str(e)}")
                            return False
                    except Exception as e:
                        error_msg = f"Error in delete_user task: {str(e)}"
                        logger.error(error_msg)
                        add_log_message(error_msg)
                        send_telegram_message(chat_id, f"Error: {str(e)}")
                        return False
                success = delete_user_task()
                if success:
                    return True
                retry_count += 1
                if retry_count < max_retries:
                    send_telegram_message(chat_id, f"Retrying command in 3 minutes... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(TASK_DELAY)
                continue

            # --- No Command Matches ---
            send_telegram_message(
                chat_id,
                "Invalid command format. Please use one of the following formats:\n"
                "1. @LearnystBot email@example.com access course_code\n"
                "2. @LearnystBot email@example.com (Full Name) enroll course_code\n"
                "3. @LearnystBot email@example.com suspend\n"
                "4. @LearnystBot email@example.com delete\n"
                "\nAvailable course codes: " + ", ".join(COURSE_MAP.keys())
            )
            return True
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                send_telegram_message(chat_id, f"Retrying command in 3 minutes... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(TASK_DELAY)
            continue
    return False

def process_message(message):
    """Process a message from Telegram."""
    chat_id = message.get('chat', {}).get('id')
    message_text = message.get('text', '')

    # Check if message mentions @LearnystBot
    if '@LearnystBot' not in message_text:
        return

    logger.info(f"Received command: {message_text}")
    add_log_message(f"Received command: {message_text}")

    # Add command to queue
    command_queue.put({
        'chat_id': chat_id,
        'message_text': message_text
    })
    
    # Notify user about queuing
    queue_position = command_queue.qsize()
    if queue_position > 0:
        send_telegram_message(chat_id, f"Your command has been queued. Position in queue: {queue_position}")
    
    # Start queue processing if not already running
    if not is_processing:
        threading.Thread(target=process_queued_commands, daemon=True).start()

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