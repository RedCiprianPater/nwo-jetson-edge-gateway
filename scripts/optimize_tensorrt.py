#!/usr/bin/env python3
"""
Convert models to TensorRT for Jetson Orin optimization
"""

import argparse
import tensorrt as trt
import onnx
import torch

def convert_to_tensorrt(model_path, output_path, fp16=True):
    """Convert ONNX model to TensorRT engine."""
    
    logger = trt.Logger(trt.Logger.INFO)
    builder = trt.Builder(logger)
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    parser = trt.OnnxParser(network, logger)
    
    # Parse ONNX
    with open(model_path, 'rb') as f:
        if not parser.parse(f.read()):
            for error in range(parser.num_errors):
                print(parser.get_error(error))
            return False
    
    # Build config
    config = builder.create_builder_config()
    config.max_workspace_size = 2 * 1024 * 1024 * 1024  # 2GB
    
    if fp16:
        config.set_flag(trt.BuilderFlag.FP16)
        print("Using FP16 precision")
    
    # Build engine
    print(f"Building TensorRT engine...")
    engine = builder.build_engine(network, config)
    
    if engine is None:
        print("Failed to build engine")
        return False
    
    # Save engine
    with open(output_path, 'wb') as f:
        f.write(engine.serialize())
    
    print(f"Saved TensorRT engine to {output_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Optimize models for Jetson')
    parser.add_argument('--model', required=True, help='Model ID to optimize')
    parser.add_argument('--output', help='Output path')
    parser.add_argument('--fp16', action='store_true', default=True, help='Use FP16')
    
    args = parser.parse_args()
    
    model_path = f"models/{args.model}.onnx"
    output_path = args.output or f"models/cache/{args.model}.trt"
    
    convert_to_tensorrt(model_path, output_path, args.fp16)

if __name__ == '__main__':
    main()
