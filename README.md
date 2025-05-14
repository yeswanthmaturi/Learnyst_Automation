# Learnyst Telegram Bot

This bot allows you to manage Learnyst courses via Telegram commands.

## Features

- Give access to an existing user 
- Enroll a new user to a course
- Suspend a user account
- Delete a user account

## Commands

### Give Access to Existing User
```
@LearnystBot [email] access [course_code]
```
Example: `@LearnystBot user@example.com access fs1`

### Enroll New User
```
@LearnystBot [email] [full_name] enroll [course_code]
```
Example: `@LearnystBot user@example.com John Doe enroll fs2`

### Suspend User
```
@LearnystBot [email] suspend
```
Example: `@LearnystBot user@example.com suspend`

### Delete User
```
@LearnystBot [email] delete
```
Example: `@LearnystBot user@example.com delete`

### Available Course Codes:
- fs1 - Full Stack 1
- fs2 - Full Stack 2
- fs3 - Full Stack 3
- fs4 - Full Stack 4
- fs5 - Full Stack 5
- meta - Meta Interview Advance Concepts

## Architecture

The system uses a two-part architecture:

1. **Telegram Bot Server (This Application)**:
   - Handles communication with Telegram API
   - Processes commands and sends them to the external service
   - Provides web dashboard for monitoring

2. **External Automation Service** (To be set up separately):
   - Runs browser automation using Playwright
   - Performs the actual operations on Learnyst
   - Communicates via a simple REST API

## Setting Up the External Service

Since Replit has limitations with browser automation, you'll need to run the automation service on a machine that can run Chrome/Playwright properly.

### External Service Requirements

1. A server or computer that can run:
   - Node.js or Python
   - Playwright
   - A REST API server
   
2. Implement the following API endpoint:
   ```
   POST /learnyst/execute
   ```

3. The endpoint should accept JSON payloads with this structure:
   ```json
   {
     "action": "give_access|enroll_user|suspend_user|delete_user",
     "email": "user@example.com",
     "full_name": "John Doe",  // Only for enroll_user action
     "course_name": "Full Stack 1",  // Only for give_access and enroll_user actions
     "user_identifier": "user@example.com",  // Only for suspend_user and delete_user actions
     "learnyst_username": "admin@example.com",
     "learnyst_password": "password",
     "api_key": "your-api-key"
   }
   ```

4. The endpoint should return a JSON response:
   ```json
   {
     "success": true|false,
     "message": "Operation result message"
   }
   ```

## Environment Variables

Set the following environment variables:

1. `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
2. `EXTERNAL_SERVICE_URL`: URL of your external automation service
3. `EXTERNAL_SERVICE_API_KEY`: API key for your external service
4. `LEARNYST_USERNAME`: Your Learnyst admin username
5. `LEARNYST_PASSWORD`: Your Learnyst admin password