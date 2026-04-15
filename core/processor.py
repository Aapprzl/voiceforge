import numpy as np
import noisereduce as nr
import pedalboard
from scipy.signal import iirpeak, sosfilt
from typing import List, Optional


class NoiseGate:
    def __init__(
        self,
        threshold_db: float = -40.0,
        attack_ms: float = 10.0,
        release_ms: float = 100.0,
        sample_rate: int = 44100
    ):
        self.threshold_db = threshold_db
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.sample_rate = sample_rate
        self.enabled = True
        
        self._envelope = 0.0
    
    def set_threshold(self, threshold_db: float) -> None:
        self.threshold_db = np.clip(threshold_db, -80.0, 0.0)
    
    def set_attack(self, attack_ms: float) -> None:
        self.attack_ms = attack_ms
    
    def set_release(self, release_ms: float) -> None:
        self.release_ms = release_ms
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
        
        threshold_linear = 10 ** (self.threshold_db / 20.0)
        n_samples = len(audio)
        
        frame_rms = np.sqrt(np.mean(audio ** 2))
        
        if frame_rms > threshold_linear:
            coeff = np.exp(-n_samples / (self.sample_rate * self.attack_ms / 1000.0))
            self._envelope = frame_rms + coeff * (self._envelope - frame_rms)
        else:
            coeff = np.exp(-n_samples / (self.sample_rate * self.release_ms / 1000.0))
            self._envelope = coeff * self._envelope
        
        gate_open = self._envelope > threshold_linear
        
        if gate_open:
            return audio
        else:
            return np.zeros_like(audio)
    
    def get_params(self) -> dict:
        return {
            'enabled': self.enabled,
            'threshold_db': self.threshold_db,
            'attack_ms': self.attack_ms,
            'release_ms': self.release_ms
        }
    
    def set_params(self, params: dict) -> None:
        if 'enabled' in params:
            self.enabled = params['enabled']
        if 'threshold_db' in params:
            self.set_threshold(params['threshold_db'])
        if 'attack_ms' in params:
            self.set_attack(params['attack_ms'])
        if 'release_ms' in params:
            self.set_release(params['release_ms'])


class NoiseRemoval:
    def __init__(self, strength: float = 0.75, sample_rate: int = 44100):
        self.strength = strength
        self.sample_rate = sample_rate
        self.enabled = True
        
        self._buffer = np.array([], dtype=np.float32)
        self._buffer_duration = 0.5
        self._min_buffer_samples = int(sample_rate * self._buffer_duration)
        self._output_buffer = np.array([], dtype=np.float32)
    
    def set_strength(self, strength: float) -> None:
        self.strength = np.clip(strength, 0.0, 1.0)
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
        
        self._buffer = np.concatenate([self._buffer, audio])
        
        if len(self._buffer) < self._min_buffer_samples:
            return np.zeros(len(audio), dtype=np.float32)
        
        if len(self._output_buffer) > 0:
            output_len = min(len(audio), len(self._output_buffer))
            output = self._output_buffer[:output_len]
            self._output_buffer = self._output_buffer[output_len:]
            if output_len < len(audio):
                output = np.concatenate([output, np.zeros(len(audio) - output_len, dtype=np.float32)])
            return output[:len(audio)]
        
        audio_2d = self._buffer.reshape(1, -1)
        
        noise_sample = self._buffer[:self._min_buffer_samples]
        if np.std(noise_sample) > 0:
            noise_profile = noise_sample.reshape(1, -1)
        else:
            noise_profile = None
        
        try:
            reduced = nr.reduce_noise(
                y=audio_2d,
                sr=self.sample_rate,
                stationary=False,
                prop_decrease=self.strength,
                y_noise=noise_profile
            )
        except Exception:
            reduced = audio_2d
        
        reduced_1d = reduced[0]
        
        self._output_buffer = reduced_1d[self._min_buffer_samples:]
        self._buffer = np.array([], dtype=np.float32)
        
        output_len = min(len(audio), len(self._output_buffer))
        output = self._output_buffer[:output_len]
        self._output_buffer = self._output_buffer[output_len:]
        
        if output_len < len(audio):
            output = np.concatenate([output, np.zeros(len(audio) - output_len, dtype=np.float32)])
        
        return output
    
    def flush(self) -> np.ndarray:
        remaining = self._output_buffer.copy()
        self._buffer = np.array([], dtype=np.float32)
        self._output_buffer = np.array([], dtype=np.float32)
        return remaining
    
    def get_params(self) -> dict:
        return {
            'enabled': self.enabled,
            'strength': self.strength
        }
    
    def set_params(self, params: dict) -> None:
        if 'enabled' in params:
            self.enabled = params['enabled']
        if 'strength' in params:
            self.set_strength(params['strength'])


