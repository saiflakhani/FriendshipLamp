import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:5000"

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

def test_server():
    lamp_id = "test_mac_1234"
    
    print(f"--- Testing Lamp Status (Registration) for {lamp_id} ---")
    status, response = make_request("GET", "/api/lamp/status", params={"id": lamp_id})
    print(f"Status: {status}, Response: {response}\n")
    
    print("--- Testing Get All Lamps ---")
    status, response = make_request("GET", "/api/lamps")
    print(f"Status: {status}, Response: {response}\n")
    
    print(f"--- Testing Send Message to {lamp_id} ---")
    status, response = make_request("POST", "/api/send", json_data={"id": lamp_id})
    print(f"Status: {status}, Response: {response}\n")
    
    print(f"--- Testing Lamp Status (Active Check) for {lamp_id} ---")
    status, response = make_request("GET", "/api/lamp/status", params={"id": lamp_id})
    print(f"Status: {status}, Response: {response}\n")
    
    print(f"--- Testing Lamp Ack for {lamp_id} ---")
    status, response = make_request("POST", "/api/lamp/ack", params={"id": lamp_id})
    print(f"Status: {status}, Response: {response}\n")
    
    print(f"--- Testing Lamp Status (Post-Ack Check) for {lamp_id} ---")
    status, response = make_request("GET", "/api/lamp/status", params={"id": lamp_id})
    print(f"Status: {status}, Response: {response}\n")

if __name__ == "__main__":
    print(f"Connecting to server at {BASE_URL}...")
    test_server()
