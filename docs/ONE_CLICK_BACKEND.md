# Installer backend CPU sekali jalan

## Windows

Klik dua kali `INSTALL_BACKEND.cmd` dari folder repository. Tidak perlu memasang Python atau Node.js terlebih dahulu. Installer memakai uv dari sumber resmi Astral untuk menyediakan Python 3.12, lalu membuat environment CPU lokal. Jika jaringan/policy organisasi memblokir installer uv, pasang uv dari sumber resmi dengan bantuan administrator; script tidak mengubah execution policy Windows.

Saat selesai akan muncul `READY` dan URL `/docs`, `/health`, `/ready`. Biarkan terminal terbuka. Gunakan Ctrl+C untuk berhenti. Untuk menjalankan lagi tanpa instalasi: klik `START_BACKEND.cmd`.

## Linux (Ubuntu/Debian x86-64)

```sh
cd /path/to/activity-lab
bash install_backend.sh
```

Butuh bash dan curl. Jika curl belum ada: `sudo apt-get update` lalu `sudo apt-get install curl`. Library OpenCV/MediaPipe pada host apt akan dipasang bila belum ada; sudo dapat meminta password. Python dikelola uv di akun yang menjalankan installer. Jangan menjalankan seluruh installer dengan sudo bila tidak diperlukan.

```sh
bash start_backend.sh
```

Distro lain perlu library ekuivalen libGL dan GLib. Kompatibilitas container/Linux belum diverifikasi end-to-end pada host tujuan; script berhenti jika instalasi atau model gagal, bukan menampilkan sukses palsu.

## Tahapan otomatis

1. Bootstrap uv dari `https://astral.sh/uv/install.ps1` atau `install.sh` jika belum tersedia.
2. Sediakan Python 3.12 menggunakan uv; environment `.venv-backend-cpu` terpisah dari environment training/GPU.
3. Pasang PyTorch/torchvision CPU dan `requirements.txt`; jalankan dependency check.
4. Verifikasi hash dan impor ANN dari `trained-models/baseline`.
5. Unduh checkpoint publik YOLO/MediaPipe/X-CLIP (revision dipin), verifikasi checksum model yang memiliki manifest.
6. Buat `.env` jika belum ada. File yang sudah ada dipertahankan.
7. Jalankan satu worker, paksa `DEVICE=cpu`, default `MAX_INFLIGHT=1`, lalu tunggu semua model ready maksimal 10 menit. Jika port terpakai, tidak menghentikan aplikasi pemilik port.

Internet diperlukan pada setup pertama; waktu dan ruang disk bergantung koneksi/dependencies. X-CLIP sendiri sekitar 780 MB. Rerun menggunakan environment dan cache yang tersedia; tidak menghapus model atau data pengguna.

## Opsi

```sh
# Pasang saja, tidak menjalankan server
bash install_backend.sh --install-only
# Windows:
INSTALL_BACKEND.cmd --install-only
```

`--dry-run` pada installer Python memperlihatkan rencana tanpa membuat environment/config atau memasang dependency. Wrapper shell masih dapat melakukan bootstrap uv/Python atau pengecekan library sebelum memanggil Python; gunakan Python langsung jika ingin dry-run sepenuhnya tanpa perubahan.

Backend berjalan di foreground; bukan service systemd/Windows Service. Tidak ada autostart atau otomatis hidup setelah reboot. Untuk deployment permanen, gunakan Compose dengan restart policy atau service manager yang dikonfigurasi administrator.

## Menghubungkan website

Default backend mendengarkan `127.0.0.1:8765`. Website pada server/perangkat yang sama dapat memakai URL ini. Untuk frontend Vercel atau pengunjung dari perangkat lain, backend memerlukan domain HTTPS dan gateway autentikasi. Sesuaikan `ALLOWED_ORIGINS` dalam `.env` dengan domain frontend dan `NEXT_PUBLIC_INFERENCE_URL` saat build frontend. Jangan membuka port publik sebagai pengganti HTTPS/auth.

Sumber bootstrap resmi: [uv installation](https://docs.astral.sh/uv/getting-started/installation/) dan [managed Python](https://docs.astral.sh/uv/guides/install-python/).

## Bukti pengujian paket

Logika installer diuji dengan unit test: config lama dipertahankan, default CPU/loopback, rencana dependency CPU, impor ANN, serta environment tidak dibuat ulang. Dry-run Python dan validasi sintaks dijalankan. Instalasi penuh pada server i7 gen 7/16 GB belum diuji; tidak ada klaim latensi/kapasitas server sebelum pengukuran aktual.

## Error cv2 / GStreamerPipeline

MediaPipe meminta opencv-contrib-python sedangkan Ultralytics meminta opencv-python. Keduanya memakai namespace cv2; memasang versi berbeda dapat mencampur wrapper Python dan binary. Installer kini mengecualikan wheel base/headless dan memakai contrib sebagai penyedia API OpenCV.

Pada Windows, setelah update repository, klik `REPAIR_OPENCV.cmd`, lalu `START_BACKEND.cmd`. Linux: `bash install_backend.sh --repair-opencv`, lalu `bash start_backend.sh`. Model dan konfigurasi tidak dihapus.

Pemeriksaan memakai `scripts/check_dependencies.py`: seluruh dependency diperiksa, dengan substitusi khusus opencv-python → opencv-contrib-python. `uv pip check` biasa dapat melaporkan nama opencv-python tidak terpasang walaupun API cv2 tersedia melalui contrib; jangan memperbaikinya dengan memasang varian kedua. Sumber: https://pypi.org/project/opencv-python/.
