#!/usr/bin/env python3
"""
Inference Router - Routes inference between edge and cloud
"""

import numpy as np

class InferenceRouter:
    """Routes inference requests between edge and cloud based on requirements."""
    
    def __init__(self, model_cache, cloud_proxy):
        self.model_cache = model_cache
        self.cloud_proxy = cloud_proxy
        
        # Routing rules
        self.edge_models = ['xiaomi-robotics-0', 'pi05']  # Cached locally
        self.servo_model = 'xiaomi-robotics-0'
        
        # Current servo targets
        self.current_targets = None
        
    def inference_local(self, data):
        """Run inference on edge."""
        model_id = data.get('model_id', self.servo_model)
        
        # Check if model is cached
        model = self.model_cache.get(model_id)
        if model is None:
            # Try to preload
            if self.model_cache.preload(model_id):
                model = self.model_cache.get(model_id)
            else:
                return {'error': f'Model {model_id} not available locally', 'fallback': 'cloud'}
        
        # TODO: Run actual inference
        # For now, return dummy result
        return {
            'model_id': model_id,
            'inference_location': 'edge',
            'latency_ms': 1.0,
            'output': {'action': 'dummy_action'}
        }
        
    def inference_cloud(self, data):
        """Route inference to cloud."""
        return self.cloud_proxy.inference(data)
        
    def route(self, data):
        """Intelligently route inference request."""
        model_id = data.get('model_id')
        priority = data.get('priority', 'normal')
        
        # High priority or specific models -> cloud
        if priority == 'high' or model_id in ['gr00t-n1.7', 'gr00t-n2']:
            return self.inference_cloud(data)
            
        # Cached models -> edge
        if model_id in self.edge_models:
            return self.inference_local(data)
            
        # Default: try edge first, fallback to cloud
        edge_result = self.inference_local(data)
        if 'error' not in edge_result:
            return edge_result
            
        return self.inference_cloud(data)
        
    def get_servo_targets(self, current_positions):
        """Get servo targets from local model (1kHz loop)."""
        # This runs at 1kHz, must be fast
        
        # Check if we have cached model
        model = self.model_cache.get(self.servo_model)
        if model is None:
            return None
            
        # TODO: Run actual model inference
        # For now, return simple PD-like targets
        if self.current_targets is None:
            self.current_targets = current_positions.copy()
            
        return self.current_targets
        
    def set_servo_targets(self, targets):
        """Set targets from higher-level controller."""
        self.current_targets = np.array(targets)
