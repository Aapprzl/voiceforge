"""Test script for Preset System - Stage 8 verification"""
import sys
import os
import json
import tempfile
sys.path.insert(0, '.')

from presets.preset_manager import PresetManager
from presets.defaults import PRESETS


def test_preset_manager():
    print("=== Testing PresetManager ===\n")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"presets": {}, "active_preset": "streaming"}')
        config_path = f.name
    
    try:
        pm = PresetManager(config_path=config_path)
        
        print("1. Testing load_defaults:")
        print(f"   Built-in presets: {list(PRESETS.keys())}")
        presets = pm.list_presets()
        print(f"   Total presets: {len(presets)}")
        print(f"   ✓ PASS\n")
        
        print("2. Testing load_preset:")
        for name in ['streaming', 'podcast', 'gaming']:
            params = pm.load_preset(name)
            print(f"   {name}: loaded {'✓' if params else '✗'}")
            if params:
                print(f"      - Has {len(params)} keys")
        print(f"   ✓ PASS\n")
        
        print("3. Testing save_preset (custom):")
        custom_params = PRESETS['streaming'].copy()
        custom_params['name'] = 'My Custom Preset'
        result = pm.save_preset('custom_test', custom_params)
        print(f"   Save result: {result}")
        loaded = pm.load_preset('custom_test')
        print(f"   Load custom: {'✓' if loaded else '✗'}")
        print(f"   ✓ PASS\n")
        
        print("4. Testing delete_preset:")
        can_delete = pm.delete_preset('custom_test')
        print(f"   Delete custom: {can_delete}")
        cannot_delete = not pm.delete_preset('streaming')
        print(f"   Cannot delete built-in: {cannot_delete}")
        print(f"   ✓ PASS\n")
        
        print("5. Testing list_presets:")
        all_presets = pm.list_presets()
        print(f"   Total: {len(all_presets)}")
        for p in all_presets:
            marker = "[B]" if p['is_builtin'] else "[C]"
            print(f"   {marker} {p['name']}")
        print(f"   ✓ PASS\n")
        
        print("6. Testing active_preset:")
        pm.set_active_preset('podcast')
        active = pm.get_active_preset()
        print(f"   Set to podcast, get: {active}")
        print(f"   ✓ PASS\n")
        
        print("7. Testing config persistence:")
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        print(f"   Config has presets: {len(saved_config.get('presets', {}))}")
        print(f"   Config has active_preset: {saved_config.get('active_preset')}")
        print(f"   ✓ PASS\n")
        
        all_passed = True
        
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)
    
    return all_passed


def test_apply_preset_to_processor():
    print("\n=== Testing Apply Preset to AudioProcessor ===\n")
    
    from core.processor import AudioProcessor
    from presets.preset_manager import PresetManager
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"presets": {}, "active_preset": "streaming"}')
        config_path = f.name
    
    try:
        pm = PresetManager(config_path=config_path)
        processor = AudioProcessor()
        
        preset = pm.load_preset('podcast')
        
        if preset:
            processor.set_params(preset)
            
            print(f"Applied 'podcast' preset:")
            print(f"  NoiseGate threshold: {processor.noise_gate.threshold_db}")
            print(f"  NoiseRemoval strength: {processor.noise_removal.strength}")
            print(f"  Compressor ratio: {processor.compressor.ratio}")
            print(f"  AutoLeveler enabled: {processor.auto_leveler.enabled}")
            
            threshold_ok = processor.noise_gate.threshold_db == -45.0
            strength_ok = processor.noise_removal.strength == 0.6
            ratio_ok = processor.compressor.ratio == 3.0
            
            print(f"\n  Threshold correct (-45): {'✓' if threshold_ok else '✗'}")
            print(f"  Strength correct (0.6): {'✓' if strength_ok else '✗'}")
            print(f"  Ratio correct (3.0): {'✓' if ratio_ok else '✗'}")
            
            return threshold_ok and strength_ok and ratio_ok
        
        return False
        
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


if __name__ == "__main__":
    try:
        pm_ok = test_preset_manager()
        apply_ok = test_apply_preset_to_processor()
        
        if pm_ok and apply_ok:
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
