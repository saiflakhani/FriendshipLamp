# Friendship Lamp

A complete hardware and software stack for building a pair (or more!) of internet-connected Friendship Lamps.

When one person touches their lamp, or sends a command via the web interface, the other person's lamp will light up to let them know they are being thought of!

This repository contains both the **ESP32 Firmware** and the **Python/Flask Server API** required to run the lamps.

---

## 🏗️ Architecture

1. **Firmware:** The C++ code (`firmware/lamp/lamp.ino`) runs on an ESP32 microcontroller. The ESP32 wakes up from deep sleep on a configurable interval, uses RTC memory to accomplish an ultra-fast WiFi connection, and polls the server to check if it has any active messages. If it does, it blinks the built-in LED (or an external one) and acknowledges the message.
2. **Server:** The Python server (`server/app.py`) runs a lightweight Flask API that keeps track of registered lamps, their "active" (blinking) state, and when they were last seen by the network.

---

## 🚀 Server Setup

The server is built using Python 3 and Flask. It provides a REST API that the lamps use to check their status.

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/saiflakhani/FriendshipLamp.git
   cd FriendshipLamp
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt # Or install flask/gunicorn/pytest manually
   ```

3. **Run the server:**
   ```bash
   python server/app.py
   ```
   The server will run on `http://0.0.0.0:5000/`. Note your local IP address so you can configure the ESP32 to connect to it.

---

## 💡 Firmware Setup (ESP32)

The firmware is designed for the standard ESP32 Dev Module.

1. **Open the sketch:** Open `firmware/lamp/lamp.ino` in the Arduino IDE.
2. **Install Board Definitions:** Make sure you have the ESP32 boards package installed in your Arduino IDE Board Manager.
3. **Configure WiFi and Server:**
   Update the top of the file with your specific credentials:
   ```cpp
   const char* WIFI_SSID = "YOUR_WIFI_SSID";
   const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";
   
   // Replace with your flask server IP or Domain Name
   const char* SERVER_BASE_URL = "http://192.168.1.X:5000";
   ```
4. **Compile and Upload:** Select "ESP32 Dev Module" in your Arduino Tools menu, choose the correct COM port, and upload the sketch to the board. 

*Note: The built-in LED (GPIO 2) is used by default. Wiring an external LED to GPIO 2 and GND is highly recommended for a better effect.*

---

## 📡 API Endpoints

### `GET /api/lamps`
Returns a JSON dictionary of all registered lamps, their `active` state, and the `last_seen` timestamp.

### `GET /api/lamp/status?id=<mac_address>`
Called by the ESP32. Registers the lamp if it doesn't exist, updates the `last_seen` timestamp, and returns the current `active` state.

### `POST /api/send`
**Payload:** `{"id": "<mac_address>"}`
Sets the target lamp's `active` state to `True`. The next time the lamp wakes up and polls the server, it will detect this state and blink!

### `POST /api/lamp/ack?id=<mac_address>`
Called by the ESP32 after it successfully blinks. Sets the `active` state back to `False`.

### `POST /api/github-webhook`
A deployment endpoint that pulls the latest code from the `main` branch and triggers a server restart via `deploy.sh`. 

---

## 🌐 Production Deployment Guide

If you are running the server on a Linux VPS (like Ubuntu via DigitalOcean, Linode, AWS, etc.) and want it to run continuously and auto-update on push, follow these steps.

### 1. Map a Subdomain to a Port (Nginx Reverse Proxy)

Create an Nginx configuration file for your subdomain (e.g., `sudo nano /etc/nginx/sites-available/friendshiplamp`):

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable it and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/friendshiplamp /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### 2. Configure Systemd Service (Gunicorn)

Create a service file to run the server continuously in the background using Gunicorn:
```bash
sudo nano /etc/systemd/system/friendshiplamp.service
```

```ini
[Unit]
Description=Gunicorn instance to serve Friendship Lamp API
After=network.target

[Service]
User=your_linux_user
Group=www-data
WorkingDirectory=/path/to/FriendshipLamp
Environment="PATH=/path/to/FriendshipLamp/venv/bin"
ExecStart=/path/to/FriendshipLamp/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```
Enable and start it:
```bash
sudo systemctl daemon-reload
sudo systemctl start friendshiplamp
sudo systemctl enable friendshiplamp
```

### 3. Grant Webhook Restart Permissions

The `POST /api/github-webhook` endpoint runs the `deploy.sh` script, which attempts to restart the systemd service. To allow this without a password prompt, run `sudo visudo` and append:

```
your_linux_user ALL=(ALL) NOPASSWD: /bin/systemctl restart friendshiplamp.service
```

### 4. Configure the Webhook on GitHub

1. Go to **Settings > Webhooks > Add webhook** in your repository.
2. **Payload URL**: `http://api.yourdomain.com/api/github-webhook`
3. **Content type**: `application/json`
4. **Which events**: "Just the push event".
5. Save! Your server will now auto-deploy when you push to `main` (or `master`).
