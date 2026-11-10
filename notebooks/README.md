# Training dan reproduksi notebook

Jalankan notebook terpisah dari backend website agar proses training tidak berebut RAM/VRAM. Notebook lokal/research mempertahankan pemeriksaan CUDA dari eksperimen asal; dukungan CPU backend tidak berarti notebook training sudah dioptimalkan untuk CPU.

```sh
pip install uv
uv pip install --python .venv -r requirements-training.txt --excludes requirements-exclude.txt
cd notebooks
jupyter lab
```

Pilih kernel environment yang memiliki PyTorch CUDA dan Keras. Jika nama kernel asal tidak tersedia, pilih kernel Python milik environment sendiri. Untuk Colab gunakan `Pengenalan_Aktivitas_KTH_Colab.ipynb`, mount Drive dan sesuaikan `ROOT` di sel konfigurasi.

## Dataset dan direktori kerja

Letakkan enam ZIP KTH di `notebooks/datasets/KTH/`: boxing.zip, handclapping.zip, handwaving.zip, jogging.zip, running.zip, walking.zip. Atau tetapkan environment `KTH_DATASET_DIR` ke direktori ZIP. Dataset tidak disertakan; sumber: https://www.csc.kth.se/cvap/actions/.

Jalankan notebook baseline, adaptasi dan advanced dari direktori kerja `notebooks/`. Video demo opsional: `notebooks/inference/video_uji.mp4`. Sel konfigurasi adaptasi/advanced menjelaskan struktur video tambahan yang dibutuhkan; video pribadi asal tidak dibundel. Jangan menganggap notebook adaptasi dapat mereproduksi hasil tanpa data tambahan tersebut.

Baseline menulis ke `notebooks/outputs_local`, advanced ke `notebooks/outputs_advanced`; cache/runtime juga di dalam folder notebook dan diabaikan Git. File publik dalam `trained-models/` adalah salinan hasil terdahulu, bukan tujuan output training baru.

## Research YOLO–GRU

Jalankan baseline lokal lebih dahulu agar `notebooks/outputs_local/video_manifest.csv` terbentuk dengan path video yang sesuai mesin baru. Unduh model publik dengan `python scripts/download_models.py` dari root repository. Kemudian jalankan Jupyter dari `notebooks/research/` dan buka notebook perbandingan. Modul `experiments.py` disertakan, dengan path YOLO diarahkan ke `backend/models/hybrid`.

E01/E02/E03 tersedia sebagai konfigurasi; hanya checkpoint E03 seed 42 yang ditemukan dan disertakan. Jangan menulis semua eksperimen selesai atau terlatih jika belum menjalankannya.

## Apa yang dibersihkan?

Output sel, execution count dan metadata sesi dibersihkan agar gambar/video pribadi, path output mesin lama, serta log panjang tidak masuk GitHub. Kode komputasi dipertahankan; path dataset lokal dan pesan launcher disesuaikan untuk struktur repository. Perubahan ini belum diuji dengan training ulang penuh. Metrik, training history dan grafik yang tersedia disalin ke `trained-models/`.
