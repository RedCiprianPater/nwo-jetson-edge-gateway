#!/usr/bin/env python3
"""
NWO Jetson Edge Gateway
Main entry point for hybrid edge-cloud robot control.
"""

import os
import sys
import time
import json
import signal
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import numpy as np

# Import local modules
from servo_controller import ServoController
from model_cache import ModelCache
from cloud_proxy import CloudProxy
from inference_router import InferenceRouter

# Configuration
CONFIG = {
    'servo_rate': int(os.getenv('EDGE_SERVO_RATE', 1000)),
    'cloud_sync_hz': int(os.getenv('EDGE_CLOUD_SYNC_HZ', 10)),
    'model_cache_mb': int(os.getenv('EDGE_MODEL_CACHE_MB', 2048)),
    'api_key': os.getenv('NWO_API_KEY'),
    'agent_id': os.getenv('NWO_AGENT_ID', 'g1_001'),
    'cloud_url': os.getenv('NWO_CLOUD_URL', 'https://nwo.capital/webapp'),
    'tensorrt_fp16': os.getenv('TENSORRT_FP16', 'true').lower() == 'true'
}

# Flask app
app = Flask(__name__)

class EdgeGateway:
    """Main edge gateway controller."""
    
    def __init__(self):
        self.running = False
        self.servo_controller = None
        self.model_cache = None
        self.cloud_proxy = None
        self.inference_router = None
        self.telemetry_buffer = []
        self.stats = {
            'servo_cycles': 0,
            'cloud_requests': 0,
            'local_inferences': 0,
            'start_time': time.time()
        }
        
    def initialize(self):
        """Initialize all components."""
        print("[EdgeGateway] Initializing NWO Jetson Edge Gateway...")
        print(f"[EdgeGateway] Agent ID: {CONFIG['agent_id']}")
        print(f"[EdgeGateway] Servo Rate: {CONFIG['servo_rate']} Hz")
        print(f"[EdgeGateway] Cloud Sync: {CONFIG['cloud_sync_hz']} Hz")
        
        # Initialize model cache
        print("[EdgeGateway] Initializing TensorRT model cache...")
        self.model_cache = ModelCache(
            max_size_mb=CONFIG['model_cache_mb'],
            fp16=CONFIG['tensorrt_fp16']
        )
        
        # Initialize cloud proxy
        print("[EdgeGateway] Initializing cloud proxy...")
        self.cloud_proxy = CloudProxy(
            api_key=CONFIG['api_key'],
            cloud_url=CONFIG['cloud_url'],
            agent_id=CONFIG['agent_id']
        )
        
        # Initialize inference router
        print("[EdgeGateway] Initializing inference router...")
        self.inference_router = InferenceRouter(
            model_cache=self.model_cache,
            cloud_proxy=self.cloud_proxy
        )
        
        # Initialize servo controller
        print("[EdgeGateway] Initializing servo controller...")
        self.servo_controller = ServoController(
            rate_hz=CONFIG['servo_rate'],
            inference_router=self.inference_router
        )
        
        print("[EdgeGateway] Initialization complete!")
        return True
        
    def start(self):
        """Start the edge gateway."""
        self.running = True
        
        # Start servo control thread
        self.servo_thread = threading.Thread(target=self._servo_loop)
        self.servo_thread.daemon = True
        self.servo_thread.start()
        
        # Start cloud sync thread
        self.cloud_thread = threading.Thread(target=self._cloud_sync_loop)
        self.cloud_thread.daemon = True
        self.cloud_thread.start()
        
        # Start telemetry thread
        self.telemetry_thread = threading.Thread(target=self._telemetry_loop)
        self.telemetry_thread.daemon = True
        self.telemetry_thread.start()
        
        print("[EdgeGateway] All threads started")
        
    def stop(self):
        """Stop the edge gateway."""
        print("[EdgeGateway] Stopping...")
        self.running = False
        
        if self.servo_thread:
            self.servo_thread.join(timeout=1.0)
        if self.cloud_thread:
            self.cloud_thread.join(timeout=1.0)
        if self.telemetry_thread:
            self.telemetry_thread.join(timeout=1.0)
            
        print("[EdgeGateway] Stopped")
        
    def _servo_loop(self):
        """High-frequency servo control loop (1kHz)."""
        period = 1.0 / CONFIG['servo_rate']
        next_time = time.time()
        
        while self.running:
            try:
                # Run servo control
                self.servo_controller.step()
                self.stats['servo_cycles'] += 1
                
                # Maintain precise timing
                next_time += period
                sleep_time = next_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"[ServoLoop] Error: {e}")
                
    def _cloud_sync_loop(self):
        """Low-frequency cloud synchronization (10Hz)."""
        period = 1.0 / CONFIG['cloud_sync_hz']
        
        while self.running:
            try:
                # Sync with cloud
                self.cloud_proxy.sync()
                self.stats['cloud_requests'] += 1
                
                # Update model cache from cloud
                self.model_cache.check_updates()
                
                time.sleep(period)
                
            except Exception as e:
                print(f"[CloudSync] Error: {e}")
                time.sleep(period)
                
    def _telemetry_loop(self):
        """Telemetry batching and upload."""
        batch_size = 100
        batch_interval = 1.0  # 1 second
        
        while self.running:
            try:
                # Collect telemetry from servo controller
                telemetry = self.servo_controller.get_telemetry()
                if telemetry:
                    self.telemetry_buffer.append(telemetry)
                    
                # Batch upload when buffer is full or interval elapsed
                if len(self.telemetry_buffer) >= batch_size:
                    self._upload_telemetry()
                    
                time.sleep(0.01)  # 100Hz collection
                
            except Exception as e:
                print(f"[Telemetry] Error: {e}")
                
    def _upload_telemetry(self):
        """Upload batched telemetry to cloud."""
        if not self.telemetry_buffer:
            return
            
        try:
            batch = self.telemetry_buffer[:100]  # Max 100 samples
            self.cloud_proxy.upload_telemetry(batch)
            self.telemetry_buffer = self.telemetry_buffer[100:]
            
        except Exception as e:
            print(f"[Telemetry] Upload error: {e}")
            
    def get_health(self):
        """Get gateway health status."""
        uptime = time.time() - self.stats['start_time']
        
        return {
            'status': 'healthy' if self.running else 'stopped',
            'agent_id': CONFIG['agent_id'],
            'uptime_seconds': uptime,
            'servo_rate': CONFIG['servo_rate'],
            'servo_cycles': self.stats['servo_cycles'],
            'cloud_requests': self.stats['cloud_requests'],
            'local_inferences': self.stats['local_inferences'],
            'model_cache': self.model_cache.get_status() if self.model_cache else None,
            'timestamp': datetime.utcnow().isoformat()
        }

