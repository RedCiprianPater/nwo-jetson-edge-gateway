#!/usr/bin/env python3
"""
Cloud Proxy - Handles cloud communication with batching and caching
"""

import requests
import json
import time
import threading
from queue import Queue

class CloudProxy:
    """Proxy for cloud API with request batching."""
    
    def __init__(self, api_key, cloud_url, agent_id):
        self.api_key = api_key
        self.cloud_url = cloud_url
        self.agent_id = agent_id
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })
        
        # Request queue
        self.request_queue = Queue()
        self.response_cache = {}
        
        # Statistics
        self.requests_sent = 0
        self.responses_received = 0
        self.errors = 0
        
    def inference(self, data):
        """Send inference request to cloud."""
        try:
            url = f"{self.cloud_url}/api-robot-v2.php"
            
            payload = {
                'agent_id': self.agent_id,
                **data
            }
            
            response = self.session.post(url, json=payload, timeout=5.0)
            response.raise_for_status()
            
            self.requests_sent += 1
            self.responses_received += 1
            
            return response.json()
            
        except requests.exceptions.Timeout:
            self.errors += 1
            return {'error': 'Cloud timeout', 'fallback': 'local'}
            
        except Exception as e:
            self.errors += 1
            return {'error': str(e), 'fallback': 'local'}
            
    def upload_telemetry(self, telemetry_batch):
        """Upload batched telemetry to cloud."""
        try:
            url = f"{self.cloud_url}/api-telemetry.php"
            
            payload = {
                'agent_id': self.agent_id,
                'batch': telemetry_batch
            }
            
            response = self.session.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"[CloudProxy] Telemetry upload error: {e}")
            return {'error': str(e)}
            
    def sync(self):
        """Sync with cloud (check for updates, configs)."""
        try:
            # Check for model updates
            url = f"{self.cloud_url}/api-model-sync.php"
            
            response = self.session.get(url, params={
                'agent_id': self.agent_id
            }, timeout=5.0)
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"[CloudProxy] Sync error: {e}")
            
        return None
        
    def get_status(self):
        """Get proxy status."""
        return {
            'requests_sent': self.requests_sent,
            'responses_received': self.responses_received,
            'errors': self.errors,
            'success_rate': self.responses_received / max(self.requests_sent, 1)
        }
