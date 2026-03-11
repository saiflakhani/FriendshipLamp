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
    return jsonify({"lamps": lamps})

import subprocess
import hmac
import hashlib

@app.route("/api/github-webhook", methods=["POST"])
def github_webhook():
    # Optional: You can verify the GitHub webhook secret here
    # signature = request.headers.get('X-Hub-Signature-256')
    
    # Run the deployment script to pull and restart the service
    try:
        result = subprocess.run(
            ["/home/saif/Code/FriendshipLamp/deploy.sh"], 
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
    if not lamp_id:
        return jsonify({"error": "Missing id parameter"}), 400
        
    # Register or update last seen
    if lamp_id not in lamps:
        lamps[lamp_id] = {
            "name": f"Lamp {lamp_id[-4:]}", 
            "active": False,
            "last_seen": time.time()
        }
    else:
        lamps[lamp_id]["last_seen"] = time.time()
        
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
