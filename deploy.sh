#!/bin/bash
# Stop the script if any command fails
set -e

echo "Starting deployment..."
cd /home/saif/Code/FriendshipLamp

echo "Pulling latest code from main..."
git pull origin main

echo "Installing/updating dependencies..."
# If you have requirements.txt:
# ./venv/bin/pip install -r requirements.txt

# The reload must be done by restarting the actual systemd service. 
# Because the webhook runs as the user running the Flask app, it typically 
# doesn't have permissions to run `sudo systemctl restart`. 
# To fix this, we restart a user-level systemd service or use sudoers.

echo "Restarting service..."
# If using a system-level service, you will need to allow passwordless sudo for this specific command in visudo:
# saif ALL=(ALL) NOPASSWD: /bin/systemctl restart friendshiplamp.service
sudo systemctl restart friendshiplamp.service

echo "Deployment finished successfully."
