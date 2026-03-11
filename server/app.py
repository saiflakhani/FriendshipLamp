import os
import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Dictionary to hold states of all registered lamps
# Key: lamp_id (e.g., MAC address), Value: state dict
lamps = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/lamps", methods=["GET"])
def get_lamps():
    # Only return lamps that have been seen in the last hour (3600 seconds)
    current_time = time.time()
    active_lamps = {
        lamp_id: data 
        for lamp_id, data in lamps.items() 
        if (current_time - data.get("last_seen", 0)) < 3600
    }
    return jsonify({"lamps": active_lamps})

import subprocess
import hmac
import hashlib

@app.route("/api/github-webhook", methods=["POST"])
def github_webhook():
    # Optional: You can verify the GitHub webhook secret here
    # signature = request.headers.get('X-Hub-Signature-256')
    
    # Just a simple git pull for now
    try:
        # Run git pull
        result = subprocess.run(
            ["git", "pull", "origin", "master"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return jsonify({"status": "success", "output": result.stdout}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e), "output": e.stderr}), 500

@app.route("/api/send", methods=["POST"])
def send_message():
    data = request.json
    lamp_id = data.get("id")
    if lamp_id in lamps:
        lamps[lamp_id]["active"] = True
        return jsonify({"status": "success", "active": True})
    return jsonify({"status": "error", "message": "Lamp not found"}), 404

@app.route("/api/lamp/status", methods=["GET"])
def lamp_status():
    lamp_id = request.args.get("id")
    lamp_name = request.args.get("name")
    
    if not lamp_id:
        return jsonify({"error": "Missing id parameter"}), 400
        
    if not lamp_name:
        lamp_name = f"Lamp {lamp_id[-4:]}"
        
    current_time = time.time()
        
    # Register or update last seen
    if lamp_id not in lamps:
        lamps[lamp_id] = {
            "name": lamp_name, 
            "active": False,
            "last_seen": current_time
        }
    else:
        lamps[lamp_id]["last_seen"] = current_time
        lamps[lamp_id]["name"] = lamp_name
        
    return jsonify(lamps[lamp_id])

@app.route("/api/lamp/ack", methods=["POST"])
def lamp_ack():
    lamp_id = request.args.get("id")
    if lamp_id in lamps:
        lamps[lamp_id]["active"] = False
        return jsonify({"status": "acknowledged"})
    return jsonify({"status": "error", "message": "Lamp not found"}), 404

if __name__ == "__main__":
    # Use 0.0.0.0 so we can access it from the lamp on the local network
    app.run(host="0.0.0.0", port=5000, debug=True)
