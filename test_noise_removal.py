"""Test script for NoiseRemoval - Stage 4 verification"""
import sys
import numpy as np
sys.path.insert(0, '.')

from core.processor import NoiseRemoval, NoiseGate, AudioProcessor


def test_noise_removal():
    print("=== Testing NoiseRemoval ===\n")
    
    sample_rate = 44100
    
    t = np.linspace(0, 3.0, int(sample_rate * 3.0), dtype=np.float32)
    
    noise = np.random.normal(0, 0.05, len(t)).astype(np.float32)
    
    signal_freq = 440
    signal = 0.3 * np.sin(2 * np.pi * signal_freq * t)
    
    audio_with_noise = signal + noise
    
    print(f"Test signal: 3s of 440Hz sine + white noise")
    print(f"Input RMS: {np.sqrt(np.mean(audio_with_noise**2)):.4f}")
    print(f"Noise RMS: {np.sqrt(np.mean(noise**2)):.4f}\n")
    
    nr_processor = NoiseRemoval(strength=0.75, sample_rate=sample_rate)
    
    chunk_size = 1024
    output_chunks = []
    
    for i in range(0, len(audio_with_noise), chunk_size):
        chunk = audio_with_noise[i:i+chunk_size]
        output_chunk = nr_processor.process(chunk)
        output_chunks.append(output_chunk)
    
    remaining = nr_processor.flush()
    if len(remaining) > 0:
        output_chunks.append(remaining)
    
    output = np.concatenate(output_chunks)
    
    skip_samples = int(sample_rate * 0.6)
    output_trimmed = output[skip_samples:]
    
    input_trimmed = audio_with_noise[skip_samples:]
    
    input_rms = np.sqrt(np.mean(input_trimmed**2))
    output_rms = np.sqrt(np.mean(output_trimmed**2))
    noise_rms = np.sqrt(np.mean(noise[skip_samples:]**2))
    
    print(f"After buffer latency skip ({skip_samples/sample_rate:.1f}s):")
    print(f"  Input RMS: {input_rms:.4f}")
    print(f"  Output RMS: {output_rms:.4f}")
    print(f"  Original noise RMS: {noise_rms:.4f}")
    print(f"  Noise reduction ratio: {noise_rms / (output_rms + 1e-10):.2f}x")
    
    signal_preserved = output_rms > 0.01
    noise_reduced = output_rms < input_rms
    
    print(f"\nSignal preserved (output > 0.01): {'✓ PASS' if signal_preserved else '✗ FAIL'}")
    print(f"Noise reduced (output < input):    {'✓ PASS' if noise_reduced else '✗ FAIL'}")
    
    return signal_preserved and noise_reduced


def test_audio_processor_chain():
    print("\n=== Testing AudioProcessor with Noise Gate + Noise Removal ===\n")
    
    processor = AudioProcessor(sample_rate=44100)
    
    print(f"Chain: {[p.__class__.__name__ for p in processor.chain]}")
    
    sample_rate = 44100
    t = np.linspace(0, 1.0, sample_rate, dtype=np.float32)
    signal = 0.3 * np.sin(2 * np.pi * 440 * t)
    
    processor.noise_gate.enabled = True
    processor.noise_removal.enabled = True
    
    output = processor.process(signal)
    
    print(f"Output level: {processor.get_output_level():.1f} dB")
    
    params = processor.get_params()
    print(f"Processor params keys: {list(params.keys())}")
    
    processor.set_params({
        'NoiseRemoval': {'strength': 0.5}
    })
    
    print(f"After set_params, strength: {processor.noise_removal.strength}")
    
    works = processor.get_output_level() > -60
    print(f"\n{'✓ PASS' if works else '✗ FAIL'}")
    
    return works


if __name__ == "__main__":
    try:
        nr_ok = test_noise_removal()
        proc_ok = test_audio_processor_chain()
        
        if nr_ok and proc_ok:
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
