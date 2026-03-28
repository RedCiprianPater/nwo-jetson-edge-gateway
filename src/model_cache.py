#!/usr/bin/env python3
"""
Model Cache - TensorRT-optimized model caching for Jetson Orin
"""

import os
import json
import time
import hashlib
from pathlib import Path
import numpy as np

class ModelCache:
    """LRU cache for TensorRT-optimized models."""
    
    def __init__(self, max_size_mb=2048, fp16=True):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.fp16 = fp16
        self.cache_dir = Path('/app/models/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache state
        self.cached_models = {}  # model_id -> model_data
        self.model_access_times = {}  # model_id -> last_access_time
        self.current_size_bytes = 0
        
        # Load existing cache
        self._load_cache_index()
        
    def _load_cache_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dir / 'cache_index.json'
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index = json.load(f)
                    self.current_size_bytes = index.get('size_bytes', 0)
                    print(f"[ModelCache] Loaded cache index: {len(index.get('models', {}))} models")
            except Exception as e:
                print(f"[ModelCache] Error loading cache index: {e}")
                
    def _save_cache_index(self):
        """Save cache index to disk."""
        index_file = self.cache_dir / 'cache_index.json'
        try:
            index = {
                'models': {k: {'size': 0} for k in self.cached_models.keys()},
                'size_bytes': self.current_size_bytes,
                'updated': time.time()
            }
            with open(index_file, 'w') as f:
                json.dump(index, f)
        except Exception as e:
            print(f"[ModelCache] Error saving cache index: {e}")
            
    def get(self, model_id):
        """Get model from cache."""
        if model_id in self.cached_models:
            self.model_access_times[model_id] = time.time()
            return self.cached_models[model_id]
        return None
        
    def put(self, model_id, model_data, model_size_bytes):
        """Add model to cache."""
        # Check if we need to evict
        while self.current_size_bytes + model_size_bytes > self.max_size_bytes:
            self._evict_oldest()
            
        # Add to cache
        self.cached_models[model_id] = model_data
        self.model_access_times[model_id] = time.time()
        self.current_size_bytes += model_size_bytes
        
        self._save_cache_index()
        
    def _evict_oldest(self):
        """Evict least recently used model."""
        if not self.model_access_times:
            return
            
        oldest_id = min(self.model_access_times, key=self.model_access_times.get)
        
        if oldest_id in self.cached_models:
            # TODO: Actually free memory
            del self.cached_models[oldest_id]
            del self.model_access_times[oldest_id]
            print(f"[ModelCache] Evicted model: {oldest_id}")
            
    def preload(self, model_id):
        """Preload model from cloud into cache."""
        print(f"[ModelCache] Preloading model: {model_id}")
        
        # Check if already cached
        if model_id in self.cached_models:
            print(f"[ModelCache] Model {model_id} already cached")
            return True
            
        # TODO: Download and optimize model
        # For now, simulate
        dummy_model = {'id': model_id, 'optimized': True}
        self.put(model_id, dummy_model, 100 * 1024 * 1024)  # 100MB
        
        print(f"[ModelCache] Preloaded {model_id}")
        return True
        
    def check_updates(self):
        """Check for model updates from cloud."""
        # TODO: Query cloud for model updates
        pass
        
    def list_models(self):
        """List cached models."""
        return {
            'cached_models': list(self.cached_models.keys()),
            'cache_size_mb': self.current_size_bytes / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'utilization': self.current_size_bytes / self.max_size_bytes
        }
        
    def get_status(self):
        """Get cache status."""
        return {
            'models_cached': len(self.cached_models),
            'size_mb': self.current_size_bytes / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'hit_rate': 0.95  # TODO: Track actual hit rate
        }
