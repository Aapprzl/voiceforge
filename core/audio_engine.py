import sounddevice as sd
import numpy as np
import threading
import time
from typing import Callable, Optional


class AudioEngine:
    DEFAULT_SAMPLE_RATE = 44100
    DEFAULT_BLOCKSIZE = 512
    
    def __init__(self, sample_rate: int = 44100, blocksize: int = 512):
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self._stream: Optional[sd.Stream] = None
        self._input_device: Optional[int] = None
        self._output_device: Optional[int] = None
        self._callback_fn: Optional[Callable] = None
        self._is_running: bool = False
        self._latency_ms: float = 0.0
        self._error_count: int = 0
        self._max_errors: int = 10
        
        self._cpu_usage: float = 0.0
        self._cpu_lock = threading.Lock()
        self._processing_times = []
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def latency_ms(self) -> float:
        return self._latency_ms
    
    @property
    def cpu_usage(self) -> float:
        with self._cpu_lock:
            return self._cpu_usage
    
    def list_devices(self) -> dict:
        try:
            devices = sd.query_devices()
            if devices is None:
                return {'input': [], 'output': []}
            if isinstance(devices, dict):
                devices = [devices]
            
            input_devices = []
            output_devices = []
            
            for i, device in enumerate(devices):
                device_info = {
                    'index': i,
                    'name': device.get('name', f'Device {i}'),
                    'max_input_channels': device.get('max_input_channels', 0),
                    'max_output_channels': device.get('max_output_channels', 0),
                    'default_samplerate': device.get('default_samplerate', self.DEFAULT_SAMPLE_RATE)
                }
                
                if device_info['max_input_channels'] > 0:
                    input_devices.append(device_info)
                
                if device_info['max_output_channels'] > 0:
                    output_devices.append(device_info)
            
            return {
                'input': input_devices,
                'output': output_devices
            }
        except Exception:
            return {'input': [], 'output': []}
    
    def set_blocksize(self, blocksize: int) -> None:
        self.blocksize = max(128, min(4096, blocksize))
        self._latency_ms = (self.blocksize / self.sample_rate) * 1000
    
    def start(
        self,
        input_device_index: int,
        output_device_index: int,
        callback_fn: Callable[[np.ndarray], np.ndarray]
    ) -> None:
        if self._is_running:
            self.stop()

        self._input_device = input_device_index
        self._output_device = output_device_index
        self._callback_fn = callback_fn
        self._processing_times = []
        self._error_count = 0
        self._latency_ms = (self.blocksize / self.sample_rate) * 1000
        
        silent_buffer = np.zeros((self.blocksize, 1), dtype=np.float32)
        
        def audio_callback(indata, outputdata, frames, time_info, status):
            nonlocal silent_buffer
            
            if status:
                return
            
            try:
                if indata.shape[0] != frames:
                    outputdata[:] = silent_buffer
                    return
                
                audio_chunk = indata[:, 0]
                
                if len(audio_chunk) != frames:
                    outputdata[:] = silent_buffer
                    return
                
                processed_audio = callback_fn(audio_chunk)
                
                if processed_audio is None or len(processed_audio) == 0:
                    outputdata[:] = silent_buffer
                    return
                
                if len(processed_audio.shape) == 1:
                    if len(processed_audio) == frames:
                        outputdata[:, 0] = processed_audio
                    else:
                        outputdata[:] = silent_buffer
                else:
                    outputdata[:] = processed_audio
                
                self._error_count = 0
                
            except Exception as e:
                self._error_count += 1
                outputdata[:] = silent_buffer
                
                if self._error_count > self._max_errors:
                    print(f"Too many errors, stopping stream...")
                    try:
                        if self._stream:
                            self._stream.stop()
                    except:
                        pass
        
        stream = sd.Stream(
            samplerate=self.sample_rate,
            blocksize=self.blocksize,
            device=(input_device_index, output_device_index),
            channels=(1, 1),
            dtype=np.float32,
            callback=audio_callback
        )

        stream.start()
        self._stream = stream
        self._is_running = True

    def stop(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        
        self._is_running = False
        self._input_device = None
        self._output_device = None
        self._callback_fn = None
        self._processing_times = []
        self._cpu_usage = 0.0
        self._latency_ms = 0.0
        self._error_count = 0
    
    def get_stats(self) -> dict:
        return {
            'latency_ms': self._latency_ms,
            'cpu_usage': 0.0,
            'blocksize': self.blocksize,
            'sample_rate': self.sample_rate,
            'is_running': self._is_running,
            'error_count': self._error_count
        }
