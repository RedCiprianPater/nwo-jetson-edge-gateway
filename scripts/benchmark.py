#!/usr/bin/env python3
"""
Benchmark script for NWO Jetson Edge Gateway
Tests servo loop performance and inference latency
"""

import time
import requests
import statistics

def benchmark_servo_loop(duration_seconds=10):
    """Benchmark servo control loop performance."""
    print(f"Benchmarking servo loop for {duration_seconds}s...")
    
    latencies = []
    start = time.time()
    
    while time.time() - start < duration_seconds:
        loop_start = time.time()
        
        # Send servo command
        try:
            response = requests.post(
                'http://localhost:8080/control/servo',
                json={'joint_targets': [0.0] * 23},
                timeout=0.01
            )
        except:
            pass
        
        loop_end = time.time()
        latencies.append((loop_end - loop_start) * 1000)  # ms
        
        time.sleep(0.001)  # 1kHz target
    
    print(f"Servo Loop Results:")
    print(f"  Mean latency: {statistics.mean(latencies):.2f} ms")
    print(f"  Max latency: {max(latencies):.2f} ms")
    print(f"  Min latency: {min(latencies):.2f} ms")
    print(f"  P99 latency: {sorted(latencies)[int(len(latencies)*0.99)]:.2f} ms")

def benchmark_inference():
    """Benchmark local vs cloud inference."""
    print("\nBenchmarking inference...")
    
    # Local inference
    start = time.time()
    try:
        response = requests.post(
            'http://localhost:8080/inference/local',
            json={'model_id': 'xiaomi-robotics-0'},
            timeout=5.0
        )
        local_latency = (time.time() - start) * 1000
        print(f"Local inference: {local_latency:.2f} ms")
    except Exception as e:
        print(f"Local inference failed: {e}")
    
    # Cloud inference
    start = time.time()
    try:
        response = requests.post(
            'http://localhost:8080/inference/cloud',
            json={'model_id': 'gr00t-n1.7', 'instruction': 'test'},
            timeout=10.0
        )
        cloud_latency = (time.time() - start) * 1000
        print(f"Cloud inference: {cloud_latency:.2f} ms")
    except Exception as e:
        print(f"Cloud inference failed: {e}")

def main():
    print("NWO Jetson Edge Gateway Benchmark")
    print("=" * 40)
    
    # Check if gateway is running
    try:
        response = requests.get('http://localhost:8080/health', timeout=2.0)
        print(f"Gateway status: {response.json()['status']}")
    except:
        print("Error: Gateway not running on localhost:8080")
        return
    
    benchmark_servo_loop(duration_seconds=10)
    benchmark_inference()
    
    print("\nBenchmark complete!")

if __name__ == '__main__':
    main()
