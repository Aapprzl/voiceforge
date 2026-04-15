# VoiceForge — Panduan Pembangunan App untuk Agent AI

---

## INTRO: Apa yang Sedang Kita Bangun

Kamu adalah engineer yang bertugas membangun **VoiceForge** — sebuah aplikasi desktop Python yang berfungsi sebagai **real-time audio processor** khusus untuk mikrofon.

**Masalah yang dipecahkan:** Pengguna melakukan recording dan streaming menggunakan OBS dengan mikrofon kualitas rendah (built-in laptop, headset murah). Kualitas suara hasilnya buruk — ada noise background, suara tipis, volume tidak stabil.

**Solusi yang dibangun:** VoiceForge duduk di antara mikrofon fisik dan OBS. App ini menangkap audio dari mic asli, memprosesnya secara real-time dengan berbagai teknik audio engineering, lalu mengeluarkan hasilnya melalui virtual microphone device yang bisa dipilih di OBS persis seperti mic biasa.

**Stack teknologi:**
- Bahasa: Python 3.10+
- Audio engine: `sounddevice` + `numpy`
- Audio processing: `scipy`, `noisereduce`, `pedalboard`
- Virtual device: VB-Audio Virtual Cable (driver Windows, user install manual)
- UI: `PyQt6`
- Config: JSON file
- Packaging: `pyinstaller` (opsional, tahap akhir)

**Hasil akhir yang diharapkan:** Satu aplikasi desktop Windows yang bisa dibuka, memilih mic input, memilih virtual output, mengatur semua parameter audio secara real-time, menyimpan preset, dan terdeteksi oleh OBS sebagai microphone.

**Target perangkat:** ASUS ZenBook, AMD Ryzen 5 5500U, RAM 8GB, Windows 11. App harus ringan dan efisien.

---

## PENTING SEBELUM MULAI

Sebelum mengeksekusi tahapan apapun, baca seluruh dokumen ini sampai selesai terlebih dahulu agar kamu memahami gambaran besar keseluruhan proyek.

Setiap tahapan harus diselesaikan dan diverifikasi benar sebelum lanjut ke tahapan berikutnya. Jika ada error, perbaiki di tahapan yang sama sebelum melanjutkan.

---

## STRUKTUR FOLDER PROYEK

```
voiceforge/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── config/
│   └── settings.json        # Config & preset storage
├── core/
│   ├── __init__.py
│   ├── audio_engine.py      # Capture & playback engine
│   └── processor.py         # Semua processing chain
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # Jendela utama
│   ├── controls.py          # Slider, knob, toggle widgets
│   └── visualizer.py        # Waveform & level meter
└── presets/
    └── defaults.py          # Built-in preset definitions
```

---

# TAHAPAN PEMBANGUNAN

---

## TAHAP 1 — Setup Proyek & Dependencies

**Tujuan:** Membuat struktur folder dan file requirements yang siap digunakan.

**Instruksi:**

Buat struktur folder proyek seperti yang tertera di atas. Semua folder dan file harus ada meskipun masih kosong.

Buat file `requirements.txt` dengan isi berikut:
```
sounddevice==0.4.6
numpy==1.26.4
scipy==1.13.0
noisereduce==3.0.2
pedalboard==0.9.9
PyQt6==6.7.0
pyqtgraph==0.13.7
```

Buat file `config/settings.json` dengan struktur awal:
```json
{
  "input_device": null,
  "output_device": null,
  "active_preset": "streaming",
  "presets": {}
}
```

**Verifikasi:** Pastikan semua folder dan file sudah ada. Jalankan `pip install -r requirements.txt` dan pastikan tidak ada error.

---

## TAHAP 2 — Audio Engine: Capture & Routing Dasar

**Tujuan:** Membuat engine yang bisa menangkap audio dari mic input dan mengeluarkannya ke virtual device output.

**File yang dibuat/diedit:** `core/audio_engine.py`

**Instruksi:**

Buat class `AudioEngine` dengan kemampuan berikut:

1. Method `list_devices()` — mengembalikan list semua audio device yang tersedia di sistem (input dan output secara terpisah).

2. Method `start(input_device_index, output_device_index, callback_fn)` — membuka stream audio dari device input dan device output secara bersamaan menggunakan `sounddevice.Stream`. Setiap chunk audio yang masuk (buffer) langsung dikirim ke `callback_fn` untuk diproses, kemudian output dari callback langsung diteruskan ke output device.

