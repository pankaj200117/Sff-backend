#!/bin/bash

# Update package list and install necessary packages
apt-get update -y
apt-get install -y python3-pip python3-venv

# Navigate to the application directory
cd /var/www/html/Sff-backend

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install required Python packages
pip install -r requirements.txt

# Ensure .env file permissions are set correctly
chown www-data:www-data .env

