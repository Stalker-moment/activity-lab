# Model, dataset, sumber, dan batasan

| Komponen | Asal | Catatan |
|---|---|---|
| ANN | Ekspor model proyek KTH | 6 kelas; classifier dilatih sendiri, backbone MobileNetV2 pralatih |
| MobileNetV2 | Keras Applications / ImageNet | Fitur frame grayscale yang dikembalikan ke RGB |
| YOLO11n detection | Ultralytics official assets | COCO 80 kelas; bobot asli |
| YOLO11n pose | Ultralytics official assets | COCO person keypoints 17 titik; bobot asli |
| Face Landmarker | Google MediaPipe models | 478 landmark, 52 blendshape |
| Gesture Recognizer | Google MediaPipe models | 21 landmark dan 7 gestur |
| X-CLIP | microsoft/xclip-base-patch16-zero-shot | 32 frame 224px; pretrained Kinetics-400; zero-shot kandidat deskripsi |

## Sumber untuk laporan

1. [KTH Recognition of Human Actions](https://www.csc.kth.se/cvap/actions/) — dataset baseline enam aktivitas. Ikuti ketentuan penggunaan sumber; dataset tidak disertakan.
2. [Keras MobileNetV2](https://keras.io/api/applications/mobilenet/) — backbone ANN, bukan hasil training dari nol.
3. [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/) dan [pose](https://docs.ultralytics.com/tasks/pose/).
4. [MediaPipe Face Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker) dan [Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer).
5. [X-CLIP model card](https://huggingface.co/microsoft/xclip-base-patch16-zero-shot), [paper](https://arxiv.org/abs/2208.02816), [Microsoft VideoX](https://github.com/microsoft/VideoX/tree/master/X-CLIP).
6. [Transformers X-CLIP 4.57.3 source](https://github.com/huggingface/transformers/blob/v4.57.3/src/transformers/models/x_clip/modeling_x_clip.py) — acuan parity cache.

Model download URLs + SHA-256: [hybrid-sources.json](hybrid-sources.json). X-CLIP revision: `6746d6a5202bf24300cd9bf36f457f174483d41b`. ANN hashes: [ann-provenance.json](ann-provenance.json). Manifest asli: [model-sources-original.json](model-sources-original.json).

## Lisensi & redistribusi

Sumber aplikasi disediakan di bawah AGPL-3.0-or-later (lihat LICENSE). Dependency Ultralytics memakai AGPL-3.0 atau lisensi Enterprise; tinjau [ketentuan resmi](https://www.ultralytics.com/license) sebelum penggunaan tertutup/komersial. MediaPipe dan Transformers memiliki ketentuan Apache-2.0 untuk kode; bobot model dapat memiliki ketentuan tersendiri. X-CLIP model card menandai MIT. Ikuti lisensi sumber masing-masing; lisensi aplikasi tidak mengubah lisensi model, dataset, atau library pihak ketiga.

Checkpoint classifier proyek dan backbone baseline yang dibutuhkan disertakan dalam `trained-models/`, dengan SHA-256 di manifest. Bobot YOLO/MediaPipe/X-CLIP runtime, video pribadi dan dataset **tidak masuk source release**. Pada laptop asal, bobot tersedia dalam folder ignored agar aplikasi dapat diuji. Untuk pengguna GitHub, downloader mengambil model publik; ANN dapat diimpor dari `trained-models/baseline`. File LICENSE aplikasi bukan izin untuk mendistribusikan ulang dataset KTH atau semua checkpoint.

## Indikator yang tidak boleh diklaim sebagai model terlatih

Deteksi mata/mulut dan potensi jatuh memakai aturan buatan pada output landmark, bukan classifier safety yang dilatih dan dievaluasi. Eye closure blendshape bukan geometric EAR atau PERCLOS. Mulut terbuka tidak membuktikan menguap/kelelahan. Postur horizontal dan penurunan tidak selalu berarti jatuh; gerakan olahraga dan kamera bergerak dapat menghasilkan false alarm.

Estimasi usia Antigravity sebelumnya menghitung proporsi landmark dan menambah angka confidence berdasarkan jumlah sampel. Tidak ada model usia atau validasi akurasi yang mendukung angka tersebut. Implementasi itu diganti respons unavailable; UI menampilkannya nonaktif. Menambahkan model usia kelak perlu sumber/lisensi, evaluasi error serta bias, dan UI yang menjelaskan ketidakpastian.
