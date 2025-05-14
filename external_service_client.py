import os
import json
import logging
import time
import requests
from config import add_log_message

# Configure logging
logger = logging.getLogger(__name__)

# Default to localhost during development
DEFAULT_SERVICE_URL = "http://localhost:5500"

# Get the external service URL from environment variables
EXTERNAL_SERVICE_URL = os.environ.get("EXTERNAL_SERVICE_URL", DEFAULT_SERVICE_URL)
EXTERNAL_SERVICE_API_KEY = os.environ.get("EXTERNAL_SERVICE_API_KEY", "")

# Set to True during development if external service is not yet available
DEVELOPMENT_MODE = os.environ.get("DEVELOPMENT_MODE", "True").lower() == "true"

def simulate_response(action, **kwargs):
    """Simulate a response during development mode when external service is not available."""
    time.sleep(2)  # Simulate processing time
    
    if action == "give_access":
        message = f"[SIMULATION] Access granted to {kwargs.get('email')} for course {kwargs.get('course_name')}"
        logger.info(message)
        add_log_message(message)
        return {"message": message, "success": True}
    
    elif action == "enroll_user":
        message = f"[SIMULATION] User {kwargs.get('email')} ({kwargs.get('full_name')}) enrolled in course {kwargs.get('course_name')}"
        logger.info(message)
        add_log_message(message)
        return {"message": message, "success": True}
    
    elif action == "suspend_user":
        message = f"[SIMULATION] User {kwargs.get('user_identifier')} suspended"
        logger.info(message)
        add_log_message(message)
        return {"message": message, "success": True}
    
    elif action == "delete_user":
        message = f"[SIMULATION] User {kwargs.get('user_identifier')} deleted"
        logger.info(message)
        add_log_message(message)
        return {"message": message, "success": True}
    
    else:
        message = f"[SIMULATION] Unknown action: {action}"
        logger.error(message)
        add_log_message(message)
        return {"message": message, "success": False}

def give_access(email, course_name):
    """Send a request to give access to a course for an existing user."""
    logger.info(f"Sending give_access request to external service for {email}, course: {course_name}")
    add_log_message(f"Sending give_access request to external service for {email}, course: {course_name}")
    
    # If in development mode, use simulated response
    if DEVELOPMENT_MODE:
        logger.info("DEVELOPMENT MODE: Using simulated response")
        add_log_message("DEVELOPMENT MODE: Using simulated response")
        result = simulate_response("give_access", email=email, course_name=course_name)
        return result.get("message", "Access granted successfully (simulation)")
    
    try:
        # Prepare the request data
        data = {
            "action": "give_access",
            "email": email,
            "course_name": course_name,
            "api_key": EXTERNAL_SERVICE_API_KEY
        }
        
        # Send the request to the external service
        response = requests.post(
            f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
            json=data,
            headers={
                "Content-Type": "application/json"
            },
            timeout=60  # 60 seconds timeout
        )
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            add_log_message(f"External service response: {result.get('message', 'Success')}")
            return result.get("message", "Access granted successfully")
        else:
            error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
            logger.error(error_msg)
            add_log_message(error_msg)
            return f"Failed to give access: Service returned error {response.status_code}"
            
    except requests.RequestException as e:
        error_msg = f"Connection error with external service: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"Failed to connect to external service: {str(e)}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"An unexpected error occurred: {str(e)}"

