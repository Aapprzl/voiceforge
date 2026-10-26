"""Test script for NoiseGate - Stage 3 verification"""
import sys
import numpy as np
sys.path.insert(0, '.')

from core.processor import NoiseGate, AudioProcessor


def test_noise_gate():
    print("=== Testing NoiseGate ===\n")
    
    sample_rate = 44100
    gate = NoiseGate(threshold_db=-40.0, attack_ms=1.0, release_ms=10.0, sample_rate=sample_rate)
    
    segment_duration = 0.5
    segment_samples = int(sample_rate * segment_duration)
    
    silence = np.zeros(segment_samples, dtype=np.float32)
    t = np.linspace(0, segment_duration, segment_samples, dtype=np.float32)
    sine = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    test_signal = np.concatenate([
        sine,       # signal first - gate starts open
        silence,    # silence - gate should close
        sine,       # signal - gate should open
        silence,    # silence - gate should close
    ])
    
    output = gate.process(test_signal)
    
    print(f"Test: signal, silence, signal, silence")
    print(f"Segments: 4 x {segment_duration}s, Total: {len(test_signal)/sample_rate:.2f}s")
    print(f"Gate params: threshold=-40dB, attack=1ms, release=10ms\n")
    
    def get_rms_db(signal):
        rms = np.sqrt(np.mean(signal**2))
        return 20 * np.log10(rms) if rms > 1e-10 else -np.inf
    
    labels = ["signal", "silence", "signal", "silence"]
    passed = 0
    
    for i, label in enumerate(labels):
        start = i * segment_samples
        end = (i + 1) * segment_samples
        in_rms = get_rms_db(test_signal[start:end])
        out_rms = get_rms_db(output[start:end])
        
        in_str = f"{in_rms:.1f} dB" if in_rms > -100 else "-inf dB"
        out_str = f"{out_rms:.1f} dB" if out_rms > -100 else "-inf dB"
        
        if label == "silence":
            status = "✓" if out_rms < -50 else "✗"
            passed += 1 if out_rms < -50 else 0
        else:
            status = "✓" if out_rms > -15 else "✗"
            passed += 1 if out_rms > -15 else 0
        
        print(f"  {label:8s}: input {in_str:>10s} -> output {out_str:>10s} {status}")
    
    all_passed = passed == 4
    print(f"\nResult: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed


def test_audio_processor():
    print("\n=== Testing AudioProcessor ===\n")
    
    processor = AudioProcessor(sample_rate=44100)
    
    processor.noise_gate.enabled = False
    processor.noise_removal.enabled = False
    
    test_audio = 0.3 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 4410, dtype=np.float32))
    
    output = processor.process(test_audio)
    
    print(f"Input shape: {test_audio.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output level: {processor.get_output_level():.1f} dB")
    print(f"Chain contains: {[p.__class__.__name__ for p in processor.chain]}")
    
    level_reasonable = -60 < processor.get_output_level() < 0
    print(f"\n✓ AudioProcessor works: {'PASS' if level_reasonable else 'FAIL'}")
    
    return level_reasonable


if __name__ == "__main__":
    try:
        gate_ok = test_noise_gate()
        proc_ok = test_audio_processor()
        
        if gate_ok and proc_ok:
            print("\n" + "="*50)
            print("✓ ALL TESTS PASSED")
            print("="*50)
        else:
            print("\n" + "="*50)
            print("✗ SOME TESTS FAILED")
            print("="*50)
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
