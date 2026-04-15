from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QGroupBox
from PyQt6.QtCore import Qt, pyqtSignal


class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 26)
        self.setText("")
        self.setStyleSheet("""
            QCheckBox {
                background-color: #333;
                border-radius: 13px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 11px;
                background-color: #555;
                margin: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #2ecc71;
            }
        """)


class ControlSlider(QWidget):
    valueChanged = pyqtSignal(float)
    
    def __init__(self, label, min_val, max_val, default_val, unit="", decimals=1, parent=None):
        super().__init__(parent)
        
        self._min = min_val
        self._max = max_val
        self._unit = unit
        self._decimals = decimals
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(2)
        
        header_layout = QHBoxLayout()
        
        name_label = QLabel(label)
        name_label.setStyleSheet("color: #ccc; font-size: 12px;")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        self._value_label = QLabel()
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._value_label.setStyleSheet("color: #2ecc71; font-size: 12px; font-weight: bold;")
        header_layout.addWidget(self._value_label)
        
        layout.addLayout(header_layout)
        
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(1000)
        self._slider.setValue(int((default_val - min_val) / (max_val - min_val) * 1000))
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #333;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                background-color: #2ecc71;
                border-radius: 7px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal {
                background-color: #2ecc71;
                border-radius: 3px;
            }
        """)
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider)
        
        self._update_value_label(default_val)
    
    def _on_slider_changed(self, slider_val):
        value = self._min + (slider_val / 1000) * (self._max - self._min)
        self._update_value_label(value)
        self.valueChanged.emit(value)
    
    def _update_value_label(self, value):
        if self._decimals == 0:
            self._value_label.setText(f"{int(value)}{self._unit}")
        else:
            self._value_label.setText(f"{value:.{self._decimals}f}{self._unit}")
    
    def setValue(self, value):
        slider_val = int((value - self._min) / (self._max - self._min) * 1000)
        self._slider.blockSignals(True)
        self._slider.setValue(slider_val)
        self._slider.blockSignals(False)
        self._update_value_label(value)
    
    def getValue(self):
        slider_val = self._slider.value()
        return self._min + (slider_val / 1000) * (self._max - self._min)


class ControlGroup(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        
        self._toggle = ToggleSwitch()
        header_layout.addWidget(self._toggle)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #2ecc71; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(20, 5, 10, 5)
        self._content_layout.setSpacing(8)
        layout.addWidget(self._content)
        
        self._toggle.toggled.connect(self._on_toggle)
        self._on_toggle(False)
    
    def _on_toggle(self, checked):
        self._content.setVisible(checked)
    
    def add_slider(self, label, min_val, max_val, default_val, unit="", decimals=1):
        slider = ControlSlider(label, min_val, max_val, default_val, unit, decimals)
        self._content_layout.addWidget(slider)
        return slider
    
    def setChecked(self, checked):
        self._toggle.setChecked(checked)
    
    def isChecked(self):
        return self._toggle.isChecked()


class NoiseGateControls(QWidget):
    threshold_changed = pyqtSignal(float)
    attack_changed = pyqtSignal(float)
    release_changed = pyqtSignal(float)
    enabled_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)
        
        self._gate_group = ControlGroup("Noise Gate")
        self._gate_threshold = self._gate_group.add_slider("Threshold", -80, 0, -40, " dB")
        self._gate_attack = self._gate_group.add_slider("Attack", 1, 100, 10, " ms", 0)
        self._gate_release = self._gate_group.add_slider("Release", 10, 1000, 100, " ms", 0)
        layout.addWidget(self._gate_group)
        
        self._gate_threshold.valueChanged.connect(self.threshold_changed.emit)
        self._gate_attack.valueChanged.connect(self.attack_changed.emit)
        self._gate_release.valueChanged.connect(self.release_changed.emit)
        self._gate_group._toggle.toggled.connect(self.enabled_changed.emit)
        
        layout.addStretch()
    
    def set_params(self, params):
        if 'enabled' in params:
            self._gate_group.setChecked(params['enabled'])
        if 'threshold_db' in params:
            self._gate_threshold.setValue(params['threshold_db'])
        if 'attack_ms' in params:
            self._gate_attack.setValue(params['attack_ms'])
        if 'release_ms' in params:
            self._gate_release.setValue(params['release_ms'])
    
    def get_params(self):
        return {
            'enabled': self._gate_group.isChecked(),
            'threshold_db': self._gate_threshold.getValue(),
            'attack_ms': self._gate_attack.getValue(),
            'release_ms': self._gate_release.getValue()
        }


class NoiseRemovalControls(QWidget):
    strength_changed = pyqtSignal(float)
    enabled_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)
        
        self._nr_group = ControlGroup("Noise Removal")
        self._nr_strength = self._nr_group.add_slider("Strength", 0, 100, 75, "%", 0)
        layout.addWidget(self._nr_group)
        
        self._nr_strength.valueChanged.connect(lambda v: self.strength_changed.emit(v / 100))
        self._nr_group._toggle.toggled.connect(self.enabled_changed.emit)
        
        layout.addStretch()
    
    def set_params(self, params):
        if 'enabled' in params:
            self._nr_group.setChecked(params['enabled'])
        if 'strength' in params:
            self._nr_strength.setValue(params['strength'] * 100)
    
    def get_params(self):
        return {
            'enabled': self._nr_group.isChecked(),
            'strength': self._nr_strength.getValue() / 100
        }


class CompressorControls(QWidget):
    threshold_changed = pyqtSignal(float)
    ratio_changed = pyqtSignal(float)
    attack_changed = pyqtSignal(float)
    release_changed = pyqtSignal(float)
    enabled_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)
        
        self._comp_group = ControlGroup("Compressor")
        self._comp_threshold = self._comp_group.add_slider("Threshold", -40, 0, -20, " dB")
        self._comp_ratio = self._comp_group.add_slider("Ratio", 1, 10, 4, ":1", 1)
        self._comp_attack = self._comp_group.add_slider("Attack", 1, 100, 5, " ms", 0)
        self._comp_release = self._comp_group.add_slider("Release", 10, 500, 100, " ms", 0)
        layout.addWidget(self._comp_group)
        
        self._comp_threshold.valueChanged.connect(self.threshold_changed.emit)
        self._comp_ratio.valueChanged.connect(self.ratio_changed.emit)
        self._comp_attack.valueChanged.connect(self.attack_changed.emit)
        self._comp_release.valueChanged.connect(self.release_changed.emit)
        self._comp_group._toggle.toggled.connect(self.enabled_changed.emit)
        
        layout.addStretch()
    
    def set_params(self, params):
        if 'enabled' in params:
            self._comp_group.setChecked(params['enabled'])
        if 'threshold_db' in params:
            self._comp_threshold.setValue(params['threshold_db'])
        if 'ratio' in params:
            self._comp_ratio.setValue(params['ratio'])
        if 'attack_ms' in params:
            self._comp_attack.setValue(params['attack_ms'])
        if 'release_ms' in params:
            self._comp_release.setValue(params['release_ms'])
    
    def get_params(self):
        return {
            'enabled': self._comp_group.isChecked(),
            'threshold_db': self._comp_threshold.getValue(),
            'ratio': self._comp_ratio.getValue(),
            'attack_ms': self._comp_attack.getValue(),
            'release_ms': self._comp_release.getValue()
        }


class NoiseGateTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self._noise_gate = NoiseGateControls()
        layout.addWidget(self._noise_gate)
        
        self._noise_removal = NoiseRemovalControls()
        layout.addWidget(self._noise_removal)
        
        self._compressor = CompressorControls()
        layout.addWidget(self._compressor)
        
        layout.addStretch()
    
    def get_noise_gate(self):
        return self._noise_gate
    
    def get_noise_removal(self):
        return self._noise_removal
    
    def get_compressor(self):
        return self._compressor


class EQBandSlider(QWidget):
    valueChanged = pyqtSignal(float)
    
    def __init__(self, freq_label, default_gain=0, parent=None):
        super().__init__(parent)
        
        self._freq = freq_label
        self._min = -12
        self._max = 12
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        self._value_label = QLabel("0")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setStyleSheet("color: #2ecc71; font-size: 10px; font-weight: bold;")
        layout.addWidget(self._value_label)
        
        self._slider = QSlider(Qt.Orientation.Vertical)
        self._slider.setMinimum(0)
        self._slider.setMaximum(100)
        self._slider.setValue(50)
        self._slider.setFixedHeight(120)
        self._slider.setStyleSheet("""
            QSlider::groove:vertical {
                width: 6px;
                background-color: #333;
                border-radius: 3px;
            }
            QSlider::handle:vertical {
                height: 12px;
                width: 18px;
                background-color: #2ecc71;
                border-radius: 6px;
                margin: 0 -6px;
            }
            QSlider::sub-page:vertical {
                background-color: #2ecc71;
                border-radius: 3px;
            }
        """)
        self._slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self._slider)
        
        self._freq_label = QLabel(freq_label)
        self._freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._freq_label.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(self._freq_label)
        
        self._zero_line = QWidget()
        self._zero_line.setFixedHeight(2)
        self._zero_line.setStyleSheet("background-color: #555;")
        layout.addWidget(self._zero_line)
        
        self._update_label(0)
    
    def _on_value_changed(self, slider_val):
        gain = self._min + (slider_val / 100) * (self._max - self._min)
        self._update_label(gain)
        self.valueChanged.emit(gain)
    
    def _update_label(self, gain):
        val_str = f"{gain:.0f}"
        if gain > 0:
            val_str = f"+{val_str}"
        self._value_label.setText(val_str)
        if abs(gain) < 1:
            self._value_label.setStyleSheet("color: #888; font-size: 10px;")
        else:
            self._value_label.setStyleSheet("color: #2ecc71; font-size: 10px; font-weight: bold;")
    
    def setValue(self, value):
        slider_val = int((value - self._min) / (self._max - self._min) * 100)
        self._slider.blockSignals(True)
        self._slider.setValue(slider_val)
        self._slider.blockSignals(False)
        self._update_label(value)
    
    def getValue(self):
        slider_val = self._slider.value()
        return self._min + (slider_val / 100) * (self._max - self._min)


class EQTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self._eq_group = ControlGroup("10-Band Equalizer")
        
        bands_layout = QHBoxLayout()
        bands_layout.setSpacing(5)
        
        self._band_sliders = []
        band_freqs = ["31", "63", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]
        
        for freq in band_freqs:
            slider = EQBandSlider(freq, 0)
            self._band_sliders.append(slider)
            bands_layout.addWidget(slider)
        
        self._eq_group._content_layout.addLayout(bands_layout)
        
        reset_btn_layout = QHBoxLayout()
        reset_btn_layout.addStretch()
        
        from PyQt6.QtWidgets import QPushButton
        reset_btn = QPushButton("Reset EQ")
        reset_btn.setFixedWidth(100)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        reset_btn.clicked.connect(self._reset_eq)
        reset_btn_layout.addWidget(reset_btn)
        reset_btn_layout.addStretch()
        
        self._eq_group._content_layout.addLayout(reset_btn_layout)
        
        layout.addWidget(self._eq_group)
        layout.addStretch()
    
    def _reset_eq(self):
        for slider in self._band_sliders:
            slider.setValue(0)
    
    def get_band_sliders(self):
        return self._band_sliders
    
    def set_band_values(self, values):
        for i, val in enumerate(values):
            if i < len(self._band_sliders):
                self._band_sliders[i].setValue(val)


class AutoLevelerControls(QWidget):
    enabled_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        self._al_group = ControlGroup("Auto-Leveling")
        layout.addWidget(self._al_group)
        
        target_layout = QHBoxLayout()
        target_label = QLabel("Target level: -18 dBFS")
        target_label.setStyleSheet("color: #888; font-size: 11px;")
        target_layout.addWidget(target_label)
        target_layout.addStretch()
        self._al_group._content_layout.addLayout(target_layout)
        
        state_layout = QHBoxLayout()
        state_label = QLabel("Status:")
        state_label.setStyleSheet("color: #888; font-size: 11px;")
        state_layout.addWidget(state_label)
        
        self._state_indicator = QLabel("Idle")
        self._state_indicator.setStyleSheet("color: #2ecc71; font-size: 11px; font-weight: bold;")
        state_layout.addWidget(self._state_indicator)
        state_layout.addStretch()
        self._al_group._content_layout.addLayout(state_layout)
        
        self._al_group._toggle.toggled.connect(self.enabled_changed.emit)
        
        layout.addStretch()
    
    def set_state(self, state):
        state_colors = {
            "idle": "#888",
            "gaining": "#2ecc71",
            "reducing": "#e74c3c",
            "stable": "#2ecc71"
        }
        self._state_indicator.setText(state.capitalize())
        self._state_indicator.setStyleSheet(f"color: {state_colors.get(state, '#888')}; font-size: 11px; font-weight: bold;")
    
    def setChecked(self, checked):
        self._al_group.setChecked(checked)
    
    def isChecked(self):
        return self._al_group.isChecked()


class VoiceEnhancerControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)
        
        self._ve_group = ControlGroup("Voice Enhancer")
        self._warmth = self._ve_group.add_slider("Warmth", 0, 100, 50, "%", 0)
        self._warmth_desc = QLabel("Adds body to low-mids")
        self._warmth_desc.setStyleSheet("color: #666; font-size: 9px; margin-left: 20px;")
        self._ve_group._content_layout.addWidget(self._warmth_desc)
        
        self._presence = self._ve_group.add_slider("Presence", 0, 100, 50, "%", 0)
        self._presence_desc = QLabel("Clarity boost at 3-5kHz")
        self._presence_desc.setStyleSheet("color: #666; font-size: 9px; margin-left: 20px;")
        self._ve_group._content_layout.addWidget(self._presence_desc)
        
        self._deesser = self._ve_group.add_slider("De-esser", 0, 100, 50, "%", 0)
        self._deesser_desc = QLabel("Reduces harsh S/T sounds")
        self._deesser_desc.setStyleSheet("color: #666; font-size: 9px; margin-left: 20px;")
        self._ve_group._content_layout.addWidget(self._deesser_desc)
        
        self._harmonic = self._ve_group.add_slider("Harmonic Warmth", 0, 100, 30, "%", 0)
        self._harmonic_desc = QLabel("Adds warmth through soft saturation")
        self._harmonic_desc.setStyleSheet("color: #666; font-size: 9px; margin-left: 20px;")
        self._ve_group._content_layout.addWidget(self._harmonic_desc)
        
        layout.addWidget(self._ve_group)
        layout.addStretch()
    
    def set_params(self, params):
        if 'enabled' in params:
            self._ve_group.setChecked(params['enabled'])
        if 'warmth_intensity' in params:
            self._warmth.setValue(params['warmth_intensity'] * 100)
        if 'presence_intensity' in params:
            self._presence.setValue(params['presence_intensity'] * 100)
        if 'deesser_intensity' in params:
            self._deesser.setValue(params['deesser_intensity'] * 100)
        if 'harmonic_intensity' in params:
            self._harmonic.setValue(params['harmonic_intensity'] * 100)
    
    def get_params(self):
        return {
            'enabled': self._ve_group.isChecked(),
            'warmth_intensity': self._warmth.getValue() / 100,
            'presence_intensity': self._presence.getValue() / 100,
            'deesser_intensity': self._deesser.getValue() / 100,
            'harmonic_intensity': self._harmonic.getValue() / 100
        }


class LimiterIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self.setFixedSize(100, 30)
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(231, 76, 60, 0.1);
                border: 1px solid #333;
                border-radius: 3px;
            }
        """)
        
        self._label = QLabel("Limiter: OK")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: #888; font-size: 11px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.addWidget(self._label)
    
    def set_active(self, active):
        self._active = active
        if active:
            self._label.setText("Limiter: Active!")
            self._label.setStyleSheet("color: #e74c3c; font-size: 11px; font-weight: bold;")
        else:
            self._label.setText("Limiter: OK")
            self._label.setStyleSheet("color: #888; font-size: 11px;")


class VoiceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self._voice_enhancer = VoiceEnhancerControls()
        layout.addWidget(self._voice_enhancer)
        
        self._auto_leveler = AutoLevelerControls()
        layout.addWidget(self._auto_leveler)
        
        limiter_layout = QHBoxLayout()
        limiter_layout.addWidget(QLabel("Output Limiter:"))
        self._limiter_indicator = LimiterIndicator()
        limiter_layout.addWidget(self._limiter_indicator)
        limiter_layout.addStretch()
        
        limiter_info = QLabel("Ceiling: -1 dBFS (fixed)")
        limiter_info.setStyleSheet("color: #666; font-size: 10px;")
        limiter_layout.addWidget(limiter_info)
        
        layout.addLayout(limiter_layout)
        layout.addStretch()
    
    def get_voice_enhancer(self):
        return self._voice_enhancer
    
    def get_auto_leveler(self):
        return self._auto_leveler
    
    def get_limiter_indicator(self):
        return self._limiter_indicator
    
    def set_auto_leveler_state(self, state):
        self._auto_leveler.set_state(state)
