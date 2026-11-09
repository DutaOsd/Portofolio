# 8 Ball Pool Aim Assistant (Versi Canggih)

Alat bantu bermain **8 Ball Pool di Windows** dengan **deteksi bola otomatis** (computer vision), **garis panduan aim**, dan **prediksi arah pantulan bola** ke lubang.

Ini adalah versi modern dan lebih canggih dari program asli (C# / WinForms) — ditulis dalam **Python + OpenCV** agar deteksi bola dilakukan otomatis oleh kamera layar, tanpa perlu menargetkan bola secara manual.

## Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🔍 Deteksi Bola Otomatis | Deteksi bola pukul (putih) dan bola target (warna) secara otomatis via OpenCV (HSV color segmentation + HoughCircles). |
| 🎯 Garis Panduan Aim | Gambar garis dari bola pukul ke bola target secara real-time. |
| 👻 Ghost Ball | Menghitung posisi ideal bola pukul (ghost ball) agar bola target tercelok ke lubang. |
| ↗️ Prediksi Pantulan (Bounce) | Menghitung arah pantulan bola setelah mengenai tali (cushion) hingga 3 pantulan. |
| 🕳️ Deteksi Lubang | Deteksi otomatis posisi lubang meja bilhar. |
| 🖥️ Overlay Real-time | Jendela translucent yang menempel di atas layar game. |
| ⚙️ Konfigurasi | Semua parameter diatur melalui `config.json`. |

## Teknologi

- **Python 3.10+**
- **OpenCV** — deteksi bola, warna, dan garis
- **NumPy** — perhitungan vektor & fisika pantulan
- **mss** — tangkap layar cepat
- **tkinter + Pillow** — jendela overlay
- **Pilihan bahasa**: Code komentar & struktur dalam English; dokumentasi dalam Bahasa Indonesia

## Struktur Proyek

```
8ball-pool-aim-assistant/
├── main.py                 # Entry point (tangkap -> deteksi -> fisika -> tampil)
├── config.json             # Pengaturan deteksi, fisika, dan overlay
├── requirements.txt        # Dependensi Python
├── README.md
└── core/
    ├── __init__.py
    ├── capture.py          # Screen capture (mss)
    ├── detector.py         # Deteksi bola & lubang (OpenCV)
    ├── physics.py          # Garis aim, ghost ball, pantulan tali
    └── overlay.py          # Jendela tampilan real-time (tkinter)
```

## Cara Install & Jalankan

### 1. Clone / buka folder proyek
```bash
cd /home/user/Portofolio/8ball-pool-aim-assistant
```

### 2. Buat virtual environment dan install dependensi
```bash
python -m venv venv
source venv/bin/activate     # Linux/Mac: source venv/bin/activate
# Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Jalankan program
```bash
python main.py
```

### 4. Cara pakai
1. Buka game 8 Ball Pool di browser atau aplikasi Windows.
2. Jalankan `python main.py` — jendela overlay muncul di atas layar.
3. Posisikan jendela game agar meja bilhar terlihat jelas di layar.
4. Program akan otomatis mendeteksi:
   - **Bola putih (bola pukul)** → ditandai hijau
   - **Bola target (warna)** → ditandai kuning
   - **Lubang meja** → ditandai merah
5. Garis panduan akan muncul dari bola pukul ke bola target, serta prediksi jalur pantulan ke lubang terbaik.
6. Tekan **`q`** atau tutup jendela untuk keluar.

## Prediksi Pantulan Bola (Bounce)

Program menggunakan prinsip fisika refleksi: **sudut jatuh = sudut pantulan**. Jika bola target tidak langsung ke lubang, program menghitung jalur setelah bersentuhan dengan tali (cushion) hingga maksimum 3 kali pantulan, lalu menampilkan jalur yang diestimasi pada overlay.

## Konfigurasi (`config.json`)

```json
{
  "capture": { "monitor": 1, "fps": 30 },
  "detection": {
    "min_ball_radius": 8,
    "max_ball_radius": 40
  },
  "physics": {
    "max_bounces": 3,
    "aim_line_length": 250
  },
  "overlay": {
    "always_on_top": true,
    "opacity": 0.85
  }
}
```

- `monitor`: nomor monitor yang di-tangkap (1 = utama).
- `max_bounces`: banyaknya pantulan tali yang dihitung.
- `opacity`: transparansi jendela overlay.

## Perbedaan dengan Versi Asli (C# WinForms)

| Aspek | Versi Asli | Versi Ini |
|-------|-----------|-----------|
| Deteksi bola | Manual (user geser bola referensi) | **Otomatis via OpenCV** |
| Prediksi lubang | Tidak ada | **Ada (ghost ball + pocket)** |
| Prediksi pantulan | Tidak ada | **Ada (fisika refleksi tali)** |
| Bahasa | C# 7.3 / .NET 4.8 | **Python 3 + OpenCV** |
| Platform | Hanya Windows | **Cross-platform (Python)** |
| Tampilan | WinForms | **Overlay real-time (tkinter)** |

## Lisensi

Dibuat untuk portofolio pembelajaran. Gunakan sesuai hukum dan ketentuan layanan game yang dimainkan.

---

Dibuat oleh **DutaOsd** — Portofolio Proyek