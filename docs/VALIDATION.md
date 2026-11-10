# Verifikasi dan batas pengujian

Pengujian lokal pada 10 November 2026: Windows, Python 3.12.14, RTX 5070 Laptop GPU 8 GB. Ini hasil verifikasi fungsi, **bukan benchmark akurasi atau sertifikasi production**.

| Pemeriksaan | Hasil |
|---|---|
| Next.js production build + TypeScript | Lolos; `/` dan `/live` dibangun |
| Unit/API/installer tests | 16 tes lolos; termasuk installer CPU dan substitusi provider OpenCV |
| X-CLIP cache parity | Selisih maksimum logit **0.0** terhadap full forward pada 32 frame sintetis, 3 prompt, CUDA FP16 |
| Cache warm/cold | Output identik pada sampel parity |
| Checkpoint ANN | Keempat SHA-256 cocok manifest asli |
| Integrasi hybrid | Blank → none; video tubuh → 33 kandidat termasuk tambahan custom |
| Integrasi ANN | 6 kelas, respons valid |
| Browser | Landing → studio, manual context, toggle, ANN/hybrid switch; tidak ada error konsol teramati |
| Dependencies environment lokal | `uv pip check` lolos, 78 paket kompatibel |
| npm audit saat `npm ci` | 0 vulnerability dilaporkan pada saat pemeriksaan |

Bukti: [parity JSON](xclip-parity.json), [integration JSON](integration-results.json), [ANN provenance](ann-provenance.json), screenshot di `assets/`.

Satu pengukuran server menghasilkan 438,2 ms untuk body/X-CLIP dan 59,1 ms untuk ANN; blank request pertama 1201,2 ms termasuk pemanasan perception. Angka tersebut bukan rata-rata/p95 dan tidak mencakup decode, antrean, jaringan atau render. Jangan menulis target <60 ms sebagai hasil semua jalur.

## Yang belum diuji

- Webcam fisik/live end-to-end setelah optimasi; izin kamera tidak diaktifkan oleh agent. API memakai video uji lokal dan gambar sintetis, bukan upload ke pihak ketiga.
- Akurasi/F1/false positive rate pada data berlabel yang terpisah untuk live action, jatuh atau indikator mata/mulut.
- Generalisasi orang, pencahayaan, lokasi dan perangkat lain; deteksi jatuh dengan banyak orang atau kamera bergerak.
- Kinerja CPU i7 Gen 8, Linux, container build/runtime, deployment Vercel, TLS/gateway auth, kapasitas multi-user dan load test.
- Model usia: tidak ada; unavailable secara eksplisit.

## Protokol sebelum rollout publik

1. Siapkan video berlabel dengan izin subjek; pisahkan orang/lokasi antara pengembangan dan evaluasi.
2. Untuk action, ukur confusion matrix, macro-F1 dan latency end-to-end, lalu bandingkan ANN/hybrid pada enam kelas yang sama. Evaluasi kandidat tambahan secara terpisah.
3. Untuk fall/eye indicators, uji event positif dan aktivitas biasa yang mirip; ukur sensitivitas, false alarms per jam, dan detection delay. Hindari adegan jatuh sungguhan yang membahayakan subjek.
4. Uji lost target, perubahan model/toggle, koneksi lambat, timeout, 429, server restart dan webcam permission denial.
5. Jalankan container di staging, pasang HTTPS dan gateway auth, ukur p50/p95, concurrency, VRAM dan memory leak. Baru tetapkan kapasitas/SLO dari pengukuran tersebut.

Perbaikan OpenCV diuji dalam environment terpisah berisi wheel base + contrib: keduanya dihapus, contrib 4.12 dipasang ulang, import dan cvtColor lolos. Server Windows pengguna belum diuji ulang setelah patch ini.
