#!/usr/bin/env python3
"""
Test YOLO nano inference on Hailo AI Hat.
Requires: YOLO nano model in .hef format
"""

import sys
import time
import numpy as np
from pathlib import Path

try:
    from hailo_platform import (
        HEF, 
        Device, 
        VDevice, 
        HailoSchedulingAlgorithm,
        InferVStreams,
        InputVStreamParams,
        OutputVStreamParams,
        FormatType
    )
except ImportError:
    print("❌ Hailo API not found. Run test_hailo.py first.")
    sys.exit(1)


class HailoYOLO:
    """YOLO inference using Hailo accelerator."""
    
    def __init__(self, hef_path: str):
        """
        Initialize Hailo YOLO inference.
        
        Args:
            hef_path: Path to YOLO .hef model file
        """
        self.hef_path = Path(hef_path)
        if not self.hef_path.exists():
            raise FileNotFoundError(f"Model not found: {hef_path}")
        
        print(f"Loading model: {self.hef_path}")
        self.hef = HEF(str(self.hef_path))
        
        # Create device
        self.device = Device()
        
        # Configure network
        self.network_group = self._configure_network()
        self.input_vstreams, self.output_vstreams = self._create_vstreams()
        
        print("✅ Hailo YOLO initialized")
    
    def _configure_network(self):
        """Configure the neural network on Hailo."""
        network_groups = self.device.configure(self.hef)
        if len(network_groups) != 1:
            raise ValueError(f"Expected 1 network group, got {len(network_groups)}")
        return network_groups[0]
    
    def _create_vstreams(self):
        """Create input/output virtual streams."""
        # Get network parameters
        input_vstream_params = InputVStreamParams.make_from_network_group(
            self.network_group, 
            quantized=False,
            format_type=FormatType.FLOAT32
        )
        
        output_vstream_params = OutputVStreamParams.make_from_network_group(
            self.network_group,
            quantized=False,
            format_type=FormatType.FLOAT32
        )
        
        # Create streams
        input_vstreams = InferVStreams(self.network_group, input_vstream_params)
        output_vstreams = InferVStreams(self.network_group, output_vstream_params)
        
        return input_vstreams, output_vstreams
    
    def infer(self, image: np.ndarray) -> dict:
        """
        Run inference on image.
        
        Args:
            image: Input image (preprocessed to model input size)
            
        Returns:
            Dictionary with model outputs
        """
        # Prepare input
        input_data = {self.input_vstreams[0].name: image}
        
        # Run inference
        start = time.time()
        with InferVStreams(self.network_group, self.input_vstreams, self.output_vstreams) as infer_pipeline:
            output = infer_pipeline.infer(input_data)
        inference_time = time.time() - start
        
        # Add timing info
        output['inference_time_ms'] = inference_time * 1000
        
        return output
    
    def get_input_shape(self):
        """Get expected input shape."""
        return self.input_vstreams[0].shape
    
    def cleanup(self):
        """Release resources."""
        if hasattr(self, 'device'):
            self.device.release()
            print("✅ Hailo resources released")


def preprocess_image(image: np.ndarray, target_shape: tuple) -> np.ndarray:
    """
    Preprocess image for YOLO input.
    
    Args:
        image: Input image (H, W, C)
        target_shape: Target shape (H, W, C)
        
    Returns:
        Preprocessed image
    """
    import cv2
    
    h, w, c = target_shape
    
    # Resize
    resized = cv2.resize(image, (w, h))
    
    # Normalize to [0, 1]
    normalized = resized.astype(np.float32) / 255.0
    
    # Add batch dimension if needed
    if len(normalized.shape) == 3:
        normalized = np.expand_dims(normalized, axis=0)
    
    return normalized


def test_inference_speed(model: HailoYOLO, num_iterations: int = 100):
    """Benchmark inference speed."""
    print(f"\n🏃 Running inference benchmark ({num_iterations} iterations)...")
    
    # Get input shape
    input_shape = model.get_input_shape()
    print(f"Input shape: {input_shape}")
    
    # Create dummy input
    dummy_input = np.random.rand(*input_shape).astype(np.float32)
    
    # Warmup
    print("Warming up...")
    for _ in range(10):
        model.infer(dummy_input)
    
    # Benchmark
    print("Benchmarking...")
    times = []
    for i in range(num_iterations):
        start = time.time()
        result = model.infer(dummy_input)
        elapsed = time.time() - start
        times.append(elapsed)
        
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{num_iterations}")
    
    # Statistics
    times_ms = [t * 1000 for t in times]
    avg_time = np.mean(times_ms)
    std_time = np.std(times_ms)
    fps = 1000 / avg_time
    
    print("\n" + "=" * 60)
    print("📊 Benchmark Results:")
    print("=" * 60)
    print(f"Average inference time: {avg_time:.2f} ms (±{std_time:.2f} ms)")
    print(f"Min: {min(times_ms):.2f} ms | Max: {max(times_ms):.2f} ms")
    print(f"Throughput: {fps:.1f} FPS")
    print("=" * 60)


def main():
    """Test YOLO on Hailo."""
    print("=" * 60)
    print("🚀 YOLO nano + Hailo AI Hat Test")
    print("=" * 60)
    
    # Model path - auto-detect available models
    model_dir = Path("models")
    possible_models = [
        "yolov8n.hef",
        "yolov5n.hef",
        "yolov8s.hef",
    ]
    
    model_path = None
    for model_name in possible_models:
        candidate = model_dir / model_name
        if candidate.exists():
            model_path = str(candidate)
            print(f"✅ Found model: {model_name}")
            break
    
    if model_path is None:
        model_path = "models/yolov8n.hef"  # Default fallback
    
    if not Path(model_path).exists():
        print(f"\n❌ Model not found: {model_path}")
        print("\nYou need to:")
        print("1. Get YOLO nano in Hailo .hef format")
        print("2. Place it in: hailo_poc/models/")
        print("\nOptions:")
        print("  - Download from Hailo Model Zoo")
        print("  - Convert using Hailo Dataflow Compiler")
        return 1
    
    try:
        # Initialize model
        model = HailoYOLO(model_path)
        
        # Run benchmark
        test_inference_speed(model)
        
        print("\n✅ YOLO on Hailo is working!")
        
        # Cleanup
        model.cleanup()
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
