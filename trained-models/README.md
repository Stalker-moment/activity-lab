# Checkpoint hasil training proyek

Checkpoint dalam direktori ini ikut masuk GitHub biasa. Setiap file model di bawah 10 MB. Semua hash dan ukuran tercatat dalam [manifest.json](manifest.json). Dataset, video pribadi, model smoke test, cache, serta bobot YOLO/X-CLIP/MediaPipe tidak disertakan di sini.

| Direktori | Komponen hasil training | Peran |
|---|---|---|
| baseline | activity_model.keras, ann_best.keras, lstm_best.keras | Enam kelas KTH; ANN dipilih berdasarkan validation loss dan digunakan website |
| advanced | activity_model.keras, ann_best.keras, temporal_best.keras | Tujuh keluaran termasuk idle; visual + optical flow, ANN vs model temporal |
| yolo-gru-e03 | best.keras | YOLO person crop → MobileNetV2 frozen → GRU, E03 seed 42 |

`activity_model.keras` adalah salinan model terpilih; dapat identik dengan `ann_best.keras`. Backbone MobileNetV2 ImageNet 160px dalam baseline adalah model **pralatih**, bukan hasil training sendiri; disertakan supaya pipeline baseline dapat diimpor tanpa mengunduh backbone kembali. YOLO pada E03 juga pralatih; bagian GRU yang dilatih oleh proyek.

Konfigurasi preprocessing, training history, metrik dan grafik yang ditemukan disertakan per folder. Model advanced dan E03 tidak kompatibel sebagai pengganti langsung ANN live. Gunakan notebook yang bersesuaian untuk inferensinya.

## Hasil yang tercatat

| Eksperimen | Accuracy test | Macro-F1 | Cakupan evaluasi |
|---|---:|---:|---|
| Baseline ANN | 77,29% | 0,7730 | 863 subsekuens KTH; baseline enam kelas |
| Advanced terpilih: ANN | 70,99% | 0,7072 | 648 jendela KTH enam kelas; idle/video pribadi belum memiliki test independen |
| E03 YOLO–GRU | 47,07% | 0,4861 | 648 jendela; detection coverage 63,89%, missing detection ikut dihitung salah |

Angka ini berasal dari file `test_metrics.json` yang disalin, **bukan evaluasi ulang dalam pekerjaan pengemasan ini**. Protokol baseline dan jendela advanced/research berbeda, jadi tabel ini tidak membuktikan peringkat metode yang sebanding secara langsung. Macro-F1 advanced mengikuti field tingkat atas yang mengevaluasi enam kelas teruji, bukan baris macro avg tujuh kelas yang menyertakan idle tanpa support.

## Aktifkan baseline pada backend

Dari root repository:

```sh
python scripts/import_ann.py trained-models/baseline
```

Importer mencocokkan hash baseline dengan provenance asli sebelum menyalin empat file yang diperlukan ke `backend/models/ann`. Ini tidak mengubah training atau model website. Untuk bobot runtime hybrid, gunakan downloader model publik sesuai README utama.

Lihat [sumber/lisensi](../docs/MODELS.md). Ketentuan dataset KTH dan backbone tetap berlaku; penyertaan classifier tidak memberikan lisensi baru terhadap dataset asal.
