import pytest
import json
import time

# We need to import app from the parent directory's server package
# A better way is to rely on pytest discovering the module or appending to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, lamps

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def clear_lamps():
    # Clear the lamps dictionary before each test
    lamps.clear()

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200

def test_api_lamps_empty(client):
    rv = client.get('/api/lamps')
    assert rv.status_code == 200
    assert rv.get_json() == {"lamps": {}}

def test_lamp_status_registration(client):
    mac = "test_mac_1111"
    rv = client.get(f'/api/lamp/status?id={mac}')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["name"] == "Lamp 1111"
    assert data["active"] is False
    assert "last_seen" in data
    
    # Check it was added to the state
    assert mac in lamps

def test_send_message_lamp_not_found(client):
    rv = client.post('/api/send', json={"id": "unknown_mac"})
    assert rv.status_code == 404
    assert rv.get_json() == {"status": "error", "message": "Lamp not found"}

def test_send_message_success(client):
    mac = "test_mac_2222"
    
    # Register first
    client.get(f'/api/lamp/status?id={mac}')
    
    # Send message
    rv = client.post('/api/send', json={"id": mac})
    assert rv.status_code == 200
    assert rv.get_json() == {"status": "success", "active": True}
    
    # Check status changed
    rv = client.get(f'/api/lamp/status?id={mac}')
    assert rv.get_json()["active"] is True

def test_lamp_ack_not_found(client):
    rv = client.post('/api/lamp/ack?id=unknown_mac')
    assert rv.status_code == 404

def test_lamp_ack_success(client):
    mac = "test_mac_3333"
    
    # Register
    client.get(f'/api/lamp/status?id={mac}')
    # Send message to activate
    client.post('/api/send', json={"id": mac})
    
    # Ack to deactivate
    rv = client.post(f'/api/lamp/ack?id={mac}')
    assert rv.status_code == 200
    assert rv.get_json() == {"status": "acknowledged"}
    
    # Verify deactivated
    rv = client.get(f'/api/lamp/status?id={mac}')
    assert rv.get_json()["active"] is False
