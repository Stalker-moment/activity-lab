# Perubahan dari snapshot Antigravity

| Area | Temuan | Perbaikan |
|---|---|---|
| Auto payload | Selalu satu frame; X-CLIP terus mengumpulkan gerakan | Gunakan buffer setelah raw route body, plus probe periodik |
| X-CLIP cache | Dot-product video/text melewati video-conditioned prompt generator | Cache projected text saja, jalankan tahapan forward lainnya; parity logit 0 pada sampel |
| Fall ratio | Rasio normalized tidak memperhitungkan aspek video | Kalikan dengan width/height piksel |
| Safety state | State dapat bertahan lintas gap / toggle | Reset gap, missing target, toggle, perubahan sesi; kapasitas dibatasi |
| Fall label | Horizontal langsung diberi alarm jatuh | Perlu penurunan teramati dan durasi horizontal; klaim eksperimental |
| Age | Rumus tanpa model, confidence meningkat otomatis | Nonaktif/unavailable, tanpa angka usia buatan |
| API | CORS wildcard + credentials, queue thread tak terbatas | Origin eksplisit, no credentials, admission 429 |
| Body limit | Hanya Content-Length | Batas byte ASGI termasuk chunked |
| History | Simpan seluruh landmark per hasil | Ringkasan ringan, maksimal 80 |
| Repo | Workspace berisi model, log, environment, data pengguna | Folder terpisah, ignore, downloader, CI, dokumentasi deployment |

ANN checkpoint, kelas dan preprocessing dipertahankan. Folder eksperimen awal tidak ditimpa. Target latensi <60 ms dari dokumen rencana belum dibuktikan dan tidak ditulis sebagai hasil.
