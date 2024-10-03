#!/bin/bash
# This script runs after the installation phase

# Navigate to the app directory
cd /var/www/html/Sff-backend

# Install Python dependencies from requirements.txt
pip3 install -r requirements.txt

# Ensure proper file permissions
sudo chown -R www-data:www-data /var/www/html/Sff-backend
sudo chmod -R 755 /var/www/html/Sff-backend

echo "After Install phase is complete."