3. Method `stop()` — menghentikan stream dengan aman.

4. Attribute `is_running` — boolean status apakah stream sedang aktif.

Parameter stream yang digunakan: sample rate 44100 Hz, channels 1 (mono), dtype float32, blocksize 512.

**Verifikasi:** Buat script test sederhana yang memanggil `list_devices()` dan print hasilnya. Pastikan device-device audio yang ada di sistem muncul.

---

## TAHAP 3 — Processor: Noise Gate

**Tujuan:** Membangun komponen pertama processing chain — noise gate yang memotong suara saat tidak ada input.

**File yang dibuat/diedit:** `core/processor.py`

**Instruksi:**

Buat class `AudioProcessor` yang memiliki attribute `chain` berupa list dari processing steps yang akan dijalankan berurutan.

Implementasikan komponen `NoiseGate`:
- Threshold dalam dB (range: -80 dB sampai 0 dB, default: -40 dB)
- Attack time: waktu gate terbuka saat suara muncul (default: 10ms)
- Release time: waktu gate menutup saat suara hilang (default: 100ms)
- Cara kerja: hitung RMS dari audio chunk, jika di bawah threshold maka output adalah silence (numpy zeros), jika di atas threshold maka audio dilewatkan.
- Gate tidak langsung on/off tetapi smooth menggunakan envelope follower untuk menghindari clicking artifact.

Buat method `process(audio_chunk)` di `AudioProcessor` yang menjalankan audio chunk melewati seluruh komponen dalam `chain` secara berurutan dan mengembalikan hasilnya.

**Verifikasi:** Buat unit test: generate sinyal sine wave dengan beberapa bagian silence, jalankan melalui `NoiseGate`, pastikan bagian silence di-cut dan sinyal asli dilewatkan.

---

## TAHAP 4 — Processor: Noise Removal

**Tujuan:** Membangun komponen penghilang background noise menggunakan spectral subtraction.

**File yang dibuat/diedit:** `core/processor.py`

**Instruksi:**

Tambahkan class `NoiseRemoval` ke dalam `processor.py`:

- Gunakan library `noisereduce` dengan mode `stationary=False` (untuk noise yang berubah-ubah seperti kipas laptop).
- Strength parameter (0.0 sampai 1.0, default: 0.75) yang mengontrol seberapa agresif noise dihilangkan.
- Karena `noisereduce` bekerja paling baik pada chunk yang cukup panjang, implementasikan buffer internal: kumpulkan beberapa chunk (minimal 0.5 detik audio), proses, lalu kembalikan hasilnya. Ini mengorbankan sedikit latency tapi menghasilkan noise removal yang jauh lebih baik.
- Tambahkan `NoiseRemoval` ke dalam chain di `AudioProcessor`.

**Verifikasi:** Buat test dengan audio yang mengandung white noise + sine wave. Jalankan melalui `NoiseRemoval`. Pastikan noise berkurang tanpa merusak sinyal utama.

---

## TAHAP 5 — Processor: Compressor & Auto-Leveling

**Tujuan:** Membangun dynamic range compressor dan automatic gain control untuk stabilkan volume.

**File yang dibuat/diedit:** `core/processor.py`

**Instruksi:**

Tambahkan class `Compressor`:
- Parameter: `threshold_db` (default: -20 dB), `ratio` (default: 4.0), `attack_ms` (default: 5 ms), `release_ms` (default: 100 ms), `knee_db` (default: 6 dB — soft knee untuk suara natural).
- Gunakan `pedalboard.Compressor` dari Spotify Pedalboard library untuk implementasi yang sudah teruji dan efisien.
- Makeup gain otomatis: setelah compression, naikkan gain untuk mengembalikan level ke -12 dBFS target.

Tambahkan class `AutoLeveler` (AGC — Automatic Gain Control):
- Pantau level output rata-rata dalam window 2 detik.
- Jika level terlalu pelan dari target (-18 dBFS), naikkan gain secara perlahan.
- Jika level terlalu keras (mendekati 0 dBFS), turunkan gain segera.
- Perubahan gain smooth (tidak mendadak) untuk menghindari pumping effect.
- Bisa di-enable/disable.

