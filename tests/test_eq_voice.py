"""Test script for EQ & VoiceEnhancer - Stage 6 verification"""
import sys
import numpy as np
sys.path.insert(0, '.')

from core.processor import Equalizer10Band, VoiceEnhancer, AudioProcessor


def test_equalizer():
    print("=== Testing Equalizer10Band ===\n")
    
    sample_rate = 44100
    t = np.linspace(0, 1.0, sample_rate, dtype=np.float32)
    
    signal = np.sin(2 * np.pi * 1000 * t)
    
    eq = Equalizer10Band(sample_rate=sample_rate)
    
    original_rms = np.sqrt(np.mean(signal ** 2))
    
    output = eq.process(signal)
    output_rms_flat = np.sqrt(np.mean(output ** 2))
    
    print(f"Flat EQ (all 0dB):")
    print(f"  Original RMS: {original_rms:.4f}")
    print(f"  Output RMS: {output_rms_flat:.4f}")
    print(f"  Level preserved: {'✓' if abs(output_rms_flat - original_rms) < 0.1 else '✗'}")
    
    eq.set_band(5, 6.0)
    eq.set_band(6, 6.0)
    
    output = eq.process(signal)
    output_rms_boosted = np.sqrt(np.mean(output ** 2))
    
    print(f"\nEQ boosted at 1kHz & 2kHz (+6dB each):")
    print(f"  Output RMS: {output_rms_boosted:.4f}")
    print(f"  Processing changed signal: {'✓' if abs(output_rms_boosted - original_rms) > 0.01 else '✗'}")
    
    eq.reset()
    output = eq.process(signal)
    output_rms_reset = np.sqrt(np.mean(output ** 2))
    
    print(f"\nAfter reset (all 0dB):")
    print(f"  Output RMS: {output_rms_reset:.4f}")
    
    flat_preserved = abs(output_rms_flat - original_rms) < 0.1
    processing_changed = abs(output_rms_boosted - original_rms) > 0.01
    reset_works = abs(output_rms_reset - original_rms) < 0.1
    
    print(f"\n  Flat EQ preserved: {'✓ PASS' if flat_preserved else '✗ FAIL'}")
    print(f"  Processing works:  {'✓ PASS' if processing_changed else '✗ FAIL'}")
    print(f"  Reset works:       {'✓ PASS' if reset_works else '✗ FAIL'}")
    
    return flat_preserved and processing_changed and reset_works


def test_voice_enhancer():
    print("\n=== Testing VoiceEnhancer ===\n")
    
    sample_rate = 44100
    t = np.linspace(0, 1.0, sample_rate, dtype=np.float32)
    
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    enhancer = VoiceEnhancer(sample_rate=sample_rate)
    
    original_rms = np.sqrt(np.mean(signal ** 2))
    
    enhancer.enabled = False
    output = enhancer.process(signal)
    bypass_rms = np.sqrt(np.mean(output ** 2))
    print(f"Bypass mode: {bypass_rms:.4f} (same as input: {'✓' if abs(bypass_rms - original_rms) < 0.01 else '✗'})")
    
    enhancer.enabled = True
    enhancer.warmth_enabled = True
    enhancer.warmth_intensity = 0.5
    enhancer.presence_enabled = True
    enhancer.presence_intensity = 0.5
    enhancer.deesser_enabled = False
    enhancer.harmonic_enabled = False
    
    output = enhancer.process(signal)
    output_rms = np.sqrt(np.mean(output ** 2))
    
    print(f"With warmth & presence: {output_rms:.4f}")
    print(f"  Signal changed: {'✓' if abs(output_rms - original_rms) > 0.01 else '✗'}")
    
    enhancer.harmonic_enabled = True
    enhancer.harmonic_intensity = 0.3
    output = enhancer.process(signal)
    
    print(f"With harmonic warmth: {np.sqrt(np.mean(output**2)):.4f}")
    
    bypass_ok = abs(bypass_rms - original_rms) < 0.01
    processed_ok = abs(output_rms - original_rms) > 0.01
    
    print(f"\n  Bypass works: {'✓ PASS' if bypass_ok else '✗ FAIL'}")
    print(f"  Processing works: {'✓ PASS' if processed_ok else '✗ FAIL'}")
    
    return bypass_ok and processed_ok


def test_audio_processor_chain():
    print("\n=== Testing AudioProcessor with EQ & VoiceEnhancer ===\n")
    
    processor = AudioProcessor(sample_rate=44100)
    
    print(f"Chain: {[p.__class__.__name__ for p in processor.chain]}")
    
    sample_rate = 44100
    t = np.linspace(0, 0.5, sample_rate // 2, dtype=np.float32)
    signal = 0.3 * np.sin(2 * np.pi * 440 * t)
    
    processor.noise_gate.enabled = False
    processor.noise_removal.enabled = False
    processor.compressor.enabled = False
    processor.auto_leveler.enabled = False
    
    processor.equalizer.enabled = True
    processor.voice_enhancer.enabled = True
    
    output = processor.process(signal)
    
    print(f"Output level: {processor.get_output_level():.1f} dB")
    
    params = processor.get_params()
    print(f"Processor params keys: {list(params.keys())}")
    
    processor.equalizer.set_band(5, 6.0)
    
    output_changed = processor.process(signal)
    output_rms = np.sqrt(np.mean(output_changed ** 2))
    original_rms = np.sqrt(np.mean(signal ** 2))
    
    print(f"After EQ boost: RMS {output_rms:.4f} (was {original_rms:.4f})")
    
    works = processor.get_output_level() > -60
    eq_processing = abs(output_rms - original_rms) > 0.001
    
    print(f"\n  Processor works: {'✓ PASS' if works else '✗ FAIL'}")
    print(f"  EQ processing:    {'✓ PASS' if eq_processing else '✗ FAIL'}")
    
    return works and eq_processing


if __name__ == "__main__":
    try:
        eq_ok = test_equalizer()
        voice_ok = test_voice_enhancer()
        proc_ok = test_audio_processor_chain()
        
        if eq_ok and voice_ok and proc_ok:
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
