# Review E03

Training, evaluasi, dan inferensi selesai tanpa error notebook tersimpan.

- Test accuracy: 47.07% (305/648).
- Test macro F1: 48.61%.
- Detection coverage >=80%: 414/648 windows (63.89%).
- Accuracy pada subset coverage valid: 73.67%; ini metrik kondisional dan tidak boleh menggantikan hasil end-to-end.
- Train: 326 windows digunakan; 247/573 dikeluarkan oleh aturan coverage.
- Best validation macro F1: 49.24%, epoch 22 dari 29. Train accuracy epoch tersebut 100%; terdapat gap generalisasi.
- Running: 0/108 benar, 95/108 ditolak karena coverage. Walking: 15/108 benar, 68 ditolak. Jogging: 23/108 benar, 71 ditolak.
- Video pribadi: setelah pengumpulan data sekitar dua detik, seluruh 229 frame berikutnya dilabel boxing. Tanpa anotasi manual ini bukan bukti akurasi video pribadi.

## Temuan pembentukan data

Pemeriksaan frame VALIDASI menemukan jendela jogging/running mencakup masuk-keluar aktor; contoh walking bahkan seluruh jendelanya latar kosong. Uniform windows pada keseluruhan file KTH tidak selalu merupakan segmen aktivitas valid. Ini kelemahan pembentukan manifest, bukan bukti bahwa crop YOLO pasti lebih buruk.

Diagnosis tersimpan di research/pilot/low_coverage_diagnostic.jpg. Hasil E03 asli dipertahankan dan tidak ditimpa.

## Langkah selanjutnya

Buat protokol revisi yang memilih jendela dari batas aktivitas resmi 00sequences.txt, audit keberadaan aktor dan durasi pendek pada running. Jika jendela dua detik tidak muat, pilih durasi bersama lebih pendek melalui train/val atau gunakan padding/mask yang didefinisikan secara konsisten. Jangan menurunkan ambang coverage hanya untuk memperbaiki angka test.

Setelah protokol revisi dibekukan, jalankan ulang E01, E02, E03 dengan manifest yang sama dan direktori hasil baru. Jangan langsung membandingkan 47.07% dengan 77.29% baseline lama karena unit evaluasinya berbeda. Simpan benchmark sekarang sebagai eksperimen yang mengungkap masalah sampling.
