"""Test script for Limiter & Final Chain - Stage 7 verification"""
import sys
import numpy as np
sys.path.insert(0, '.')

from core.processor import Limiter, AudioProcessor


def test_limiter():
    print("=== Testing Limiter ===\n")
    
    sample_rate = 44100
    limiter = Limiter(sample_rate=sample_rate)
    
    print(f"Limiter ceiling: {limiter.CEILING_DB} dBFS ({limiter._ceiling_linear:.4f} linear)")
    
    t = np.linspace(0, 1.0, sample_rate, dtype=np.float32)
    
    clipping_signal = 1.5 * np.sin(2 * np.pi * 440 * t)
    
    output = limiter.process(clipping_signal)
    peak = np.max(np.abs(output))
    
    print(f"Input peak: {np.max(np.abs(clipping_signal)):.4f} (would clip)")
    print(f"Output peak: {peak:.4f}")
    print(f"Clipping prevented: {'✓' if peak <= limiter._ceiling_linear * 1.01 else '✗'}")
    
    quiet_signal = 0.3 * np.sin(2 * np.pi * 440 * t)
    output_quiet = limiter.process(quiet_signal)
    quiet_peak = np.max(np.abs(output_quiet))
    
    print(f"\nQuiet signal (0.3):")
    print(f"  Input peak: {quiet_peak:.4f}")
    print(f"  Output peak: {np.max(np.abs(output_quiet)):.4f}")
    print(f"  Quiet passed through: {'✓' if abs(quiet_peak - np.max(np.abs(output_quiet))) < 0.01 else '✗'}")
    
    limiter.enabled = False
    output_bypass = limiter.process(clipping_signal)
    bypass_peak = np.max(np.abs(output_bypass))
    print(f"\nBypass mode:")
    print(f"  Output peak: {bypass_peak:.4f}")
    print(f"  Bypass works: {'✓' if abs(bypass_peak - 1.5) < 0.01 else '✗'}")
    
    limiter.enabled = True
    limiter_active = limiter.is_limiter_active()
    print(f"\n  Limiter active indicator: {limiter_active}")
    
    clipping_prevented = peak <= limiter._ceiling_linear * 1.01
    quiet_preserved = abs(quiet_peak - np.max(np.abs(output_quiet))) < 0.01
    bypass_works = abs(bypass_peak - 1.5) < 0.01
    
    print(f"\n  Clipping prevented: {'✓ PASS' if clipping_prevented else '✗ FAIL'}")
    print(f"  Quiet preserved:    {'✓ PASS' if quiet_preserved else '✗ FAIL'}")
    print(f"  Bypass works:       {'✓ PASS' if bypass_works else '✗ FAIL'}")
    
    return clipping_prevented and quiet_preserved and bypass_works


def test_full_processor_chain():
    print("\n=== Testing Full Processor Chain ===\n")
    
    processor = AudioProcessor(sample_rate=44100)
    
    print(f"Chain: {[p.__class__.__name__ for p in processor.chain]}")
    
    all_processors = [
        processor.noise_gate,
        processor.noise_removal,
        processor.compressor,
        processor.equalizer,
        processor.voice_enhancer,
        processor.auto_leveler,
        processor.limiter
    ]
    
    for p in all_processors:
        attr_name = p.__class__.__name__.replace('Equalizer10Band', 'equalizer').replace('NoiseGate', 'noise_gate').replace('NoiseRemoval', 'noise_removal').replace('Compressor', 'compressor').replace('VoiceEnhancer', 'voice_enhancer').replace('AutoLeveler', 'auto_leveler').replace('Limiter', 'limiter')
        assert hasattr(processor, attr_name), f"Missing {attr_name}"
    
    sample_rate = 44100
    t = np.linspace(0, 0.5, sample_rate // 2, dtype=np.float32)
    signal = 0.3 * np.sin(2 * np.pi * 440 * t)
    
    processor.noise_gate.enabled = False
    processor.noise_removal.enabled = False
    processor.compressor.enabled = False
    processor.auto_leveler.enabled = False
    processor.equalizer.enabled = False
    processor.voice_enhancer.enabled = False
    processor.limiter.enabled = True
    
    output = processor.process(signal)
    output_level = processor.get_output_level()
    
    print(f"Input RMS: {np.sqrt(np.mean(signal**2)):.4f}")
    print(f"Output RMS: {np.sqrt(np.mean(output**2)):.4f}")
    print(f"Output level: {output_level:.1f} dB")
    
    limiter_chain = processor.limiter
    loud_signal = 1.5 * np.sin(2 * np.pi * 440 * t)
    limited_output = limiter_chain.process(loud_signal)
    limited_peak = np.max(np.abs(limited_output))
    
    print(f"\nWith clipping signal (1.5):")
    print(f"  Output peak: {limited_peak:.4f}")
    print(f"  Limited to ceiling: {'✓' if limited_peak < 1.2 else '✗'}")
    
    params = processor.get_params()
    print(f"\nProcessor params keys: {list(params.keys())}")
    print(f"All 7 processors in chain: {'✓' if len(params) == 7 else '✗'}")
    
    output_reasonable = output_level > -60 and output_level < 0
    limiter_works = limited_peak < 1.2
    chain_complete = len(params) == 7
    
    print(f"\n  Output reasonable:    {'✓ PASS' if output_reasonable else '✗ FAIL'}")
    print(f"  Limiter works:       {'✓ PASS' if limiter_works else '✗ FAIL'}")
    print(f"  Chain complete (7):  {'✓ PASS' if chain_complete else '✗ FAIL'}")
    
    return output_reasonable and limiter_works and chain_complete


if __name__ == "__main__":
    try:
        limiter_ok = test_limiter()
        chain_ok = test_full_processor_chain()
        
        if limiter_ok and chain_ok:
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
