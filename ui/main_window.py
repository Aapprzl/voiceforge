import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton, QTabWidget, QScrollArea
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont


class MainWindow(QMainWindow):
    device_selected = pyqtSignal(int, int)
    power_toggled = pyqtSignal(bool)
    preset_selected = pyqtSignal(str, dict)
    
    def __init__(self, audio_engine=None):
        super().__init__()
        
        self.setWindowTitle("VoiceForge")
        self.setFixedSize(QSize(900, 600))
        self.setStyleSheet("background-color: #1a1a1a;")
        
        self._audio_engine = audio_engine
        self._is_streaming = False
        self._vb_cable_warning_shown = False
        self._preset_manager = None
        self._preset_change_locked = False
        
        self._setup_ui()
        self._populate_devices()
        self._connect_signals()
    
    def _populate_devices(self):
        if self._audio_engine:
            devices = self._audio_engine.list_devices()
            
            self._input_device_combo.blockSignals(True)
            self._output_device_combo.blockSignals(True)
            
            self._input_device_combo.clear()
            self._output_device_combo.clear()
            
            for dev in devices['input']:
                self._input_device_combo.addItem(dev['name'], dev['index'])
            
            for dev in devices['output']:
                self._output_device_combo.addItem(dev['name'], dev['index'])
            
            self._input_device_combo.blockSignals(False)
            self._output_device_combo.blockSignals(False)
    
    def _check_vb_cable(self, output_index):
        if self._audio_engine:
            devices = self._audio_engine.list_devices()
            for dev in devices['output']:
                if dev['index'] == output_index:
                    if 'cable' in dev['name'].lower() or 'vb' in dev['name'].lower():
                        self._vb_cable_warning.setVisible(False)
                        self._vb_cable_warning_shown = False
                    else:
                        self._vb_cable_warning.setVisible(True)
                        self._vb_cable_warning_shown = True
    
    def _on_output_changed(self, index):
        device_index = self._output_device_combo.currentData()
        self._check_vb_cable(device_index)
    
    def _on_refresh_clicked(self):
        self._populate_devices()
    
    def _on_power_toggled(self, checked):
        self._is_streaming = checked
        self.power_toggled.emit(checked)
        
        if checked:
            input_idx = self._input_device_combo.currentData()
            output_idx = self._output_device_combo.currentData()
            self.device_selected.emit(input_idx, output_idx)
    
    def _connect_signals(self):
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        self._output_device_combo.currentIndexChanged.connect(self._on_output_changed)
        self._power_button.toggled.connect(self._on_power_toggled)
    
    def set_audio_engine(self, engine):
        self._audio_engine = engine
        self._populate_devices()
    
    def set_streaming(self, is_streaming):
        self._is_streaming = is_streaming
        self._status_indicator.set_streaming(is_streaming)
        self._power_button.setChecked(is_streaming)
        if is_streaming:
            self._status_label.setText("Streaming | 44100 Hz | Latency: ~12ms")
        else:
            self._status_label.setText("Ready | 44100 Hz | Latency: --")
    
    def set_error(self, message):
        self._status_indicator.set_error()
        self._status_label.setText(f"Error: {message}")
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self._create_header(main_layout)
        self._create_content(main_layout)
        self._create_footer(main_layout)
    
    def _create_header(self, parent_layout):
        from PyQt6.QtWidgets import QLabel, QPushButton
        
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("background-color: #242424;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        title = QLabel("VoiceForge")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2ecc71;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self._status_indicator = StatusIndicator()
        header_layout.addWidget(self._status_indicator)
        
        header_layout.addStretch()
        
        self._power_button = QPushButton()
        self._power_button.setFixedSize(40, 40)
        self._power_button.setText("")
        self._power_button.setCheckable(True)
        self._power_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                border: 2px solid #555;
                border-radius: 20px;
            }
            QPushButton:checked {
                background-color: #2ecc71;
                border-color: #2ecc71;
            }
        """)
        header_layout.addWidget(self._power_button)
        
        parent_layout.addWidget(header)
    
    def _create_content(self, parent_layout):
        from PyQt6.QtWidgets import QTabWidget
        
        content = QWidget()
        content.setStyleSheet("background-color: #1a1a1a;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        self._left_panel = QWidget()
        self._left_panel.setFixedWidth(220)
        self._left_panel.setStyleSheet("background-color: #242424; border-radius: 5px;")
        left_layout = QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        self._setup_left_panel(left_layout)
        
        self._center_panel = QWidget()
        self._center_panel.setStyleSheet("background-color: #242424; border-radius: 5px;")
        center_layout = QVBoxLayout(self._center_panel)
        center_layout.setContentsMargins(10, 10, 10, 10)
        self._setup_center_panel(center_layout)
        
        self._right_panel = QWidget()
        self._right_panel.setFixedWidth(240)
        self._right_panel.setStyleSheet("background-color: #242424; border-radius: 5px;")
        right_layout = QVBoxLayout(self._right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        self._setup_right_panel(right_layout)
        
        content_layout.addWidget(self._left_panel)
        content_layout.addWidget(self._center_panel, 1)
        content_layout.addWidget(self._right_panel)
        
        parent_layout.addWidget(content, 1)
    
    def _setup_left_panel(self, layout):
        from PyQt6.QtWidgets import QLabel, QComboBox, QPushButton, QScrollArea
        
        layout.addWidget(QLabel("Device"))
        layout.addSpacing(5)
        
        self._input_device_combo = QComboBox()
        self._input_device_combo.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        layout.addWidget(self._input_device_combo)
        
        self._output_device_combo = QComboBox()
        self._output_device_combo.setStyleSheet(self._input_device_combo.styleSheet())
        layout.addWidget(self._output_device_combo)
        
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        layout.addWidget(self._refresh_btn)
        
        self._vb_cable_warning = QLabel("VB-Cable not found.\nInstall from vb-audio.com")
        self._vb_cable_warning.setStyleSheet("""
            color: #f39c12;
            font-size: 10px;
            padding: 5px;
            background-color: rgba(243, 156, 18, 0.1);
            border-radius: 3px;
        """)
        self._vb_cable_warning.setWordWrap(True)
        self._vb_cable_warning.setVisible(False)
        layout.addWidget(self._vb_cable_warning)
        
        layout.addSpacing(20)
        
        layout.addWidget(QLabel("Preset"))
        
        self._preset_combo = QComboBox()
        self._preset_combo.setStyleSheet(self._input_device_combo.styleSheet())
        layout.addWidget(self._preset_combo)
        
        preset_btn_layout = QHBoxLayout()
        self._save_preset_btn = QPushButton("Save...")
        self._save_preset_btn.setStyleSheet(self._refresh_btn.styleSheet())
        self._delete_preset_btn = QPushButton("Delete")
        self._delete_preset_btn.setStyleSheet(self._refresh_btn.styleSheet())
        preset_btn_layout.addWidget(self._save_preset_btn)
        preset_btn_layout.addWidget(self._delete_preset_btn)
        layout.addLayout(preset_btn_layout)
        
        layout.addStretch()
    
    def _setup_center_panel(self, layout):
        from PyQt6.QtWidgets import QTabWidget, QLabel, QScrollArea
        
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: transparent;
                border: none;
            }
            QTabBar::tab {
                background-color: #333;
                color: #aaa;
                padding: 8px 20px;
                border: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #2ecc71;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #444;
            }
        """)
        
        self._tab_noise = QScrollArea()
        self._tab_noise.setWidgetResizable(True)
        self._tab_noise.setStyleSheet("background-color: transparent; border: none;")
        
        from ui.controls import NoiseGateTab
        self._noise_gate_tab = NoiseGateTab()
        self._tab_noise.setWidget(self._noise_gate_tab)
        
        self._tab_eq = QScrollArea()
        self._tab_eq.setWidgetResizable(True)
        self._tab_eq.setStyleSheet("background-color: transparent; border: none;")
        
        from ui.controls import EQTab
        self._eq_tab = EQTab()
        self._tab_eq.setWidget(self._eq_tab)
        
        self._tab_voice = QScrollArea()
        self._tab_voice.setWidgetResizable(True)
        self._tab_voice.setStyleSheet("background-color: transparent; border: none;")
        
        from ui.controls import VoiceTab
        self._voice_tab = VoiceTab()
        self._tab_voice.setWidget(self._voice_tab)
        
        self._tabs.addTab(self._tab_noise, "Noise & Gate")
        self._tabs.addTab(self._tab_eq, "EQ")
        self._tabs.addTab(self._tab_voice, "Voice")
        
        layout.addWidget(self._tabs)
    
    def _setup_right_panel(self, layout):
        from ui.visualizer import AudioVisualizer
        
        self._visualizer = AudioVisualizer()
        layout.addWidget(self._visualizer)
        
        layout.addStretch()
    
    def _create_footer(self, parent_layout):
        footer = QWidget()
        footer.setFixedHeight(30)
        footer.setStyleSheet("background-color: #242424;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 0, 15, 0)
        
        self._status_label = QLabel("Ready | 44100 Hz | Latency: --")
        self._status_label.setStyleSheet("color: #888; font-size: 11px;")
        footer_layout.addWidget(self._status_label)
        
        footer_layout.addStretch()
        
        self._cpu_label = QLabel("CPU: --%")
        self._cpu_label.setStyleSheet("color: #888; font-size: 11px;")
        footer_layout.addWidget(self._cpu_label)
        
        parent_layout.addWidget(footer)
    
    def set_status(self, is_streaming: bool) -> None:
        self._is_streaming = is_streaming
        self._status_indicator.set_streaming(is_streaming)
        if is_streaming:
            self._status_label.setText("Streaming | 44100 Hz | Latency: ~12ms")
            self._power_button.setChecked(True)
        else:
            self._status_label.setText("Ready | 44100 Hz | Latency: --")
            self._power_button.setChecked(False)
    
    def set_cpu_usage(self, usage: float) -> None:
        self._cpu_label.setText(f"CPU: {usage:.0f}%")
    
    def get_power_button(self):
        return self._power_button
    
    def get_refresh_button(self):
        return self._refresh_btn
    
    def get_input_combo(self):
        return self._input_device_combo
    
    def get_output_combo(self):
        return self._output_device_combo
    
    def get_preset_combo(self):
        return self._preset_combo
    
    def get_tabs(self):
        return self._tabs
    
    def get_tab_noise(self):
        return self._tab_noise
    
    def get_tab_eq(self):
        return self._tab_eq
    
    def get_tab_voice(self):
        return self._tab_voice
    
    def set_preset_manager(self, preset_manager):
        self._preset_manager = preset_manager
        self._populate_presets()
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self._save_preset_btn.clicked.connect(self._on_save_preset)
        self._delete_preset_btn.clicked.connect(self._on_delete_preset)
    
    def _populate_presets(self):
        if self._preset_manager:
            self._preset_combo.blockSignals(True)
            self._preset_combo.clear()
            
            presets = self._preset_manager.list_presets()
            
            builtin_count = 0
            for p in presets:
                if p['is_builtin']:
                    self._preset_combo.addItem(f"[B] {p['display_name']}", p['name'])
                    builtin_count += 1
            
            if builtin_count < len(presets):
                self._preset_combo.insertSeparator(builtin_count)
            
            for p in presets:
                if p['is_custom']:
                    self._preset_combo.addItem(f"[C] {p['display_name']}", p['name'])
            
            active = self._preset_manager.get_active_preset()
            for i in range(self._preset_combo.count()):
                if self._preset_combo.itemData(i) == active:
                    self._preset_combo.setCurrentIndex(i)
                    break
            
            self._preset_combo.blockSignals(False)
    
    def _on_preset_changed(self, index):
        if self._preset_manager and not self._preset_change_locked:
            preset_name = self._preset_combo.itemData(index)
            if preset_name:
                preset = self._preset_manager.load_preset(preset_name)
                if preset:
                    self.preset_selected.emit(preset_name, preset)
    
    def _on_save_preset(self):
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name:
            name = name.lower().replace(' ', '_')
            if self._preset_manager and not self._preset_manager.load_preset(name):
                if hasattr(self, '_current_processor'):
                    params = self._current_processor.get_params()
                    self._preset_manager.save_preset(name, params)
                    self._populate_presets()
                    QMessageBox.information(self, "Preset Saved", f"Preset '{name}' saved successfully!")
    
    def _on_delete_preset(self):
        from PyQt6.QtWidgets import QMessageBox
        index = self._preset_combo.currentIndex()
        preset_name = self._preset_combo.itemData(index)
        if preset_name and self._preset_manager:
            preset_list = self._preset_manager.list_presets()
            for p in preset_list:
                if p['name'] == preset_name:
                    if p['is_builtin']:
                        QMessageBox.warning(self, "Cannot Delete", "Built-in presets cannot be deleted.")
                        return
                    break
            
            reply = QMessageBox.question(self, "Delete Preset", 
                f"Delete preset '{preset_name}'?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._preset_manager.delete_preset(preset_name)
                self._populate_presets()
    
    def get_preset_manager(self):
        return self._preset_manager
    
    def set_processor(self, processor):
        self._current_processor = processor
    
    def get_save_button(self):
        return self._save_preset_btn
    
    def get_delete_button(self):
        return self._delete_preset_btn
    
    def get_noise_gate_tab(self):
        return self._noise_gate_tab
    
    def get_eq_tab(self):
        return self._eq_tab
    
    def get_voice_tab(self):
        return self._voice_tab
    
    def get_visualizer(self):
        return self._visualizer
    
    def start_visualizer(self):
        self._visualizer.start()
    
    def stop_visualizer(self):
        self._visualizer.stop()


class StatusIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self._is_streaming = False
        self._is_error = False
        self.setFixedSize(100, 30)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor("#2ecc71") if self._is_streaming else QColor("#f39c12")
        if self._is_error:
            color = QColor("#e74c3c")
        
        painter.setBrush(color)
        painter.drawEllipse(5, 10, 12, 12)
        
        text = "LIVE" if self._is_streaming else "READY"
        if self._is_error:
            text = "ERROR"
        
        painter.setPen(QColor("#888"))
        painter.drawText(22, 21, text)
    
    def set_streaming(self, streaming: bool) -> None:
        self._is_streaming = streaming
        self._is_error = False
        self.update()
    
    def set_error(self) -> None:
        self._is_error = True
        self._is_streaming = False
        self.update()


def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
