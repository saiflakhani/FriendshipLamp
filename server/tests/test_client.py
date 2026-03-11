import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://friendshiplamp.lakhanimediaserver.xyz"

def make_request(method, endpoint, params=None, json_data=None):
    url = BASE_URL + endpoint
    
    if params:
        url += "?" + urllib.parse.urlencode(params)
        
    req = urllib.request.Request(url, method=method)
    
    if json_data:
        data = json.dumps(json_data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, data=data) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode())
            except:
                msg = e.read().decode()
            return e.code, msg
        except Exception as e:
            return None, str(e)
    else:
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode())
            except:
                msg = e.read().decode()
            return e.code, msg
        except Exception as e:
            return None, str(e)

def run_active_client(lamp_id="test_mac_1234"):
    print(f"--- Starting Active Lamp Simulation for {lamp_id} ---")
    
    # Optional header to bypass aggressive Cloudflare WAF block rules
    headers = {
        "User-Agent": "FriendshipLampClient/1.0"
    }

    def _request(method, endpoint, params=None):
        url = BASE_URL + endpoint
        if params:
            url += "?" + urllib.parse.urlencode(params)
            
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode())
            except:
                msg = e.read().decode()
            return e.code, msg
        except Exception as e:
            return None, str(e)

    try:
        while True:
            # Poll status (this also registers the lamp if it doesn't exist)
            print(f"Checking server for messages...")
            status, response = _request("GET", "/api/lamp/status", params={"id": lamp_id})
            
            if status == 200:
                is_active = response.get("active", False)
                if is_active:
                    print("\n✨✨✨ FRIEND IS THINKING OF YOU! ✨✨✨")
                    print("Blinking LED (Simulation)...\n")
                    
                    # Wait 2 seconds to simulate blinking, then Ack it
                    time.sleep(2)
                    
                    print("Sending acknowledgment to clear the glow...")
                    ack_status, ack_response = _request("POST", "/api/lamp/ack", params={"id": lamp_id})
                    if ack_status == 200:
                        print("Message acknowledged successfully.")
                    else:
                        print(f"Failed to ACK: {ack_status} {ack_response}")
                else:
                    print("No new message. Lamp is inactive.")
            else:
                print(f"Error polling server: Status Code {status} - {response}")
                
            # Sleep before polling again
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\nStopping active client simulation.")

if __name__ == "__main__":
    print(f"Connecting to server at {BASE_URL}...")
    run_active_client()
