# Kontribusi

Gunakan Python 3.12 dan Node.js 22/24. Jalankan unit/API test serta production build sebelum pull request. Perubahan preprocessing ANN harus dipisahkan sebagai eksperimen baru; jangan mengganti checkpoint baseline diam-diam.

Cache X-CLIP bergantung pada internal Transformers 4.57.3. Saat mengganti versi, jalankan parity test terhadap forward asli. Jangan memotong prompt generator demi menurunkan latensi tanpa mencatat perubahan model dan mengevaluasi hasilnya.

Jangan commit checkpoint runtime tambahan, video kamera, dataset, `.env`, token, atau log pengguna. Checkpoint publik hanya di `trained-models/` dan harus terdaftar beserta hash di manifest. Gunakan `python scripts/check_release.py`. Tambahkan sumber/lisensi untuk model baru, hasil evaluasi yang dapat direproduksi, serta batasan yang relevan. Jangan menyebut heuristik sebagai model terlatih atau skor sebagai keyakinan terkalibrasi.
