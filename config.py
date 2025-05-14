# Configuration file for the Learnyst Telegram Bot

# Global variables to track bot status and log messages
BOT_STATUS = {'status': 'Inactive'}
LOG_MESSAGES = []

def add_log_message(message):
    """Add a log message to the global log queue."""
    LOG_MESSAGES.append(message)
    # Keep only the last 100 messages
    if len(LOG_MESSAGES) > 100:
        LOG_MESSAGES.pop(0)