class Compressor:
    def __init__(
        self,
        threshold_db: float = -20.0,
        ratio: float = 4.0,
        attack_ms: float = 5.0,
        release_ms: float = 100.0,
        knee_db: float = 6.0,
        sample_rate: int = 44100
    ):
        self.threshold_db = threshold_db
        self.ratio = ratio
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.knee_db = knee_db
        self.sample_rate = sample_rate
        self.enabled = True
        
        self._pedalboard_comp = pedalboard.Compressor(
            threshold_db=threshold_db,
            ratio=ratio,
            attack_ms=attack_ms,
            release_ms=release_ms
        )
        self._makeup_gain = pedalboard.Gain(gain_db=0.0)
    
    def _update_pedalboard(self) -> None:
        self._pedalboard_comp = pedalboard.Compressor(
            threshold_db=self.threshold_db,
            ratio=self.ratio,
            attack_ms=self.attack_ms,
            release_ms=self.release_ms
        )
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
        
        audio_2d = audio.reshape(1, -1)
        
        compressed = self._pedalboard_comp(audio_2d, self.sample_rate)
        
        rms = np.sqrt(np.mean(compressed ** 2))
        if rms > 0:
            current_db = 20 * np.log10(rms)
            target_db = -12.0
            makeup_db = target_db - current_db
            makeup_db = max(0, min(makeup_db, 20))
        else:
            makeup_db = 0
        
        self._makeup_gain = pedalboard.Gain(gain_db=makeup_db)
        with_makeup = self._makeup_gain(compressed, self.sample_rate)
        
        return with_makeup[0].astype(np.float32)
    
    def get_params(self) -> dict:
        return {
            'enabled': self.enabled,
            'threshold_db': self.threshold_db,
            'ratio': self.ratio,
            'attack_ms': self.attack_ms,
            'release_ms': self.release_ms
        }
    
    def set_params(self, params: dict) -> None:
        if 'enabled' in params:
            self.enabled = params['enabled']
        if 'threshold_db' in params:
            self.threshold_db = float(np.clip(params['threshold_db'], -40, 0))
            self._update_pedalboard()
        if 'ratio' in params:
            self.ratio = float(np.clip(params['ratio'], 1, 10))
            self._update_pedalboard()
        if 'attack_ms' in params:
            self.attack_ms = float(np.clip(params['attack_ms'], 1, 100))
            self._update_pedalboard()
        if 'release_ms' in params:
            self.release_ms = float(np.clip(params['release_ms'], 10, 500))
            self._update_pedalboard()


class AutoLeveler:
    def __init__(
        self,
        target_db: float = -18.0,
        window_sec: float = 2.0,
        sample_rate: int = 44100
    ):
        self.target_db = target_db
        self.window_sec = window_sec
        self.sample_rate = sample_rate
        self.enabled = True
        
        self._window_samples = int(sample_rate * window_sec)
        self._level_history = []
        self._current_gain = 1.0
        self._max_gain = 3.0
        self._min_gain = 0.1
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
        
        rms = np.sqrt(np.mean(audio ** 2))
        current_db = 20 * np.log10(rms) if rms > 1e-10 else -60.0
        
        self._level_history.append(current_db)
        if len(self._level_history) > 10:
            self._level_history.pop(0)
        
        avg_db = sum(self._level_history) / len(self._level_history) if self._level_history else -60.0
        
        target_linear = 10 ** (self.target_db / 20.0)
        
        gain_change_rate = 0.01
        
        if avg_db < self.target_db - 1:
            target_gain = target_linear / (rms + 1e-10)
            self._current_gain += gain_change_rate * (target_gain - self._current_gain)
        elif avg_db > -1:
            self._current_gain *= 0.95
        
        self._current_gain = np.clip(self._current_gain, self._min_gain, self._max_gain)
        
        return audio * self._current_gain
    
    def get_gain_state(self) -> str:
        if len(self._level_history) < 2:
            return "idle"
        recent = self._level_history[-1]
        if recent < self.target_db - 2:
            return "gaining"
        elif recent > -2:
            return "reducing"
        return "stable"
    
    def get_params(self) -> dict:
        return {
            'enabled': self.enabled,
            'target_db': self.target_db
        }
    
    def set_params(self, params: dict) -> None:
        if 'enabled' in params:
            self.enabled = params['enabled']
        if 'target_db' in params:
            self.target_db = float(np.clip(params['target_db'], -30, -6))