Tambahkan kedua komponen ke `chain` di `AudioProcessor`.

**Verifikasi:** Test dengan sinyal yang volume-nya berubah-ubah. Pastikan output volume lebih konsisten.

---

## TAHAP 6 — Processor: 10-Band EQ & Voice Enhancement

**Tujuan:** Membangun equalizer 10-band dan voice enhancer untuk memperindah karakter suara.

**File yang dibuat/diedit:** `core/processor.py`

**Instruksi:**

Tambahkan class `Equalizer10Band`:
- 10 band standar: 31Hz, 63Hz, 125Hz, 250Hz, 500Hz, 1kHz, 2kHz, 4kHz, 8kHz, 16kHz.
- Setiap band memiliki gain dalam dB (range: -12 dB sampai +12 dB, default: 0 dB).
- Implementasi menggunakan `scipy.signal.iirpeak` dan `scipy.signal.sosfilt` untuk efisiensi.
- Method `set_band(band_index, gain_db)` untuk mengubah gain satu band.

Tambahkan class `VoiceEnhancer`:
- **Warmth:** Boost slight pada 200-300 Hz untuk suara lebih penuh.
- **Presence:** Boost pada 3-5 kHz untuk kejelasan dan ketajaman suara (area paling sensitif telinga manusia).
- **De-esser:** High-frequency compressor yang spesifik hanya bekerja pada range 6-9 kHz untuk mengurangi bunyi "S" dan "T" yang terlalu tajam.
- **Harmonic enhancement:** Tambahkan sedikit harmonic saturation untuk suara lebih "hangat" — gunakan soft clipping ringan (tanh function dengan gain rendah).
- Setiap komponen bisa toggle on/off dan memiliki intensity parameter (0.0 - 1.0).

Tambahkan kedua komponen ke `chain`.

**Verifikasi:** Test dengan rekaman suara (atau sine wave di berbagai frekuensi). Pastikan tidak ada distorsi berlebihan pada intensity rendah.

---

## TAHAP 7 — Processor: Limiter & Final Output Stage

**Tujuan:** Membangun limiter sebagai safeguard terakhir dan menyempurnakan output chain.

**File yang dibuat/diedit:** `core/processor.py`

**Instruksi:**

Tambahkan class `Limiter`:
- Hard ceiling di -1 dBFS (tidak boleh ada sample yang melebihi ini).
- Gunakan `pedalboard.Limiter` dari Pedalboard library.
- Release time: 50ms.
- Tujuan: mencegah clipping dan distorsi keras di output akhir.

Rapikan urutan `chain` di `AudioProcessor` menjadi:
1. NoiseGate
2. NoiseRemoval
3. Compressor
4. Equalizer10Band
5. VoiceEnhancer
6. AutoLeveler
7. Limiter

Tambahkan method `get_output_level()` yang mengembalikan level output terakhir dalam dB (untuk ditampilkan di UI meter).

Tambahkan method `get_params()` dan `set_params(params_dict)` untuk mendapatkan dan mengatur semua parameter sekaligus (diperlukan untuk preset system).

**Verifikasi:** Jalankan processor lengkap dengan test audio. Pastikan tidak ada crash dan output tidak clipping.

---

## TAHAP 8 — Preset System

**Tujuan:** Membangun sistem preset bawaan dan custom preset dengan penyimpanan ke file.

**File yang dibuat/diedit:** `presets/defaults.py`, `config/settings.json`

**Instruksi:**

Di `presets/defaults.py`, definisikan 3 preset bawaan sebagai dictionary Python:

**Preset "Streaming":** Noise gate agresif (-35 dB), noise removal tinggi (0.8), compressor ratio 4:1, EQ boost di 2kHz dan 4kHz untuk kejelasan, voice presence tinggi. Cocok untuk streaming gaming.

**Preset "Podcast":** Noise gate moderat (-45 dB), noise removal medium (0.6), compressor ratio 3:1 dengan attack lebih lambat, EQ boost di 200Hz untuk warmth + boost 3kHz untuk kejelasan, de-esser aktif. Cocok untuk konten bicara panjang.

**Preset "Gaming":** Noise gate ketat (-30 dB), noise removal rendah (0.4) untuk latency minimum, compressor ringan, EQ flat dengan sedikit boost 1kHz. Prioritas latency rendah.

