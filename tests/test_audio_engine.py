"""Test script for AudioEngine - Stage 2 verification"""
import sys
sys.path.insert(0, '.')

from core.audio_engine import AudioEngine

def test_list_devices():
    engine = AudioEngine()
    devices = engine.list_devices()
    
    print("=== Audio Devices ===\n")
    print("INPUT DEVICES:")
    for dev in devices['input']:
        print(f"  [{dev['index']}] {dev['name']} (channels: {dev['max_input_channels']})")
    
    print("\nOUTPUT DEVICES:")
    for dev in devices['output']:
        print(f"  [{dev['index']}] {dev['name']} (channels: {dev['max_output_channels']})")
    
    print(f"\nTotal: {len(devices['input'])} input, {len(devices['output'])} output devices")
    return True

if __name__ == "__main__":
    try:
        test_list_devices()
        print("\n✓ AudioEngine.list_devices() works correctly")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
