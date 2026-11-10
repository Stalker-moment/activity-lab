# API

Base lokal: `http://127.0.0.1:8765`. OpenAPI interaktif: `/docs`.

## `GET /health`

200 mengembalikan `models.ann`, `models.xclip`, `models.hybrid` dengan state loading/ready/error, device, kemampuan. Liveness bukan readiness. `GET /ready` mengembalikan 200/503 untuk ANN + hybrid.

## `POST /infer`

```json
{
  "model": "hybrid",
  "mode": "auto",
  "frames": ["data:image/jpeg;base64,..."],
  "timestamps": [12.5],
  "request_id": 1,
  "session_id": "uuid-per-session",
  "custom_actions": ["playing badminton"],
  "drowsiness_enabled": false,
  "fall_detection_enabled": false,
  "age_detection_enabled": false
}
```

| Field | Batas |
|---|---|
| model | ann / hybrid / xclip (legacy enam prompt) |
| mode | auto / body / face / hand / objects; relevan pada hybrid |
| frames | 1–40 JPEG/base64; setiap string ≤180.000 karakter; resolusi ≤1024 per sisi |
| timestamps | Jumlah sama dengan frame, finite, meningkat ketat, span ≤3 detik |
| ANN/X-CLIP | Minimal 8 frame, span ≥1,6 detik; disampel ke 16/32 frame |
| session_id | ≤64 karakter; unik per client/sesi, jangan pakai identitas pribadi |
| custom_actions | ≤20 deskripsi, masing-masing ≤120 karakter |
| request body | Maksimal 6.000.000 byte, termasuk chunked |

Hybrid satu frame cukup untuk perception. Jika route tubuh dipilih tetapi klip belum cukup, `label=collecting_action`. Usia yang diminta mengembalikan `available:false`, bukan angka.

Respons hybrid memuat `route`, `raw_route`, `display_label`, `scores`, `score_labels`, `score_kind`, `latency_ms`, `routing`, `warning`, `objects`, `poses`, `faces`, `hands`, serta hasil indikator bila diaktifkan. Koordinat normalized [0..1] terhadap frame yang tidak dicerminkan. Face/hand bisa menghasilkan landmark sedikit di luar frame; gunakan clipping saat rendering bila diperlukan. Pose menambahkan confidence pada tiap keypoint.

`score_kind=similarity` adalah softmax relatif antar kandidat; `blendshape` adalah kekuatan gerakan wajah; `gesture`/`detection` adalah skor komponen terkait. Jangan membandingkan skor lintas jenis sebagai probabilitas yang sama.

Kode kegagalan: 413 body terlalu besar, 422 validasi/decode, 429 admission penuh (Retry-After: 1), 503 model belum siap, 500 inferensi gagal. Tidak ada queue tanpa batas; client sebaiknya membatasi satu request aktif dan retry dengan jeda saat 429.

`latency_ms` mengukur inferensi setelah decode dan setelah mendapat lock. Angka ini tidak mencakup upload, decode, antrean, atau render. Untuk respons aplikasi, ukur waktu request round-trip di client.