Buat class `PresetManager`:
- Method `load_defaults()` — memuat 3 preset bawaan ke memory.
- Method `save_preset(name, params)` — menyimpan preset custom ke `config/settings.json`.
- Method `load_preset(name)` — memuat preset (bawaan atau custom) dan mengembalikan params dict.
- Method `delete_preset(name)` — hapus preset custom (preset bawaan tidak bisa dihapus).
- Method `list_presets()` — kembalikan list semua preset yang tersedia.

**Verifikasi:** Test load/save/delete preset. Pastikan settings.json diperbarui dengan benar.

---

## TAHAP 9 — UI: Jendela Utama & Layout

**Tujuan:** Membangun kerangka UI utama dengan PyQt6.

**File yang dibuat/diedit:** `ui/main_window.py`, `main.py`

**Instruksi:**

Buat `MainWindow` (QMainWindow) dengan desain berikut:

**Ukuran jendela:** 900 x 600 pixel, tidak bisa di-resize (fixed size untuk konsistensi layout).

**Layout:** Tiga panel horizontal:
- Panel kiri (220px): Device selector + Preset manager
- Panel tengah (440px): Processing controls (tabs)
- Panel kanan (240px): Visualizer (waveform + level meter)

**Header bar** di atas (tinggi 50px): Logo/nama app "VoiceForge" di kiri, status indicator (titik hijau/merah + teks "LIVE" atau "STOPPED") di tengah, tombol power besar di kanan untuk start/stop.

**Footer bar** di bawah (tinggi 30px): Teks status kecil seperti latency, sample rate, status device.