def enroll_user(email, full_name, course_name):
    """Send a request to enroll a new user to a course."""
    logger.info(f"Sending enroll_user request to external service for {email}, {full_name}, course: {course_name}")
    add_log_message(f"Sending enroll_user request to external service for {email}, {full_name}, course: {course_name}")
    
    # If in development mode, use simulated response
    if DEVELOPMENT_MODE:
        logger.info("DEVELOPMENT MODE: Using simulated response")
        add_log_message("DEVELOPMENT MODE: Using simulated response")
        result = simulate_response("enroll_user", email=email, full_name=full_name, course_name=course_name)
        return result.get("message", "User enrolled successfully (simulation)")
    
    try:
        # Prepare the request data
        data = {
            "action": "enroll_user",
            "email": email,
            "full_name": full_name,
            "course_name": course_name,
            "api_key": EXTERNAL_SERVICE_API_KEY
        }
        
        # Send the request to the external service
        response = requests.post(
            f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
            json=data,
            headers={
                "Content-Type": "application/json"
            },
            timeout=60  # 60 seconds timeout
        )
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            add_log_message(f"External service response: {result.get('message', 'Success')}")
            return result.get("message", "User enrolled successfully")
        else:
            error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
            logger.error(error_msg)
            add_log_message(error_msg)
            return f"Failed to enroll user: Service returned error {response.status_code}"
            
    except requests.RequestException as e:
        error_msg = f"Connection error with external service: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"Failed to connect to external service: {str(e)}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"An unexpected error occurred: {str(e)}"

def suspend_user(user_identifier):
    """Send a request to suspend a user account."""
    logger.info(f"Sending suspend_user request to external service for {user_identifier}")
    add_log_message(f"Sending suspend_user request to external service for {user_identifier}")
    
    # If in development mode, use simulated response
    if DEVELOPMENT_MODE:
        logger.info("DEVELOPMENT MODE: Using simulated response")
        add_log_message("DEVELOPMENT MODE: Using simulated response")
        result = simulate_response("suspend_user", user_identifier=user_identifier)
        return result.get("message", "User suspended successfully (simulation)")
    
    try:
        # Prepare the request data
        data = {
            "action": "suspend_user",
            "user_identifier": user_identifier,
            "api_key": EXTERNAL_SERVICE_API_KEY
        }
        
        # Send the request to the external service
        response = requests.post(
            f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
            json=data,
            headers={
                "Content-Type": "application/json"
            },
            timeout=60  # 60 seconds timeout
        )
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            add_log_message(f"External service response: {result.get('message', 'Success')}")
            return result.get("message", "User suspended successfully")
        else:
            error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
            logger.error(error_msg)
            add_log_message(error_msg)
            return f"Failed to suspend user: Service returned error {response.status_code}"
            
    except requests.RequestException as e:
        error_msg = f"Connection error with external service: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"Failed to connect to external service: {str(e)}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"An unexpected error occurred: {str(e)}"

def delete_user(user_identifier):
    """Send a request to delete a user account."""
    logger.info(f"Sending delete_user request to external service for {user_identifier}")
    add_log_message(f"Sending delete_user request to external service for {user_identifier}")
    
    # If in development mode, use simulated response
    if DEVELOPMENT_MODE:
        logger.info("DEVELOPMENT MODE: Using simulated response")
        add_log_message("DEVELOPMENT MODE: Using simulated response")
        result = simulate_response("delete_user", user_identifier=user_identifier)
        return result.get("message", "User deleted successfully (simulation)")
    
    try:
        # Prepare the request data
        data = {
            "action": "delete_user",
            "user_identifier": user_identifier,
            "api_key": EXTERNAL_SERVICE_API_KEY
        }
        
        # Send the request to the external service
        response = requests.post(
            f"{EXTERNAL_SERVICE_URL}/learnyst/execute",
            json=data,
            headers={
                "Content-Type": "application/json"
            },
            timeout=60  # 60 seconds timeout
        )
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            add_log_message(f"External service response: {result.get('message', 'Success')}")
            return result.get("message", "User deleted successfully")
        else:
            error_msg = f"External service error: HTTP {response.status_code}, {response.text}"
            logger.error(error_msg)
            add_log_message(error_msg)
            return f"Failed to delete user: Service returned error {response.status_code}"
            
    except requests.RequestException as e:
        error_msg = f"Connection error with external service: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"Failed to connect to external service: {str(e)}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        add_log_message(error_msg)
        return f"An unexpected error occurred: {str(e)}"