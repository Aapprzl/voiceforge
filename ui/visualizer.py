import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._audio_data = np.zeros(1024, dtype=np.float32)
        self._cached_polygon = QPolygonF()
        self._waveform_color = QColor("#2ecc71")
        self._background_color = QColor("#1a1a1a")
        
        self.setStyleSheet("border: 1px solid #333; border-radius: 3px;")
    
    def update_audio(self, audio_chunk: np.ndarray) -> None:
        if audio_chunk is None or len(audio_chunk) == 0:
            return
            
        # Efficient buffer management
        chunk_len = len(audio_chunk)
        if chunk_len > 2048:
            audio_chunk = audio_chunk[-2048:]
            chunk_len = 2048
            
        # Slide buffer
        self._audio_data = np.concatenate([self._audio_data, audio_chunk])
        if len(self._audio_data) > 2048:
            self._audio_data = self._audio_data[-2048:]
            
        # Pre-calculate polygon for drawing (UI thread but outside paintEvent)
        width = self.width()
        height = self.height()
        if width <= 0 or height <= 0:
            return
            
        center_y = height / 2
        n_points = 200 # Fixed points for stability
        x_step = width / n_points
        samples = len(self._audio_data)
        
        poly = QPolygonF()
        for i in range(n_points):
            idx = int(i * samples / n_points)
            if idx < samples:
                val = float(self._audio_data[idx])
                y = center_y - (val * (height / 2) * 0.9)
                poly.append(QPointF(i * x_step, y))
        
        self._cached_polygon = poly
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)
        
        if self._cached_polygon.isEmpty():
            return
            
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self._waveform_color, 1.5))
        painter.drawPolyline(self._cached_polygon)
        
        # Center line
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawLine(0, int(self.height() / 2), self.width(), int(self.height() / 2))


class LevelMeterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._level = -60.0
        self._peak_level = -60.0
        self._peak_hold_samples = 0
        self._peak_hold_max = 60
        self._peak_decay = 0.5
        
        self._green = QColor("#2ecc71")
        self._yellow = QColor("#f1c40f")
        self._red = QColor("#e74c3c")
        self._background = QColor("#1a1a1a")
        
        self.setStyleSheet("border: 1px solid #333; border-radius: 3px;")
    
    def update_level(self, level_db: float) -> None:
        self._level = max(-60.0, min(0.0, level_db))
        
        if self._level > self._peak_level:
            self._peak_level = self._level
            self._peak_hold_samples = self._peak_hold_max
        elif self._peak_hold_samples > 0:
            self._peak_hold_samples -= 1
        else:
            self._peak_level -= self._peak_decay
            self._peak_level = max(self._level, self._peak_level)
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.fillRect(self.rect(), self._background)
        
        width = self.width()
        height = self.height()
        
        db_range = 60
        normalized_level = (self._level + db_range) / db_range
        normalized_peak = (self._peak_level + db_range) / db_range
        
        fill_width = int(width * normalized_level)
        
        if self._level > -10:
            color = self._red
        elif self._level > -20:
            color = self._yellow
        else:
            color = self._green
            
        painter.fillRect(0, 0, fill_width, height, color)
        
        # Peak indicator
        peak_x = int(width * normalized_peak)
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawLine(peak_x, 0, peak_x, height)


class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self._waveform = WaveformWidget()
        self._waveform.setFixedHeight(200)
        layout.addWidget(self._waveform)
        
        self._level_meter = LevelMeterWidget()
        self._level_meter.setFixedHeight(20)
        layout.addWidget(self._level_meter)
        
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._on_timer)
        self._pending_audio = None
        self._pending_level = None
        
    def start(self) -> None:
        self._update_timer.start(33)
        
    def stop(self) -> None:
        self._update_timer.stop()
        
    def _on_timer(self) -> None:
        if self._pending_audio is not None:
            self._waveform.update_audio(self._pending_audio)
            self._pending_audio = None
            
        if self._pending_level is not None:
            self._level_meter.update_level(self._pending_level)
            self._pending_level = None
        else:
            current_level = self._level_meter._level
            self._level_meter.update_level(max(-60.0, current_level - 1.0))
    
    def update_audio(self, audio_chunk: np.ndarray) -> None:
        self._pending_audio = audio_chunk
        
        # Calculate level in dB
        rms = np.sqrt(np.mean(audio_chunk ** 2)) if len(audio_chunk) > 0 else 0
        if rms > 0:
            level_db = 20 * np.log10(rms)
        else:
            level_db = -60.0
            
        self._pending_level = level_db
