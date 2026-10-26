import sounddevice as sd
import numpy as np
import threading
import time
from typing import Callable, Optional


class AudioEngine:
    DEFAULT_SAMPLE_RATE = 44100
    DEFAULT_BLOCKSIZE = 512
    
    def __init__(self, sample_rate: int = 44100, blocksize: int = 1024):
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
            
            input_map = {}
            output_map = {}
            
            # Keywords to ignore (Useless or cryptic system devices)
            ignore_keywords = [
                'mapper', 'primary', 'capture driver', 'stereo mix', 
                '@system32', 'input ()', 'hands-free hf', 'steam',
                'nvidia output', 'amd capture', 'virtual'
            ]
            
            for i, device in enumerate(devices):
                full_name = device.get('name', '').strip()
                name_lower = full_name.lower()
                
                # Filter out junk/cryptic devices
                if not full_name or any(k in name_lower for k in ignore_keywords):
                    continue
                
                # Basic cleaning: remove extra spaces or empty parens
                clean_name = full_name.split(' (')[0] if ' (' in full_name else full_name
                
                host_api = sd.query_hostapis(device.get('hostapi', 0)).get('name', '')
                is_wasapi = "WASAPI" in host_api.upper()
                
                device_info = {
                    'index': i,
                    'name': clean_name, # Use cleaner name for display
                    'full_name': full_name, # Keep full for internal use if needed
                    'max_input_channels': device.get('max_input_channels', 0),
                    'max_output_channels': device.get('max_output_channels', 0),
                    'host_api': host_api
                }
                
                # Input Filtering
                if device_info['max_input_channels'] > 0:
                    # Preference: Only show Hardware-like names, prioritize WASAPI
                    if clean_name not in input_map or is_wasapi:
                        input_map[clean_name] = device_info
                
                # Output Filtering
                if device_info['max_output_channels'] > 0:
                    if clean_name not in output_map or is_wasapi:
                        output_map[clean_name] = device_info
            
            return {
                'input': sorted(input_map.values(), key=lambda x: x['name']),
                'output': sorted(output_map.values(), key=lambda x: x['name'])
            }
        except Exception as e:
            import debug_logger
            debug_logger.log(f"Error listing devices: {e}")
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
        
        import debug_logger
        debug_logger.log(f"Configuring sd.Stream: InDevice={input_device_index}, OutDevice={output_device_index}, Rate={self.sample_rate}, Block={self.blocksize}, Channels=(1,1)")
        
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
