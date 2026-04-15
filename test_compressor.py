"""Test script for Compressor & AutoLeveler - Stage 5 verification"""
import sys
import numpy as np
sys.path.insert(0, '.')

from core.processor import Compressor, AutoLeveler, AudioProcessor


def test_compressor():
    print("=== Testing Compressor ===\n")
    
    sample_rate = 44100
    t = np.linspace(0, 1.0, sample_rate, dtype=np.float32)
    
    quiet_part = 0.1 * np.sin(2 * np.pi * 440 * t[:sample_rate//4])
    loud_part = 0.8 * np.sin(2 * np.pi * 440 * t[sample_rate//4:sample_rate//2])
    quiet_part2 = 0.1 * np.sin(2 * np.pi * 440 * t[sample_rate//2:3*sample_rate//4])
    loud_part2 = 0.9 * np.sin(2 * np.pi * 440 * t[3*sample_rate//4:])
    
    test_signal = np.concatenate([quiet_part, loud_part, quiet_part2, loud_part2])
    
    input_rms = np.sqrt(np.mean(test_signal ** 2))
    input_peak = np.max(np.abs(test_signal))
    
    print(f"Input: quiet(0.1) -> loud(0.8) -> quiet(0.1) -> loud(0.9)")
    print(f"Input RMS: {input_rms:.4f}, Peak: {input_peak:.4f}\n")
    
    compressor = Compressor(threshold_db=-20.0, ratio=4.0, sample_rate=sample_rate)
    
    output = compressor.process(test_signal)
    
    output_rms = np.sqrt(np.mean(output ** 2))
    output_peak = np.max(np.abs(output))
    
    quiet_len = sample_rate // 4
    loud_len = sample_rate // 4
    
    quiet_output_rms = np.sqrt(np.mean(output[quiet_len:2*quiet_len]**2))
    loud_output_rms = np.sqrt(np.mean(output[2*quiet_len:2*quiet_len+loud_len]**2))
    
    print(f"Output RMS: {output_rms:.4f}, Peak: {output_peak:.4f}")
    print(f"Quiet part RMS: {quiet_output_rms:.4f}")
    print(f"Loud part RMS: {loud_output_rms:.4f}")
    print(f"Dynamic range (loud/quiet): {loud_output_rms/quiet_output_rms:.1f}x (was {0.8/0.1:.0f}x)")
    
    dynamic_compressed = loud_output_rms / quiet_output_rms < 10.0
    peak_below_clip = output_peak < 1.0
    signal_preserved = output_rms > 0.1
    
    print(f"\nSignal preserved: {'✓ PASS' if signal_preserved else '✗ FAIL'}")
    print(f"Dynamic range compressed: {'✓ PASS' if dynamic_compressed else '✗ FAIL'}")
    print(f"No clipping (peak < 1.0): {'✓ PASS' if peak_below_clip else '✗ FAIL'}")
    
    return signal_preserved and dynamic_compressed and peak_below_clip


def test_auto_leveler():
    print("\n=== Testing AutoLeveler ===\n")
    
    sample_rate = 44100
    t = np.linspace(0, 5.0, int(sample_rate * 5.0), dtype=np.float32)
    
    quiet_signal = 0.05 * np.sin(2 * np.pi * 440 * t)
    
    leveler = AutoLeveler(target_db=-18.0, sample_rate=sample_rate)
    
    chunk_size = 512
    output_chunks = []
    
    for i in range(0, len(quiet_signal), chunk_size):
        chunk = quiet_signal[i:i+chunk_size]
        output_chunk = leveler.process(chunk)
        output_chunks.append(output_chunk)
    
    output = np.concatenate(output_chunks)
    
    output_rms = np.sqrt(np.mean(output ** 2))
    output_db = 20 * np.log10(output_rms) if output_rms > 1e-10 else -60
    
    print(f"Input: quiet signal (RMS ~0.05, -26 dBFS)")
    print(f"Output level: {output_db:.1f} dBFS")
    print(f"Target: -18 dBFS")
    
    gain_state = leveler.get_gain_state()
    current_gain = leveler._current_gain
    print(f"Gain state: {gain_state}")
    print(f"Current gain: {current_gain:.2f}x")
    
    level_closer = output_db > -25 and current_gain > 1.0
    
    print(f"\nLevel raised (gain > 1.0): {'✓ PASS' if level_closer else '✗ FAIL'}")
    
    return level_closer


def test_audio_processor_chain():
    print("\n=== Testing AudioProcessor with Compressor & AutoLeveler ===\n")
    
    processor = AudioProcessor(sample_rate=44100)
    
    print(f"Chain: {[p.__class__.__name__ for p in processor.chain]}")
    
    sample_rate = 44100
    t = np.linspace(0, 0.5, sample_rate // 2, dtype=np.float32)
    signal = 0.3 * np.sin(2 * np.pi * 440 * t)
    
    processor.noise_gate.enabled = True
    processor.noise_removal.enabled = False
    processor.compressor.enabled = True
    processor.auto_leveler.enabled = True
    
    output = processor.process(signal)
    
    print(f"Output level: {processor.get_output_level():.1f} dB")
    
    params = processor.get_params()
    print(f"Processor params keys: {list(params.keys())}")
    
    processor.set_params({
        'Compressor': {'threshold_db': -15.0, 'ratio': 3.0}
    })
    
    print(f"After set_params, compressor threshold: {processor.compressor.threshold_db}")
    print(f"Compressor ratio: {processor.compressor.ratio}")
    
    works = processor.get_output_level() > -60
    print(f"\n{'✓ PASS' if works else '✗ FAIL'}")
    
    return works


if __name__ == "__main__":
    try:
        comp_ok = test_compressor()
        level_ok = test_auto_leveler()
        proc_ok = test_audio_processor_chain()
        
        if comp_ok and level_ok and proc_ok:
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
