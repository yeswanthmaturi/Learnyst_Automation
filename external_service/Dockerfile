FROM amazonlinux:2

# Install dependencies
RUN yum -y update && \
    yum -y install python3 python3-pip wget unzip tar gzip shadow-utils && \
    yum -y install xorg-x11-server-Xvfb gtk3 libnotify nss alsa-lib && \
    yum -y groupinstall "Development Tools" && \
    yum -y install nodejs npm && \
    pip3 install --upgrade pip

# Set up working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Install Playwright
RUN python3 -m playwright install --with-deps chromium

# Copy application files
COPY . .

# Expose port
EXPOSE 5001

# Run the application
CMD ["python3", "server.py"]