import os
import sys

# Remove all graphics overrides to let the OS handle rendering
# Prevent math library threading conflicts in audio thread
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import json
import threading
import psutil
import numpy as np
from collections import deque

# Prevent math library threading conflicts in audio thread
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from ui.main_window import MainWindow
from core.audio_engine import AudioEngine
from core.processor import AudioProcessor
from presets.preset_manager import PresetManager
import debug_logger

class AudioSignals(QObject):
    error_occurred = pyqtSignal(str)

class VoiceForgeApp:
    def __init__(self):
        debug_logger.clear_log()
        debug_logger.log("App initializing...")
        
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("VoiceForge")
        self.app.setStyle("Fusion")
        
        self.signals = AudioSignals()
        
        self.audio_engine = AudioEngine()
        self.processor = AudioProcessor()
        self.preset_manager = PresetManager()
        self._frame_count = 0
        self._visual_queue = deque(maxlen=5)
        
        self.window = MainWindow(audio_engine=self.audio_engine)
        self.window.set_preset_manager(self.preset_manager)
        self.window.set_processor(self.processor)
        
        # Connect audio signals to UI
        self.signals.error_occurred.connect(self.window.set_error)
        
        self._setup_cpu_monitor() # Re-enabled CPU monitor
        
        debug_logger.log("Setup connections")
        self._setup_connections()
        debug_logger.log("Load settings")
        self._load_settings()
        debug_logger.log("Setup control connections")
        self._setup_control_connections()
        self._setup_cpu_monitor()
        
        # Setup visualization polling (Safest way to pass high freq data on Windows)
        self._viz_timer = QTimer()
        self._viz_timer.timeout.connect(self._update_visualizers)
        # Delay start to ensure window is mapped
        QTimer.singleShot(1000, lambda: self._viz_timer.start(30))
        
        debug_logger.log("Showing window")
        self.window.show()
        debug_logger.log("Init complete")
    
    def _setup_connections(self):
        self.window.power_toggled.connect(self._on_power_toggled)
        self.window.device_selected.connect(self._on_device_selected)
        self.window.preset_selected.connect(self._on_preset_selected)
    
    def _load_settings(self):
        config_path = "config/settings.json"
        settings = {}
        
        try:
            with open(config_path, 'r') as f:
                settings = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, IOError):
            settings = {}
        
        try:
            if settings.get('input_device') is not None:
                input_dev = settings['input_device']
                for i in range(self.window.get_input_combo().count()):
                    if self.window.get_input_combo().itemData(i) == input_dev:
                        self.window.get_input_combo().setCurrentIndex(i)
                        break
        except Exception:
            pass
        
        try:
            if settings.get('output_device') is not None:
                output_dev = settings['output_device']
                for i in range(self.window.get_output_combo().count()):
                    if self.window.get_output_combo().itemData(i) == output_dev:
                        self.window.get_output_combo().setCurrentIndex(i)
                        break
        except Exception:
            pass
        
        try:
            if settings.get('active_preset'):
                preset_name = settings['active_preset']
                combo = self.window.get_preset_combo()
                for i in range(combo.count()):
                    if combo.itemData(i) == preset_name:
                        combo.setCurrentIndex(i)
                        self._apply_preset(preset_name)
                        break
                else:
                    self._apply_preset('streaming')
            else:
                self._apply_preset('streaming')
        except Exception:
            self._apply_preset('streaming')
    
    def _save_settings(self):
        config_path = "config/settings.json"
        settings = {
            'input_device': self.window.get_input_combo().currentData(),
            'output_device': self.window.get_output_combo().currentData(),
            'active_preset': self.window.get_preset_combo().currentData(),
            'presets': {}
        }
        
        try:
            with open(config_path, 'r') as f:
                existing = json.load(f)
                if 'presets' in existing:
                    settings['presets'] = existing['presets']
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        
        with open(config_path, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def _apply_preset(self, preset_name):
        preset = self.preset_manager.load_preset(preset_name)
        if preset:
            self.processor.set_params(preset)
            
            ng_tab = self.window.get_noise_gate_tab()
            ng_tab.get_noise_gate().set_params(preset.get('NoiseGate', {}))
            ng_tab.get_noise_removal().set_params(preset.get('NoiseRemoval', {}))
            ng_tab.get_compressor().set_params(preset.get('Compressor', {}))
            
            eq_tab = self.window.get_eq_tab()
            if 'Equalizer10Band' in preset and 'bands' in preset['Equalizer10Band']:
                bands = preset['Equalizer10Band']['bands']
                band_values = []
                freq_map = {'31Hz': 0, '63Hz': 1, '125Hz': 2, '250Hz': 3, '500Hz': 4,
                           '1000Hz': 5, '2000Hz': 6, '4000Hz': 7, '8000Hz': 8, '16000Hz': 9}
                for i in range(10):
                    band_values.append(0)
                for band_name, gain in bands.items():
                    if band_name in freq_map:
                        band_values[freq_map[band_name]] = gain
                eq_tab.set_band_values(band_values)
            
            voice_tab = self.window.get_voice_tab()
            voice_tab.get_voice_enhancer().set_params(preset.get('VoiceEnhancer', {}))
    
    def _on_power_toggled(self, checked):
        if checked:
            self._start_streaming()
        else:
            self._stop_streaming()
    
    def _on_device_selected(self, input_idx, output_idx):
        pass
    
    def _setup_control_connections(self):
        ng_tab = self.window.get_noise_gate_tab()
        
        ng_tab.get_noise_gate().threshold_changed.connect(
            lambda v: self.processor.noise_gate.set_threshold(v))
        ng_tab.get_noise_gate().attack_changed.connect(
            lambda v: self.processor.noise_gate.set_attack(v))
        ng_tab.get_noise_gate().release_changed.connect(
            lambda v: self.processor.noise_gate.set_release(v))
        ng_tab.get_noise_gate().enabled_changed.connect(
            lambda e: setattr(self.processor.noise_gate, 'enabled', e))
        
        ng_tab.get_noise_removal().strength_changed.connect(
            lambda v: self.processor.noise_removal.set_strength(v))
        ng_tab.get_noise_removal().enabled_changed.connect(
            lambda e: setattr(self.processor.noise_removal, 'enabled', e))
        
        ng_tab.get_compressor().threshold_changed.connect(
            lambda v: setattr(self.processor.compressor, 'threshold_db', v))
        ng_tab.get_compressor().ratio_changed.connect(
            lambda v: setattr(self.processor.compressor, 'ratio', v))
        ng_tab.get_compressor().attack_changed.connect(
            lambda v: setattr(self.processor.compressor, 'attack_ms', v))
        ng_tab.get_compressor().release_changed.connect(
            lambda v: setattr(self.processor.compressor, 'release_ms', v))
        ng_tab.get_compressor().enabled_changed.connect(
            lambda e: setattr(self.processor.compressor, 'enabled', e))
        
        voice_tab = self.window.get_voice_tab()
        
        ve = voice_tab.get_voice_enhancer()
        ve._warmth.valueChanged.connect(
            lambda v: setattr(self.processor.voice_enhancer, 'warmth_intensity', v / 100))
        ve._presence.valueChanged.connect(
            lambda v: setattr(self.processor.voice_enhancer, 'presence_intensity', v / 100))
        ve._deesser.valueChanged.connect(
            lambda v: setattr(self.processor.voice_enhancer, 'deesser_intensity', v / 100))
        ve._harmonic.valueChanged.connect(
            lambda v: setattr(self.processor.voice_enhancer, 'harmonic_intensity', v / 100))
        ve._ve_group._toggle.toggled.connect(
            lambda e: setattr(self.processor.voice_enhancer, 'enabled', e))
        
        voice_tab.get_auto_leveler().enabled_changed.connect(
            lambda e: setattr(self.processor.auto_leveler, 'enabled', e))
        
        eq_tab = self.window.get_eq_tab()
        for i, slider in enumerate(eq_tab.get_band_sliders()):
            slider.valueChanged.connect(
                lambda v, idx=i: self.processor.equalizer.set_band(idx, v))
    
    def _on_preset_selected(self, preset_name, preset_data):
        self._apply_preset(preset_name)
        self.preset_manager.set_active_preset(preset_name)
    
    def _start_streaming(self):
        debug_logger.log("Attempting to start streaming...")
        input_idx = self.window.get_input_combo().currentData()
        output_idx = self.window.get_output_combo().currentData()
        
        if input_idx is None or output_idx is None:
            debug_logger.log("Error: No device selected")
            self.window.set_error("No device selected")
            self.window.set_streaming(False)
            return
        
        try:
            # Robust lookup: Find the device by index in the official list
            import sounddevice as sd
            all_devices = sd.query_devices()
            
            input_name = "Unknown"
            output_name = "Unknown"
            
            if 0 <= input_idx < len(all_devices):
                input_name = all_devices[input_idx].get('name', 'Unknown')
            if 0 <= output_idx < len(all_devices):
                output_name = all_devices[output_idx].get('name', 'Unknown')
                
            debug_logger.log(f"Opening: [{input_name}] -> [{output_name}]")
            
            self.audio_engine.start(
                input_idx,
                output_idx,
                self._process_audio
            )
            
            debug_logger.log("Audio engine started successfully")
            self.window.set_streaming(True)
            self.window.start_visualizer()
            debug_logger.log("UI updated to streaming state")
            
        except Exception as e:
            import traceback
            err_msg = str(e)
            debug_logger.log(f"Failed to start stream: {err_msg}\n{traceback.format_exc()}")
            self.window.set_error(err_msg)
            self.window.set_streaming(False) # This resets the power button visually
    
    def _stop_streaming(self):
        try:
            self.audio_engine.stop()
            self.window.set_streaming(False)
            self.window.stop_visualizer()
        except Exception as e:
            print(f"Error stopping: {e}")
    
    def _process_audio(self, audio_chunk):
        try:
            self._frame_count += 1
            if self._frame_count % 200 == 0:
                debug_logger.log(f"Heartbeat: Frame {self._frame_count} processed")

            if audio_chunk is None or len(audio_chunk) == 0:
                return np.zeros(1024, dtype=np.float32)
            
            processed = self.processor.process(audio_chunk)
            
            # Use thread-safe queue instead of signals to prevent Access Violation
            self._visual_queue.append(processed.copy())
                
            return processed
            
        except Exception as e:
            debug_logger.log(f"Process error: {e}")
            return np.zeros(len(audio_chunk) if audio_chunk is not None else 512, dtype=np.float32)

    def _update_visualizers(self):
        """Poll the visual queue from the UI thread (Zero-latency polling)"""
        try:
            viz = self.window.get_visualizer() if self.window else None
            if not viz or not self._visual_queue:
                return
            
            # Flush the queue to get the absolute LATEST frame for visual sync
            processed_chunk = None
            while self._visual_queue:
                processed_chunk = self._visual_queue.popleft()
            
            if processed_chunk is not None:
                viz.update_audio(processed_chunk)
        except Exception:
            pass
            
    def _setup_cpu_monitor(self):
        self._cpu_timer = QTimer()
        self._cpu_timer.timeout.connect(self._update_stats)
        self._cpu_timer.start(500)
    
    def _update_stats(self):
        try:
            stats = self.audio_engine.get_stats()
            cpu = stats.get('cpu_usage', 0)
            self.window.set_cpu_usage(cpu)
            
            if self.audio_engine.is_running:
                latency = stats.get('latency_ms', 0)
                self.window._status_label.setText(f"Streaming | {self.audio_engine.sample_rate} Hz | Latency: ~{latency:.1f}ms")
        except:
            pass
    
    def run(self):
        """Main entry point to run the application"""
        try:
            debug_logger.log("App starting exec loop")
            exit_code = self.app.exec()
            debug_logger.log(f"App exec loop finished with code: {exit_code}")
            self._save_settings()
            self._stop_streaming()
            return exit_code
        except Exception as e:
            debug_logger.log(f"CRITICAL APP ERROR during exec: {e}")
            return 1


def main():
    voiceforge = VoiceForgeApp()
    voiceforge.run()


if __name__ == "__main__":
    main()