# Global gateway instance
gateway = EdgeGateway()

# Flask routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify(gateway.get_health())

@app.route('/models', methods=['GET'])
def list_models():
    """List cached models."""
    if gateway.model_cache:
        return jsonify(gateway.model_cache.list_models())
    return jsonify({'error': 'Model cache not initialized'}), 503

@app.route('/models/preload', methods=['POST'])
def preload_model():
    """Preload a model into cache."""
    data = request.json
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({'error': 'model_id required'}), 400
        
    if gateway.model_cache:
        success = gateway.model_cache.preload(model_id)
        return jsonify({'success': success, 'model_id': model_id})
    
    return jsonify({'error': 'Model cache not initialized'}), 503

@app.route('/control/servo', methods=['POST'])
def servo_control():
    """Direct servo control endpoint."""
    data = request.json
    
    if gateway.servo_controller:
        result = gateway.servo_controller.set_targets(data)
        return jsonify(result)
    
    return jsonify({'error': 'Servo controller not initialized'}), 503

@app.route('/inference/local', methods=['POST'])
def local_inference():
    """Run inference locally on edge."""
    data = request.json
    gateway.stats['local_inferences'] += 1
    
    if gateway.inference_router:
        result = gateway.inference_router.inference_local(data)
        return jsonify(result)
    
    return jsonify({'error': 'Inference router not initialized'}), 503

@app.route('/inference/cloud', methods=['POST'])
def cloud_inference():
    """Proxy inference to cloud."""
    data = request.json
    gateway.stats['cloud_requests'] += 1
    
    if gateway.cloud_proxy:
        result = gateway.cloud_proxy.inference(data)
        return jsonify(result)
    
    return jsonify({'error': 'Cloud proxy not initialized'}), 503

@app.route('/telemetry/batch', methods=['POST'])
def queue_telemetry():
    """Queue telemetry for batch upload."""
    data = request.json
    gateway.telemetry_buffer.append(data)
    return jsonify({'queued': True, 'buffer_size': len(gateway.telemetry_buffer)})

@app.route('/test/servo', methods=['POST'])
def test_servo():
    """Test servo control loop."""
    if gateway.servo_controller:
        test_result = gateway.servo_controller.test()
        return jsonify(test_result)
    return jsonify({'error': 'Servo controller not initialized'}), 503

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print("\n[EdgeGateway] Shutdown signal received")
    gateway.stop()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize gateway
    if not gateway.initialize():
        print("[EdgeGateway] Initialization failed")
        sys.exit(1)
    
    # Start gateway
    gateway.start()
    
    # Start Flask server
    print("[EdgeGateway] Starting HTTP server on port 8080...")
    app.run(host='0.0.0.0', port=8080, threaded=True)
