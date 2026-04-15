import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._audio_data = np.zeros(22050, dtype=np.float32)
        self._waveform_color = QColor("#2ecc71")
        self._background_color = QColor("#1a1a1a")
        
        self.setStyleSheet("border: 1px solid #333; border-radius: 3px;")
    
    def update_audio(self, audio_chunk: np.ndarray) -> None:
        self._audio_data = np.concatenate([self._audio_data[len(audio_chunk):], audio_chunk])
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.fillRect(self.rect(), self._background_color)
        
        width = self.width()
        height = self.height()
        center_y = height // 2
        
        pen = QPen(self._waveform_color, 1.5)
        painter.setPen(pen)
        
        samples = len(self._audio_data)
        x_step = width / min(samples, width)
        
        points = []
        for i in range(min(samples, width * 2)):
            x = (i / 2) * x_step
            sample_idx = int(i * samples / (width * 2))
            if sample_idx < len(self._audio_data):
                y = center_y - self._audio_data[sample_idx] * (height // 2) * 0.9
                points.append((x, y))
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i+1][0]), int(points[i+1][1]))
        
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawLine(0, center_y, width, center_y)


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
        db_min = -60
        
        level_y = height - ((self._level - db_min) / db_range * height)
        level_height = height - level_y
        
        if level_height > 0:
            if self._level > -6:
                color = self._red
            elif self._level > -12:
                color = self._yellow
            else:
                color = self._green
            
            painter.fillRect(5, level_y, width - 10, level_height, color)
        
        if self._peak_level > db_min:
            peak_y = height - ((self._peak_level - db_min) / db_range * height)
            painter.fillRect(5, peak_y - 2, width - 10, 4, QColor("#fff"))
        
        painter.setPen(QPen(QColor("#555"), 1))
        for db in [-60, -40, -20, -12, -6, 0]:
            y = height - ((db - db_min) / db_range * height)
            painter.drawLine(0, int(y), width, int(y))
        
        painter.setPen(QPen(QColor("#666"), 1))
        painter.setFont(self.font())
        
        labels = ["0", "-6", "-12", "-20", "-40", "-60"]
        db_values = [0, -6, -12, -20, -40, -60]
        for label, db in zip(labels, db_values):
            y = height - ((db - db_min) / db_range * height)
            painter.drawText(width - 25, int(y) + 4, label)


class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        self._waveform_label = QLabel("Waveform")
        self._waveform_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._waveform_label)
        
        self._waveform = WaveformWidget()
        self._waveform.setFixedHeight(200)
        layout.addWidget(self._waveform)
        
        self._level_label = QLabel("Level")
        self._level_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._level_label)
        
        self._level_meter = LevelMeterWidget()
        self._level_meter.setFixedHeight(150)
        layout.addWidget(self._level_meter)
        
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._on_timer)
        self._pending_audio = None
    
    def start(self) -> None:
        self._update_timer.start(33)
    
    def stop(self) -> None:
        self._update_timer.stop()
    
    def _on_timer(self) -> None:
        if self._pending_audio is not None:
            self._waveform.update_audio(self._pending_audio)
            self._pending_audio = None
        
        current_level = self._level_meter._level
        self._level_meter.update_level(current_level - 0.5)
    
    def update_audio(self, audio_chunk: np.ndarray) -> None:
        self._pending_audio = audio_chunk
        
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        if rms > 0:
            level_db = 20 * np.log10(rms)
        else:
            level_db = -60.0
        
        self._level_meter.update_level(level_db)
    
    def update_level(self, level_db: float) -> None:
        self._level_meter.update_level(level_db)
    
    def get_waveform(self):
        return self._waveform
    
    def get_level_meter(self):
        return self._level_meter
