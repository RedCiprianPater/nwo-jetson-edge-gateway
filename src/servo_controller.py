#!/usr/bin/env python3
"""
Servo Controller - High-frequency real-time control loop
Runs at 1kHz for tight servo control on Jetson Orin.
"""

import time
import numpy as np
from collections import deque

class ServoController:
    """Real-time servo controller with 1kHz update rate."""
    
    def __init__(self, rate_hz=1000, inference_router=None):
        self.rate_hz = rate_hz
        self.period = 1.0 / rate_hz
        self.inference_router = inference_router
        
        # Joint state
        self.num_joints = 23  # Unitree G1
        self.joint_positions = np.zeros(self.num_joints)
        self.joint_velocities = np.zeros(self.num_joints)
        self.joint_targets = np.zeros(self.num_joints)
        self.joint_torques = np.zeros(self.num_joints)
        
        # Control gains (PD controller)
        self.kp = np.ones(self.num_joints) * 100.0
        self.kd = np.ones(self.num_joints) * 10.0
        
        # Safety limits
        self.max_torque = 80.0  # Nm
        self.max_velocity = 10.0  # rad/s
        
        # Telemetry buffer
        self.telemetry_buffer = deque(maxlen=1000)
        
        # Statistics
        self.cycle_count = 0
        self.missed_deadlines = 0
        self.last_cycle_time = time.time()
        
    def step(self):
        """Execute one control cycle (called at 1kHz)."""
        cycle_start = time.time()
        
        # 1. Read current joint state (simulated for now)
        self._read_joint_state()
        
        # 2. Get control targets from inference router
        if self.inference_router:
            targets = self.inference_router.get_servo_targets(self.joint_positions)
            if targets is not None:
                self.joint_targets = targets
        
        # 3. Compute PD control
        position_error = self.joint_targets - self.joint_positions
        velocity_error = -self.joint_velocities  # Target velocity is 0
        
        torque_command = (
            self.kp * position_error +
            self.kd * velocity_error
        )
        
        # 4. Apply safety limits
        torque_command = np.clip(torque_command, -self.max_torque, self.max_torque)
        self.joint_torques = torque_command
        
        # 5. Send commands to hardware (simulated)
        self._send_torque_commands(torque_command)
        
        # 6. Record telemetry (every 10th cycle = 100Hz)
        if self.cycle_count % 10 == 0:
            self._record_telemetry()
        
        # 7. Check timing
        cycle_end = time.time()
        cycle_time = cycle_end - cycle_start
        deadline_miss = cycle_time > self.period
        
        if deadline_miss:
            self.missed_deadlines += 1
        
        self.cycle_count += 1
        self.last_cycle_time = cycle_end
        
    def _read_joint_state(self):
        """Read current joint positions and velocities."""
        # TODO: Interface with actual robot hardware
        # For now, simulate with simple integration
        dt = self.period
        self.joint_velocities += (self.joint_torques / 10.0) * dt  # Simple dynamics
        self.joint_positions += self.joint_velocities * dt
        
    def _send_torque_commands(self, torques):
        """Send torque commands to robot hardware."""
        # TODO: Interface with actual robot hardware
        pass
        
    def _record_telemetry(self):
        """Record telemetry data."""
        telemetry = {
            'timestamp': time.time(),
            'positions': self.joint_positions.copy(),
            'velocities': self.joint_velocities.copy(),
            'targets': self.joint_targets.copy(),
            'torques': self.joint_torques.copy()
        }
        self.telemetry_buffer.append(telemetry)
        
    def set_targets(self, data):
        """Set joint targets from external command."""
        if 'joint_targets' in data:
            targets = np.array(data['joint_targets'])
            if len(targets) == self.num_joints:
                self.joint_targets = targets
                return {'success': True, 'targets_set': True}
            else:
                return {'error': f'Expected {self.num_joints} joints, got {len(targets)}'}
        return {'error': 'joint_targets not provided'}
        
    def get_telemetry(self):
        """Get latest telemetry data."""
        if self.telemetry_buffer:
            return self.telemetry_buffer[-1]
        return None
        
    def get_status(self):
        """Get controller status."""
        return {
            'rate_hz': self.rate_hz,
            'cycle_count': self.cycle_count,
            'missed_deadlines': self.missed_deadlines,
            'miss_rate': self.missed_deadlines / max(self.cycle_count, 1),
            'buffer_size': len(self.telemetry_buffer)
        }
        
    def test(self):
        """Run servo test routine."""
        print("[ServoController] Running test routine...")
        
        # Test 1: Position hold
        initial_positions = self.joint_positions.copy()
        self.joint_targets = initial_positions
        
        time.sleep(0.1)  # Let controller run
        
        # Test 2: Small movement
        test_target = initial_positions + 0.1
        self.joint_targets = test_target
        
        time.sleep(0.1)
        
        # Check results
        position_error = np.abs(self.joint_positions - test_target)
        max_error = np.max(position_error)
        
        return {
            'test': 'servo_basic',
            'max_position_error': float(max_error),
            'cycles_completed': self.cycle_count,
            'missed_deadlines': self.missed_deadlines,
            'passed': max_error < 0.5  # 0.5 rad tolerance
        }
