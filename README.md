# VoiceForge

Real-time audio processor untuk meningkatkan kualitas mikrofon dengan virtual device output.

## Cara Install

1. **Install Python 3.13** (recommended) atau 3.10+
   - Download dari [python.org](https://www.python.org/downloads/)
   - **Penting**: Pastikan pakai Python 3.13 jika punya multiple Python versions

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Jika error "No module named PyQt6", pastikan pakai Python yang benar:
   ```bash
   C:\Python313\python.exe -m pip install -r requirements.txt
   ```

3. **Install VB-Audio Virtual Cable** (gratis)
   - Download dari [vb-audio.com](https://vb-audio.com/Cable/)
   - Install dan restart komputer

4. **Jalankan Aplikasi**
   ```bash
   python main.py
   ```

## Cara Pakai

1. **Pilih Input Device**
   - Pilih mikrofon yang ingin diproses dari dropdown "Input Device"

2. **Pilih Output Device**
   - Pilih "CABLE Input (VB-Audio Virtual Cable)" sebagai output

3. **Tekan Tombol Power**
   - Aplikasi akan mulai memproses audio dari mikrofon

4. **Di OBS**
   - Set microphone source ke "CABLE Output (VB-Audio Virtual Cable)"

## Preset

### Streaming
Optimized untuk gaming streams dengan aggressive noise reduction dan presence boost. Cocok untuk streaming di Twitch, YouTube, dll.

### Podcast
Warm dan clear - sempurna untuk konten spoken content panjang. Memberikan karakter suara yang lebih hangat dan natural.

### Gaming
Low latency mode dengan minimal processing. Prioritaskan responsivitas untuk competitive gaming.

## Tips Tuning

### Kapan Naikkan Noise Gate Threshold
- Jika suara pelan terpotong, naikkan threshold ke -50dB atau -45dB
- Threshold yang terlalu rendah (-20dB) tidak akan memotong noise

### Kapan Naikkan Presence
- Jika suara terdengar "far away" atau muffled
- Naikkan presence di 3-5kHz untuk kejelasan lebih
- Jangan terlalu tinggi sampai terdengar harsh

### Kapan Pakai De-esser
- Jika ada bunyi "S" atau "T" yang terlalu tajam
- Aktifkan De-esser dan atur intensity sampai nyaman

## Troubleshooting

### Suara Terlalu Pelan
- Aktifkan Auto-Leveling
- Cek preset "Streaming" yang sudah optimal

### Latency Terlalu Tinggi
- Gunakan preset "Gaming" untuk latency minimum
- Noise removal menyebabkan latency tinggi karena buffer

### VB-Cable Tidak Terdeteksi
- Pastikan VB-Cable sudah terinstall
- Refresh device list dengan tombol "Refresh"
- Restart aplikasi setelah install VB-Cable

### Microphone Permission Error
- Buka Windows Settings > Privacy > Microphone
- Pastikan akses microphone diizinkan untuk Python/IDE yang digunakan

## Arsitektur

```
voiceforge/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── config/
│   └── settings.json        # Config & preset storage
├── core/
│   ├── audio_engine.py     # Capture & playback
│   └── processor.py        # Processing chain
├── ui/
│   ├── main_window.py      # Main window
│   ├── controls.py          # Control widgets
│   └── visualizer.py        # Waveform & level meter
└── presets/
    ├── defaults.py         # Built-in presets
    └── preset_manager.py   # Preset management
```

## Processing Chain

1. **Noise Gate** - Memotong suara saat tidak ada input
2. **Noise Removal** - Menghilangkan background noise
3. **Compressor** - Menstabilkan dynamic range
4. **10-Band EQ** - Fine-tune frekuensi suara
5. **Voice Enhancer** - Warmth, presence, de-esser
6. **Auto Leveler** - Automatic gain control
7. **Limiter** - Mencegah clipping di output

## Requirements

- Python 3.10+
- sounddevice
- numpy
- scipy
- noisereduce
- pedalboard
- PyQt6
- pyqtgraph
- psutil

## License

MIT License