class Equalizer10Band:
    BANDS = [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    Q = 1.41
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.enabled = True
        self._band_gains = [0.0] * 10
        self._band_filters = [None] * 10
        self._update_filters()
    
    def _update_filters(self) -> None:
        for i, freq in enumerate(self.BANDS):
            gain = self._band_gains[i]
            self._band_filters[i] = self._create_band_filter(freq, gain)
    
    def _create_band_filter(self, center_freq: float, gain_db: float):
        from scipy.signal import iirpeak
        if abs(gain_db) < 0.1:
            return None
        
        Q = self.Q
        b, a = iirpeak(center_freq, Q, fs=self.sample_rate)
        
        return (b, a)
    
    def set_band(self, band_index: int, gain_db: float) -> None:
        if 0 <= band_index < 10:
            self._band_gains[band_index] = np.clip(gain_db, -12.0, 12.0)
            self._update_filters()
    
    def set_all_bands(self, gains: List[float]) -> None:
        for i, gain in enumerate(gains):
            if i < 10:
                self._band_gains[i] = np.clip(gain, -12.0, 12.0)
        self._update_filters()
    
    def reset(self) -> None:
        self._band_gains = [0.0] * 10
        self._update_filters()
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
        
        from scipy.signal import lfilter
        result = audio.copy()
        
        for filt in self._band_filters:
            if filt is not None:
                b, a = filt
                result = lfilter(b, a, result)
        
        return result
    
    def get_params(self) -> dict:
        return {
            'enabled': self.enabled,
            'bands': dict(zip([f'{f}Hz' for f in self.BANDS], self._band_gains))
        }
    
    def set_params(self, params: dict) -> None:
        if 'enabled' in params:
            self.enabled = params['enabled']
        if 'bands' in params:
            for band_name, gain in params['bands'].items():
                for i, freq in enumerate(self.BANDS):
                    if f'{freq}Hz' == band_name:
                        self.set_band(i, gain)
                        break


class VoiceEnhancer:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.enabled = True
        
        self.warmth_enabled = True
        self.warmth_intensity = 0.5
        
        self.presence_enabled = True
        self.presence_intensity = 0.5
        
        self.deesser_enabled = False
        self.deesser_intensity = 0.5
        
        self.harmonic_enabled = False
        self.harmonic_intensity = 0.3
        
        self._warmth_sos = self._create_warmth_filter()
        self._presence_sos = self._create_presence_filter()
        self._deesser_sos = self._create_deesser_filter()
    
    def _create_warmth_filter(self):
        from scipy.signal import iirpeak
        center = 250
        Q = 1.0
        b, a = iirpeak(center, Q, fs=self.sample_rate)
        return (b, a)
    
    def _create_presence_filter(self):
        from scipy.signal import iirpeak
        center = 3500
        Q = 1.0
        b, a = iirpeak(center, Q, fs=self.sample_rate)
        return (b, a)
    
    def _create_deesser_filter(self):
        from scipy.signal import butter
        sos = butter(4, [6000, 9000], btype='bandpass', fs=self.sample_rate, output='sos')
        return sos
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
        
        from scipy.signal import lfilter, sosfiltfilt
        
        result = audio.copy()
        
        if self.warmth_enabled and self.warmth_intensity > 0:
            warmth_gain = self.warmth_intensity * 3
            b, a = self._warmth_sos
            filtered = lfilter(b, a, result)
            result = result + filtered * warmth_gain
        
        if self.presence_enabled and self.presence_intensity > 0:
            presence_gain = self.presence_intensity * 4
            b, a = self._presence_sos
            filtered = lfilter(b, a, result)
            result = result + filtered * presence_gain
        
        if self.deesser_enabled and self.deesser_intensity > 0:
            deesser = sosfiltfilt(self._deesser_sos, result)
            result = result - deesser * self.deesser_intensity * 0.5
        
        if self.harmonic_enabled and self.harmonic_intensity > 0:
            gain = self.harmonic_intensity * 2
            result = np.tanh(result * (1 + gain)) / np.tanh(1 + gain)
        
        return result
    
    def get_params(self) -> dict:
        return {
            'enabled': self.enabled,
            'warmth_enabled': self.warmth_enabled,
            'warmth_intensity': self.warmth_intensity,
            'presence_enabled': self.presence_enabled,
            'presence_intensity': self.presence_intensity,
            'deesser_enabled': self.deesser_enabled,
            'deesser_intensity': self.deesser_intensity,
            'harmonic_enabled': self.harmonic_enabled,
            'harmonic_intensity': self.harmonic_intensity
        }
    
    def set_params(self, params: dict) -> None:
        if 'enabled' in params:
            self.enabled = params['enabled']
        if 'warmth_enabled' in params:
            self.warmth_enabled = params['warmth_enabled']
        if 'warmth_intensity' in params:
            self.warmth_intensity = float(np.clip(params['warmth_intensity'], 0.0, 1.0))
        if 'presence_enabled' in params:
            self.presence_enabled = params['presence_enabled']
        if 'presence_intensity' in params:
            self.presence_intensity = float(np.clip(params['presence_intensity'], 0.0, 1.0))
        if 'deesser_enabled' in params:
            self.deesser_enabled = params['deesser_enabled']
        if 'deesser_intensity' in params:
            self.deesser_intensity = float(np.clip(params['deesser_intensity'], 0.0, 1.0))
        if 'harmonic_enabled' in params:
            self.harmonic_enabled = params['harmonic_enabled']
        if 'harmonic_intensity' in params:
            self.harmonic_intensity = float(np.clip(params['harmonic_intensity'], 0.0, 1.0))


class Limiter:
    CEILING_DB = -1.0
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.enabled = True
        self._ceiling_linear = 10 ** (self.CEILING_DB / 20.0)
        self._pedalboard_limiter = pedalboard.Limiter(threshold_db=self.CEILING_DB, release_ms=50)
        self._limiter_active = False
        self._peak_hold_time = 0
        self._peak_hold_samples = int(sample_rate * 2)
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
        
        peak = np.max(np.abs(audio))
        
        if peak > self._ceiling_linear:
            self._limiter_active = True
            self._peak_hold_time = self._peak_hold_samples
        elif self._peak_hold_time > 0:
            self._peak_hold_time -= len(audio)
        else:
            self._limiter_active = False
        
        audio_2d = audio.reshape(1, -1)
        limited = self._pedalboard_limiter(audio_2d, self.sample_rate)
        
        limited_1d = np.clip(limited[0], -self._ceiling_linear, self._ceiling_linear)
        
        return limited_1d.astype(np.float32)
    
    def is_limiter_active(self) -> bool:
        return self._limiter_active
    
    def get_params(self) -> dict:
        return {
            'enabled': self.enabled
        }
    
    def set_params(self, params: dict) -> None:
        if 'enabled' in params:
            self.enabled = params['enabled']


class AudioProcessor:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.chain: List = []
        self._output_level = -60.0
        
        self.noise_gate = NoiseGate(sample_rate=sample_rate)
        self.noise_removal = NoiseRemoval(sample_rate=sample_rate)
        self.compressor = Compressor(sample_rate=sample_rate)
        self.equalizer = Equalizer10Band(sample_rate=sample_rate)
        self.voice_enhancer = VoiceEnhancer(sample_rate=sample_rate)
        self.auto_leveler = AutoLeveler(sample_rate=sample_rate)
        self.limiter = Limiter(sample_rate=sample_rate)
        self.chain.append(self.noise_gate)
        self.chain.append(self.noise_removal)
        self.chain.append(self.compressor)
        self.chain.append(self.equalizer)
        self.chain.append(self.voice_enhancer)
        self.chain.append(self.auto_leveler)
        self.chain.append(self.limiter)
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        result = audio.copy()
        
        for processor in self.chain:
            result = processor.process(result)
        
        result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
        
        rms = np.sqrt(np.mean(result ** 2))
        if rms > 0:
            self._output_level = 20 * np.log10(rms)
        else:
            self._output_level = -60.0
        
        return result
    
    def get_output_level(self) -> float:
        return self._output_level
    
    def get_params(self) -> dict:
        params = {}
        for processor in self.chain:
            name = processor.__class__.__name__
            params[name] = processor.get_params()
        return params
    
    def set_params(self, params: dict) -> None:
        for processor in self.chain:
            name = processor.__class__.__name__
            if name in params:
                processor.set_params(params[name])