**Visual style:** Background gelap (#1a1a1a), panel sedikit lebih terang (#242424), accent color hijau (#2ecc71) untuk elemen aktif. Font: sistem default. Tidak ada efek bayangan atau gradient berlebihan.

Di `main.py`, buat entry point yang menginisialisasi QApplication dan menampilkan MainWindow.

**Verifikasi:** Jalankan `python main.py`. Pastikan jendela muncul dengan layout yang benar.

---

## TAHAP 10 — UI: Device Selector & Status Panel

**Tujuan:** Membangun panel pemilihan device input/output dan status koneksi.

**File yang dibuat/diedit:** `ui/controls.py`, `ui/main_window.py`

**Instruksi:**

Di panel kiri, tambahkan:

**Device Selector:**
- Label "Input Device" + dropdown (QComboBox) berisi semua audio input device dari `AudioEngine.list_devices()`.
- Label "Output Device" + dropdown berisi semua audio output device.
- Tombol "Refresh" untuk memperbarui list device.
- Saat output device dipilih, tampilkan pesan kecil jika VB-Cable tidak terdeteksi: "VB-Cable not found. Install from vb-audio.com".

**Connection Status:**
- Indicator visual (lingkaran kecil) dengan warna: hijau = connected dan streaming, kuning = ready tapi tidak streaming, merah = error.
- Teks status di bawahnya.

Hubungkan device selector dengan `AudioEngine` — saat tombol power ditekan, engine start menggunakan device yang dipilih.

**Verifikasi:** Device yang ada di sistem muncul di dropdown. Tombol power mengubah status indicator.

---

## TAHAP 11 — UI: Preset Manager Panel

**Tujuan:** Membangun UI untuk memilih, menyimpan, dan mengelola preset.

**File yang dibuat/diedit:** `ui/controls.py`, `ui/main_window.py`

**Instruksi:**

Di panel kiri (di bawah device selector), tambahkan:

**Preset Section:**
- Label "Preset"
- Dropdown berisi semua preset (bawaan + custom). Preset bawaan ditampilkan pertama dengan separator sebelum preset custom.
- Saat preset dipilih dari dropdown, semua parameter di panel tengah langsung berubah mengikuti preset tersebut.
- Tombol "Save as..." — membuka dialog input nama preset, lalu menyimpan setting saat ini sebagai preset baru.
- Tombol "Delete" — menghapus preset custom yang sedang dipilih (disabled untuk preset bawaan).

Saat semua UI sudah siap, pastikan perubahan parameter di panel tengah tidak otomatis mengubah preset yang sedang dipilih (preset hanya ter-apply saat dipilih dari dropdown, bukan saat user mengubah slider).

**Verifikasi:** Pilih preset, semua slider berubah. Save preset baru, muncul di dropdown. Delete preset custom, hilang dari dropdown.

---

## TAHAP 12 — UI: Processing Controls — Tab Noise & Dynamics

**Tujuan:** Membangun tab control untuk NoiseGate, NoiseRemoval, dan Compressor.

**File yang dibuat/diedit:** `ui/controls.py`, `ui/main_window.py`

**Instruksi:**

Panel tengah menggunakan QTabWidget dengan 3 tab: "Noise & Gate", "EQ", "Voice".

Di tab **"Noise & Gate"**, buat control berikut:

**Noise Gate section:**
- Toggle on/off
- Slider "Threshold": -80 dB sampai 0 dB, tampilkan nilai saat ini di sebelah slider
- Slider "Attack": 1ms sampai 100ms
- Slider "Release": 10ms sampai 1000ms

**Noise Removal section:**
- Toggle on/off
- Slider "Strength": 0% sampai 100%

**Compressor section:**
- Toggle on/off
- Slider "Threshold": -40 dB sampai 0 dB
- Slider "Ratio": 1:1 sampai 10:1
- Slider "Attack": 1ms sampai 100ms
- Slider "Release": 10ms sampai 500ms

Setiap perubahan slider langsung dikirim ke `AudioProcessor.set_params()` secara real-time tanpa perlu tombol Apply.

**Verifikasi:** Slider bisa digeser, nilai berubah, dan tidak ada crash.

---

## TAHAP 13 — UI: Processing Controls — Tab EQ

**Tujuan:** Membangun 10-band equalizer dengan visual representation.

**File yang dibuat/diedit:** `ui/controls.py`

**Instruksi:**

Di tab **"EQ"**:

Tampilkan 10 slider vertikal berjajar horizontal, masing-masing untuk satu frekuensi band:
31Hz | 63Hz | 125Hz | 250Hz | 500Hz | 1kHz | 2kHz | 4kHz | 8kHz | 16kHz

Setiap slider vertikal:
- Range: -12 dB sampai +12 dB
- Default: 0 dB (posisi tengah)
- Label frekuensi di bawah slider
- Nilai dB saat ini di atas slider
- Garis horizontal tipis di posisi 0 dB sebagai referensi

Tambahkan tombol "Reset EQ" yang mengembalikan semua band ke 0 dB.

Gunakan QDial atau QSlider vertikal dengan orientasi Qt.Vertical.

**Verifikasi:** 10 slider muncul, bisa digeser, nilai tampil dengan benar, reset berfungsi.

---

## TAHAP 14 — UI: Processing Controls — Tab Voice

**Tujuan:** Membangun control untuk VoiceEnhancer dan AutoLeveler.

**File yang dibuat/diedit:** `ui/controls.py`

**Instruksi:**

Di tab **"Voice"**:

**Voice Enhancer section:**
- Toggle master on/off untuk seluruh voice enhancer
- Slider "Warmth": 0% sampai 100% (dengan label penjelasan singkat: "Adds body to low-mids")
- Slider "Presence": 0% sampai 100% ("Clarity boost at 3-5kHz")
- Toggle "De-esser": on/off + slider intensity 0-100%
- Toggle "Harmonic warmth": on/off + slider intensity 0-100%

**Auto-Leveling section:**
- Toggle on/off
- Label "Target level: -18 dBFS" (informational, tidak bisa diubah user)
- Indicator kecil: teks "Gaining up" atau "Reducing" yang berubah real-time sesuai kondisi AGC

**Limiter section:**
- Toggle on/off
- Label "Ceiling: -1 dBFS" (fixed, tidak bisa diubah)
- Indicator merah kecil yang menyala sesaat saat limiter aktif bekerja (limiting detected)

**Verifikasi:** Semua toggle dan slider berfungsi. Indicator limiter bisa ditest dengan signal keras.

---

## TAHAP 15 — UI: Real-time Waveform Visualizer

**Tujuan:** Membangun visualizer waveform dan level meter yang update secara real-time.

**File yang dibuat/diedit:** `ui/visualizer.py`

**Instruksi:**

Di panel kanan, buat dua komponen visual:

**Waveform display** (2/3 tinggi panel):
- Gunakan `pyqtgraph.PlotWidget` untuk efisiensi rendering.
- Tampilkan waveform audio output real-time (bukan input).
- Update rate: 30 fps.
- X-axis: waktu (0.5 detik window).
- Y-axis: amplitude -1.0 sampai 1.0, fixed range.
- Warna garis: hijau (#2ecc71) pada background gelap.
- Tidak ada axis label, tidak ada grid, tidak ada border berlebihan. Minimalis.

**Level meter** (1/3 tinggi panel):
- Meter vertikal yang menunjukkan level output dalam dB.
- Range: -60 dB sampai 0 dB.
- Warna: hijau untuk -60 sampai -12 dB, kuning untuk -12 sampai -6 dB, merah untuk -6 sampai 0 dB.
- Update rate: 30 fps.
- Peak indicator: garis kecil yang menahan posisi peak selama 2 detik sebelum turun.
- Label dB di sisi kanan: -60, -40, -20, -12, -6, 0.

Buat class `AudioVisualizer` yang menerima data audio chunk dan memperbarui kedua komponen.

**Verifikasi:** Waveform bergerak saat ada suara input. Level meter naik turun mengikuti level suara.

---

## TAHAP 16 — Integrasi Penuh: Hubungkan Semua Komponen

**Tujuan:** Menghubungkan AudioEngine, AudioProcessor, PresetManager, dan seluruh UI menjadi satu sistem yang berfungsi.

**File yang dibuat/diedit:** `ui/main_window.py`, `main.py`

**Instruksi:**

Di `MainWindow`, lakukan integrasi berikut:

1. Saat app dibuka, inisialisasi `AudioEngine`, `AudioProcessor`, dan `PresetManager`.

2. Load preset terakhir yang digunakan dari `settings.json`, apply ke `AudioProcessor`, dan tampilkan di semua slider.

3. Saat tombol power ditekan (start):
   - Ambil device yang dipilih dari dropdown.
   - Panggil `AudioEngine.start()` dengan callback yang mengirim audio ke `AudioProcessor.process()`.
   - Output dari processor dikirim ke output device.
   - Output juga dikirim ke `AudioVisualizer` untuk ditampilkan.
   - Update status indicator menjadi hijau "LIVE".

4. Saat tombol power ditekan lagi (stop):
   - Panggil `AudioEngine.stop()`.
   - Update status indicator.

5. Setiap perubahan slider langsung update parameter di `AudioProcessor` tanpa delay.

6. Saat app ditutup, simpan device yang dipilih dan preset aktif ke `settings.json`.

7. Error handling: jika device tidak bisa dibuka (misalnya VB-Cable tidak terinstall), tampilkan pesan error di status bar dan status indicator merah.

**Verifikasi:** Buka app, pilih device, tekan power, bicara ke mic — suara harus keluar ke output device yang dipilih dengan processing aktif.

---

## TAHAP 17 — Latency Optimization & Performance Tuning

**Tujuan:** Memastikan app berjalan efisien tanpa memakan resource berlebihan di laptop user.

**File yang dibuat/diedit:** `core/audio_engine.py`, `core/processor.py`

**Instruksi:**

Lakukan optimasi berikut:

1. **Thread separation:** Pastikan audio processing berjalan di thread terpisah dari UI thread. Gunakan `QThread` atau Python thread untuk audio loop. UI tidak boleh pernah blocking audio processing.

2. **Buffer optimization:** Test dan dokumentasikan blocksize yang optimal. Default 512 samples (≈11.6ms latency pada 44100Hz). Jika noise removal buffer menyebabkan latency tinggi, tambahkan option di UI untuk menonaktifkan noise removal demi latency rendah (Gaming preset sudah set ini).

3. **CPU monitoring:** Tambahkan simple CPU usage monitor untuk audio thread. Tampilkan di footer bar sebagai teks kecil: "CPU: 12%". Gunakan `psutil` library.

4. **Memory:** Pastikan tidak ada memory leak — buffer harus dibersihkan dengan benar saat stream stop.

5. Tambahkan `psutil` ke `requirements.txt`.

**Verifikasi:** Jalankan app selama 10 menit. CPU usage audio thread tidak boleh melebihi 15% pada laptop Ryzen 5 5500U. Tidak ada memory terus naik.

---

## TAHAP 18 — Error Handling & Edge Cases

**Tujuan:** Membuat app robust terhadap kondisi error yang umum terjadi.

**File yang dibuat/diedit:** semua file yang relevan

**Instruksi:**

Handle kondisi error berikut dengan pesan yang jelas di UI:

1. **VB-Cable tidak terinstall:** Saat user memilih output device dan tidak ada virtual device, tampilkan warning dengan link ke vb-audio.com di status bar.

2. **Device disconnect:** Jika mic atau output device dicabut saat streaming, tangkap exception, stop engine, tampilkan error "Device disconnected. Please reconnect and restart." tanpa crash.

3. **Permission error:** Jika Windows memblokir akses ke microphone, tampilkan pesan yang memandu user ke Windows Settings > Privacy > Microphone.

4. **Config file corrupt:** Jika `settings.json` corrupt atau tidak bisa dibaca, reset ke default tanpa crash.

5. **Processing overflow:** Jika audio chunk mengandung NaN atau Inf (bisa terjadi saat device error), bersihkan dengan `numpy.nan_to_num()` sebelum output.

**Verifikasi:** Test setiap skenario error satu per satu. Pastikan app tidak crash dan pesan error mudah dipahami.

---

## TAHAP 19 — Testing End-to-End & Fine-Tuning Default Presets

**Tujuan:** Testing menyeluruh dan fine-tuning parameter preset agar hasilnya benar-benar bagus.

**Instruksi:**

1. Jalankan app lengkap dengan mic nyata (built-in laptop atau headset).

2. Test setiap preset:
   - Streaming: bicara normal, periksa apakah background noise hilang dan suara jernih.
   - Podcast: bicara panjang, periksa volume stabil dan suara hangat.
   - Gaming: periksa latency terasa minimal dan tidak ada delay.

3. Fine-tune nilai default preset berdasarkan hasil test jika diperlukan. Nilai yang perlu diperhatikan:
   - Noise gate threshold — jangan terlalu agresif sampai memotong kata-kata.
   - Noise removal strength — jangan terlalu kuat sampai suara jadi robotic.
   - Compressor ratio — jangan terlalu tinggi sampai suara terasa tercekik.
   - EQ presence boost — jangan terlalu tinggi sampai terasa harsh.

4. Test dengan OBS: pilih "VB-Cable Output" atau nama virtual device sebagai microphone source di OBS, bicara, pastikan level OBS naik dan suara terdengar bagus.

**Verifikasi:** Semua preset terdengar bagus dan natural. OBS mendeteksi virtual device.

---

## TAHAP 20 — Dokumentasi & Readme

**Tujuan:** Membuat dokumentasi singkat untuk pengguna.

**File yang dibuat:** `README.md`

**Instruksi:**

Buat file `README.md` berisi:

1. **Cara Install:**
   - Install Python 3.10+
   - Jalankan `pip install -r requirements.txt`
   - Download dan install VB-Audio Virtual Cable dari vb-audio.com (gratis)
   - Jalankan `python main.py`

2. **Cara Pakai:**
   - Pilih input device (mic kamu)
   - Pilih output device (pilih "CABLE Input (VB-Audio Virtual Cable)")
   - Tekan tombol power
   - Di OBS, set microphone source ke "CABLE Output (VB-Audio Virtual Cable)"

3. **Penjelasan singkat setiap preset** (3-4 kalimat per preset)

4. **Tips tuning** — kapan harus naikkan noise gate, kapan naikkan presence, dll.

**Verifikasi:** README bisa dipahami oleh pengguna non-teknis.

---

## CATATAN PENTING UNTUK AGENT

- Setiap tahap harus selesai dan tidak error sebelum lanjut ke tahap berikutnya.
- Jika ada library yang tidak bisa diinstall, cari alternatif yang setara dan dokumentasikan perubahannya.
- Prioritaskan stabilitas (tidak crash) di atas fitur tambahan.
- Jaga semua nama variabel dan komentar kode dalam bahasa Inggris untuk konsistensi.
- Semua UI text label boleh dalam bahasa Inggris.
- Jika ada ambiguitas dalam instruksi, pilih implementasi yang paling sederhana dan stabil.

---

*Dokumen ini dibuat sebagai blueprint oleh arsitek proyek. Total: 20 tahapan. Estimasi waktu per tahap: 10-30 menit tergantung kompleksitas.*
