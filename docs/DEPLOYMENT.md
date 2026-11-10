# Deployment

## Installer backend CPU

Gunakan `INSTALL_BACKEND.cmd` pada Windows atau `bash install_backend.sh` pada Linux. Installer mengatur environment CPU terpisah dan menjalankan backend di terminal, bukan service production/autostart. Lihat [panduan one-click](ONE_CLICK_BACKEND.md).

## Profil yang tersedia

| Profil | Frontend | Backend | Status |
|---|---|---|---|
| Lokal laptop | Next localhost | FastAPI localhost, CUDA/CPU | Diuji GPU pada laptop asal |
| Docker CPU | Next container | Python 3.12 CPU container | Konfigurasi disediakan, belum diuji container |
| NVIDIA Linux | Next/container | Torch CUDA pada server GPU | Panduan, belum diuji pada host Linux |
| Vercel + backend remote | Vercel | Host Python/GPU tersendiri | Perlu HTTPS + gateway auth; belum dideploy |

## Konfigurasi

| Variabel | Default | Keterangan |
|---|---|---|
| `DEVICE` | `auto` | `cpu`, `cuda`, atau pemilihan otomatis |
| `MODEL_DIR` | `backend/models` | Path absolut disarankan jika dipindahkan |
| `MAX_INFLIGHT` | `2` | Total job diterima; model tetap serial |
| `ALLOWED_ORIGINS` | localhost:3000 dan 127.0.0.1:3000 | Daftar origin dipisahkan koma; wildcard ditolak |
| `HOST` | `127.0.0.1` | `0.0.0.0` hanya dalam jaringan deployment yang dikendalikan |
| `PORT` | `8765` | Port backend |
| `NEXT_PUBLIC_INFERENCE_URL` | `http://127.0.0.1:8765` | **Build-time**, tanpa trailing slash; URL yang diakses browser |
| `DISABLE_MODEL_LOADING` | `0` | Hanya untuk unit/API test; readiness tidak siap |

`serve.py` membaca `.env` di root tanpa menjalankannya sebagai shell. Next membaca `web/.env.local`. Ubah URL API → rebuild frontend.

## CUDA

Pasang driver NVIDIA yang mendukung runtime pilihan. Untuk stack laptop yang telah diuji:

```sh
pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
pip install uv
uv pip install --python .venv -r requirements.txt --excludes requirements-exclude.txt
python scripts/check_dependencies.py
```

`requirements.windows.lock.txt` adalah snapshot environment Windows yang telah dipakai, termasuk paket transitif dan suffix CUDA. Jangan menganggapnya lock lintas OS; requirements utama memisahkan instalasi torch berdasarkan perangkat. CPU menggunakan FP32; GPU X-CLIP memakai FP16. `DEVICE=cpu` menyembunyikan CUDA sebelum impor torch agar Keras dan komponen lain juga menggunakan CPU. Gunakan wheel CPU pada host tanpa GPU untuk mengurangi ukuran instalasi.

## Docker CPU / reverse proxy

Jalankan dari root repository setelah checkpoint tersedia:

```sh
docker compose -f deploy/compose.yaml up --build
```

Akses `http://localhost:8080` untuk pengujian lokal. Nginx meneruskan `/api/` ke backend. Checkpoint di-mount read-only dan tidak masuk image. Docker menggunakan satu worker agar bobot dan state tidak diduplikasi. Tidak ada secret dalam build arg. Kamera browser jarak jauh memerlukan HTTPS.

Untuk akses publik, pasang TLS dan gateway autentikasi (misalnya OAuth proxy) di depan Nginx. Contoh Compose hanya mengikat port ke loopback sehingga tidak langsung mengekspos server ke jaringan. Jangan sekadar mengganti binding ke `0.0.0.0` tanpa gateway. CORS mengatur browser origin; **bukan autentikasi**.

## Vercel

Root Directory Vercel: **`web`**, Framework Preset: **Next.js**. File `web/vercel.json` sudah menetapkan build `npm run build` dan install `npm ci`.

Environment frontend sudah diisi di `web/.env.production` (ikut Git; hanya URL publik):

```env
NEXT_PUBLIC_INFERENCE_URL=https://activity-lab-api.tierkun.my.id
```

`web/.env.local` memakai URL yang sama untuk uji lokal, tetapi tetap ignored. Di dashboard Vercel, tambahkan variabel tersebut pada Production dan Preview jika ingin mengatur URL tanpa mengedit repository; nilai dashboard mengalahkan file. Setelah mengubah URL, redeploy karena NEXT_PUBLIC di-inline saat build.

Domain frontend yang disiapkan: **https://activity-lab.tierkun.com**. Tambahkan domain tersebut pada Settings → Domains di Vercel dan ikuti record DNS yang ditampilkan Vercel.

Di server Windows, jalankan **CONFIGURE_FRONTEND.cmd** setelah pull perubahan, lalu restart backend. Launcher menambahkan origin tanpa menghapus konfigurasi lain. Alternatif manual, ubah `.env` **di server backend**:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://activity-lab.tierkun.com
```

Ganti placeholder dengan origin frontend yang sebenarnya, tanpa path atau trailing slash. Restart backend. Domain preview Vercel berbeda juga memerlukan izin origin sendiri; wildcard tidak dipakai. Health API yang berhasil dibuka langsung bukan bukti CORS frontend sudah benar.

Commit/push perubahan, import repository di Vercel, pilih Root Directory `web`, lalu deploy. Backend tetap berjalan pada server Python/GPU; tidak dipindah ke fungsi Vercel. Tambahkan origin Vercel yang tepat ke `ALLOWED_ORIGINS`. Jangan menggunakan localhost pada build frontend publik: localhost menunjuk perangkat pengunjung. Backend HTTP juga akan diblokir mixed content bila frontend HTTPS.

## Operasi

- `/health`: liveness dan status tiap model; `ok:true` tidak berarti semua model siap.
- `/ready`: 200 jika ANN dan hybrid siap, 503 lainnya. Periksa `body_action_available` untuk X-CLIP.
- Satu worker per backend, lock serial, 429 saat overload. Skalakan dengan instance/GPU tersendiri dan session affinity; state belum terdistribusi.
- Reverse proxy membatasi body dan timeout; cocokkan dengan batas aplikasi 6 MB. Hindari logging body kamera.
- Tambahkan monitoring durasi end-to-end p50/p95, memori/VRAM, 429/5xx, restart/OOM, dan readiness sebelum rollout.
- Tidak ada SLO/kapasitas multi-user yang telah dibuktikan. Load test dan validasi domain tujuan wajib sebelum klaim production.

Referensi: [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/), [workers](https://fastapi.tiangolo.com/deployment/server-workers/), [containers](https://fastapi.tiangolo.com/deployment/docker/).
