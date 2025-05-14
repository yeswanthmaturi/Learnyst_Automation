# Learnyst Automation External Service

This service provides browser automation for the Learnyst Telegram Bot.

## Overview

This external service uses Playwright to perform browser automation tasks on the Learnyst website. It exposes a REST API that the Telegram bot can call to execute actions on Learnyst.

## Features

- Give access to courses for existing users
- Enroll new users to courses
- Suspend user accounts
- Delete user accounts
- API key authentication
- Browser session management for performance

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Internet connection to access Learnyst website

### Configuration

1. Create a `.env` file or edit the existing one to set your API key:

```
API_KEY=your-secret-api-key
PORT=5500
HOST=0.0.0.0
```

### Running with Docker Compose

1. Build and start the service:

```bash
docker-compose up -d
```

2. Check the logs:

```bash
docker-compose logs -f
```

3. To stop the service:

```bash
docker-compose down
```

## API Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok",
  "message": "Learnyst automation service is running",
  "timestamp": "2023-05-14T12:00:00.000Z"
}
```

### Execute Learnyst Action

```
POST /learnyst/execute
```

Request body:
```json
{
  "action": "give_access",
  "email": "user@example.com",
  "course_name": "Full Stack 1",
  "learnyst_username": "admin@example.com",
  "learnyst_password": "password",
  "api_key": "your-secret-api-key"
}
```

Response:
```json
{
  "success": true,
  "message": "✅ Successfully gave access to Full Stack 1 for user user@example.com"
}
```

## Action Types

### 1. Give Access to Existing User

```json
{
  "action": "give_access",
  "email": "user@example.com",
  "course_name": "Full Stack 1",
  "learnyst_username": "admin@example.com",
  "learnyst_password": "password",
  "api_key": "your-secret-api-key"
}
```

### 2. Enroll New User

```json
{
  "action": "enroll_user",
  "email": "user@example.com",
  "full_name": "John Doe",
  "course_name": "Full Stack 1",
  "learnyst_username": "admin@example.com",
  "learnyst_password": "password",
  "api_key": "your-secret-api-key"
}
```

### 3. Suspend User

```json
{
  "action": "suspend_user",
  "user_identifier": "user@example.com",
  "learnyst_username": "admin@example.com",
  "learnyst_password": "password",
  "api_key": "your-secret-api-key"
}
```

### 4. Delete User

```json
{
  "action": "delete_user",
  "user_identifier": "user@example.com",
  "learnyst_username": "admin@example.com",
  "learnyst_password": "password",
  "api_key": "your-secret-api-key"
}
```

## Deployment to AWS EC2

Once you've tested the service locally with Docker, you can deploy it to an AWS EC2 instance running Amazon Linux 2:

1. Launch an EC2 instance with Amazon Linux 2
2. Install Docker and Docker Compose
3. Clone this repository or copy the files to the EC2 instance
4. Set up your environment variables in the `.env` file
5. Run the service with Docker Compose

Example EC2 setup commands:
```bash
# Install Docker
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository (or copy files)
git clone <repository-url>
cd <repository-directory>

# Create .env file
echo "API_KEY=your-secret-api-key" > .env
echo "PORT=5500" >> .env
echo "HOST=0.0.0.0" >> .env

# Run the service
docker-compose up -d
```

## Security Considerations

- The API key must be kept secret and should be changed regularly
- The service should be run behind a firewall or VPN to restrict access
- HTTPS should be used for production environments
- The Learnyst credentials should be stored securely