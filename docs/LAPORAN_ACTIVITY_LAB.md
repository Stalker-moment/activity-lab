# LAPORAN ACTIVITY LAB: PENGENALAN AKTIVITAS MANUSIA BERBASIS ARTIFICIAL NEURAL NETWORK (ANN)

**Mata Kuliah:** Pengantar Teknologi Informasi (PTI) — Semester 1  
**Proyek:** Activity Lab (Human Activity Recognition)  
**Kelompok:** Kelompok [Nomor Kelompok] — Kelas [Kelas]  
**Anggota Kelompok (Mahasiswa Teknik Elektro UNS):**  
1. **Muhammad Sahrul Nabawi** (NIM: 21113032610045)  
2. **Muhammad Singgih** (NIM: 21113032610046)  
3. **Muhammad Tier Sinyo Cahyo Utomo Suharjo** (NIM: 21113032610047)  

**Repository GitHub:** [https://github.com/Stalker-moment/activity-lab](https://github.com/Stalker-moment/activity-lab)  
**Notebook Google Colab:** [Pengenalan_Aktivitas_KTH_Colab.ipynb](https://colab.research.google.com/drive/1aoXiskZIK322aEfW9xqPq8Bjx43mO9JG?usp=sharing)  
**Production API:** `https://activity-lab-api.tierkun.my.id`  

---

## RINGKASAN EKSEKUTIF

Proyek **Activity Lab** mengembangkan sistem pengenalan aktivitas manusia (*Human Activity Recognition* / HAR) berbasis visi komputer dan *Artificial Neural Network* (ANN) yang mampu mengenali gerakan tubuh secara efisien dan *real-time*. Model dilatih menggunakan dataset standar industri **KTH Action Recognition** yang mencakup 6 kelas aktivitas: *boxing*, *handclapping*, *handwaving*, *jogging*, *running*, dan *walking*.

Dengan pendekatan *transfer learning*, ekstraksi fitur spasial video dilakukan oleh tulang punggung (*backbone*) **MobileNetV2** (bobot *ImageNet* dibekukan), menghasilkan 1280 fitur per frame. Classifier ANN yang dirancang memanfaatkan *GlobalAveragePooling1D* untuk agregasi temporal, lapisan *Dropout* (0.3) untuk mencegah *overfitting*, serta *Dense layer* (32 neuron ReLU) sebelum klasifikasi akhir *Softmax* 6 kelas.

Pada tahap evaluasi independen terhadap 863 subsekuens uji, model ANN memperoleh:
- **Akurasi Uji (Test Accuracy):** **77,29%**
- **Macro-F1 Score:** **0,7730**
- **Validation Loss Terbaik:** **0,3438** (pada Epoch 20)
- **Latensi Inferensi Server:** **~59,1 ms**

Model ANN berhasil diintegrasikan ke dalam aplikasi web berbasis **Next.js** dan **FastAPI** dengan fitur *Live Studio*, memungkinkan inferensi langsung dari kamera *webcam* menggunakan *ring buffer* 16 frame (~2 detik).

---

## BAB I: PENDAHULUAN

### 1.1 Latar Belakang
Pengenalan aktivitas manusia (*Human Activity Recognition* / HAR) merupakan salah satu bidang terpenting dalam *Artificial Intelligence* (AI) dan *Computer Vision*. HAR diterapkan luas pada pemantauan kesehatan, analisis olahraga, otomasi pengawasan keamanan, serta interaksi manusia dan komputer (*Human-Computer Interaction*). 

Pengolahan video konvensional memerlukan komputasi yang sangat berat karena harus memproses urutan gambar berdimensi tinggi secara berulang. Dalam proyek Activity Lab ini, kami merancang solusi cerdas yang menyeimbangkan antara akurasi pengenalan dan efisiensi komputasi, sehingga dapat dijalankan bahkan pada lingkungan CPU standar tanpa memerlukan GPU server berbiaya tinggi.

### 1.2 Rumusan Masalah
1. Bagaimana merancang arsitektur Artificial Neural Network (ANN) yang ringan namun akurat untuk mengklasifikasi 6 aktivitas manusia dari data sekuensial video?
2. Bagaimana memproses dan mengekstraksi representasi fitur temporal dari aliran video berdurasi 2 detik secara efisien?
3. Bagaimana performa klasifikasi ANN pada tiap kelas gerakan, dan bagaimana perbandingannya dengan arsitektur temporal sekuensial seperti LSTM?
4. Bagaimana mengintegrasikan model machine learning yang telah dilatih ke dalam antarmuka web interaktif yang siap pakai (*real-time inference*)?

### 1.3 Tujuan Proyek
1. Melatih dan mengevaluasi model classifier ANN berbasis *MobileNetV2 feature extractor* pada dataset KTH Action Recognition.
2. Menganalisis metrik performa model (Loss, Accuracy, Precision, Recall, Macro-F1, dan Confusion Matrix).
3. Membangun sistem *end-to-end* yang menghubungkan antarmuka kamera web browser (Next.js) dengan backend komputasi inferensi (FastAPI).

---

## BAB II: LANDASAN TEORI

### 2.1 Artificial Neural Network (ANN)
Artificial Neural Network (Jaringan Saraf Tiruan) adalah model komputasi yang terinspirasi oleh struktur jaringan saraf biologis otak manusia. ANN terdiri dari lapisan input (*input layer*), satu atau lebih lapisan tersembunyi (*hidden layers*), dan lapisan output (*output layer*). Setiap neuron terhubung dengan bobot (*weights*) dan bias yang disesuaikan selama proses *backpropagation* menggunakan fungsi optimasi seperti Adam.

### 2.2 Transfer Learning & MobileNetV2
Untuk menghindari pelatihan model *deep learning* dari nol (*from scratch*) yang membutuhkan jutaan gambar dan waktu berhari-hari, proyek ini menerapkan **Transfer Learning**. Model *MobileNetV2* yang telah dilatih sebelumnya pada dataset *ImageNet* digunakan sebagai pengekstraksi fitur (*feature extractor*). Lapisan klasifikasi atas (*top layers*) dilepas dan bobotnya dibekukan (*frozen*), sehingga hanya mengekstrak vektor representasi visual berdimensi 1280 dari setiap frame gambar dengan sangat cepat.

### 2.3 Dataset KTH Action Recognition
Dataset KTH (KTH Royal Institute of Technology) adalah salah satu tolok ukur standar dalam riset *human action recognition*. Dataset ini berisi rekaman video dari 25 subjek (orang) yang melakukan 6 jenis aktivitas dalam 4 skenario pencahayaan dan lingkungan berbeda (luar ruangan, luar ruangan dengan variasi skala, luar ruangan dengan pakaian berbeda, dan dalam ruangan). Enam aktivitas yang dikenali adalah:
1. `boxing` (memukul / bertinju)
2. `handclapping` (bertepuk tangan)
3. `handwaving` (melambaikan tangan)
4. `jogging` (berlari santai)
5. `running` (berlari cepat)
6. `walking` (berjalan)

---

## BAB III: METODOLOGI & ARSITEKTUR SISTEM

### 3.1 Pipeline Pengolahan Data (Preprocessing)
1. **Sampling Frame:** Video dipotong menjadi klip berdurasi ~2 detik dengan laju pengambilan sampel 16 frame terpilih.
2. **Normalisasi & Grayscale-to-RGB:** Frame diubah ke resolusi spasial $160 \times 160$ piksel. Citra grayscale dikonversi kembali ke 3 kanal warna agar sesuai dengan spesifikasi input tensor MobileNetV2.
3. **Ekstraksi Spasial:** Tiap frame dilewatkan ke MobileNetV2 (*frozen*), menghasilkan representasi matriks berdimensi $(16, 1280)$ per sekuens video.

### 3.2 Desain Arsitektur ANN
Arsitektur classifier ANN yang kami bangun dirancang kompak dan bebas dari bobot yang berlebihan (*overparameterized*):

```
Model: "ann"
_________________________________________________________________
 Layer (type)                Output Shape              Param #   
=================================================================
 input_layer (InputLayer)    [(None, 16, 1280)]        0         
 global_average_pooling1d    (None, 1280)              0         
 dropout (Dropout 30%)       (None, 1280)              0         
 dense (Dense, ReLU)         (None, 32)                40,992    
 dense_1 (Dense, Softmax)    (None, 6)                 198       
=================================================================
Total params: 41,190 (160.90 KB)
Trainable params: 41,190 (160.90 KB)
Non-trainable params: 0 (0.00 Byte)
_________________________________________________________________
```

- **GlobalAveragePooling1D:** Mengompres dimensi waktu (16 frame) menjadi 1 vektor rata-rata representasi fitur temporal berdimensi 1280.
- **Dropout (0.3):** Mematikan 30% neuron secara acak selama pelatihan guna meminimalisir ketergantungan antar-fitur (*co-adaptation*) dan mencegah overfitting.
- **Dense Layer (32 neuron, aktivasi ReLU):** Memproyeksikan fitur ke representasi laten yang lebih padat dan non-linear.
- **Output Layer (6 neuron, aktivasi Softmax):** Menghasilkan distribusi probabilitas untuk 6 kelas aksi.

### 3.3 Konfigurasi Pelatihan (Training)
- **Optimizer:** Adam ($\alpha = 0.001$)
- **Loss Function:** `sparse_categorical_crossentropy`
- **Maksimum Epoch:** 30 epoch (dengan *EarlyStopping* bersyarat `patience=6` memantau `val_loss`)
- **Seed:** 42 (menjamin reproduktibilitas hasil)
- **Data Splitting:** Pembagian berbasis subjek orang (*official cross-subject split*) agar data uji tidak pernah dilihat sebelumnya saat pelatihan.

### 3.4 Arsitektur Sistem Live Studio (Full-Stack)
Aplikasi didistribusikan dalam bentuk web modern:
- **Frontend:** Next.js 15 + React + Tailwind CSS + HTML5 Video Canvas. Mengambil feed webcam klien pada kecepatan 16 FPS, menyimpannya dalam *ring buffer* 2 detik, lalu mengirimkan JPEG buffer ke backend.
- **Backend:** FastAPI (Python 3.12) berbasis asinkron dengan pembatasan antrean *in-flight requests* (maksimal 2 *jobs concurrently*) untuk mencegah *server overload*.

---

## BAB IV: HASIL PELATIHAN & EVALUASI

### 4.1 Analisis Kurva Pelatihan (Training & Validation Loss)
Pelatihan berlangsung selama 26 epoch sebelum dihentikan oleh mekanisme *EarlyStopping*. 
- **Titik Konvergensi Optimal:** Tercapai pada **Epoch 20** dengan nilai `val_loss` terendah yaitu **0,3438** dan `val_accuracy` sebesar **84,35%**.
- Pada epoch-epoch awal (Epoch 1-5), loss training turun secara drastis dari 1,5695 menjadi 0,5368, sementara akurasi validasi melonjak dari 54,89% menjadi 74,45%.
- Stabilitas kurva validasi menunjukkan bahwa teknik regularisasi (*Dropout* 0.3 dan *Frozen Backbone*) berhasil mencegah terjadinya *overfitting* yang parah pada dataset KTH.

### 4.2 Evaluasi pada Data Uji (Test Set — 863 Subsekuens)
Evaluasi akhir dilakukan pada 863 klip data uji independen yang belum pernah dilihat model selama pelatihan:

| Metrik Evaluasi | Nilai |
|---|---|
| **Akurasi Keseluruhan (Test Accuracy)** | **77,29%** |
| **Macro Average Precision** | **83,49%** |
| **Macro Average Recall** | **77,31%** |
| **Macro Average F1-Score** | **0,7730** |
| **Weighted Average F1-Score** | **0,7727** |

#### Rincian Kinerja per Kelas Aktivitas:
| Kelas Aktivitas | Precision | Recall | F1-Score | Jumlah Sampel (Support) |
|---|---|---|---|---|
| **boxing** | 97,24% | 98,60% | **97,92%** | 143 |
| **handclapping** | 76,09% | 97,22% | **85,37%** | 144 |
| **handwaving** | 98,00% | 68,06% | **80,33%** | 144 |
| **jogging** | 50,77% | 91,67% | **65,35%** | 144 |
| **running** | 85,37% | 48,61% | **61,95%** | 144 |
| **walking** | 93,48% | 59,72% | **72,88%** | 144 |

### 4.3 Pembahasan Analisis Confusion Matrix
1. **Aktivitas Tubuh Bagian Atas (*Boxing, Clapping, Waving*):**
   - Mendapatkan performa F1-Score sangat tinggi (>80% s.d. 97,9%). Gerakan pukulan bertinju (*boxing*) memiliki karakteristik fitur yang sangat distingtif sehingga hampir tidak pernah salah diklasifikasikan (akurasi 98,6%).
2. **Aktivitas Lokomosi Kaki (*Jogging vs Running vs Walking*):**
   - Terjadi misklasifikasi yang cukup signifikan antara *jogging* dan *running*. Hal ini wajar secara fisis karena pola gerakan kaki dan postur tubuh pada lari santai (*jogging*) dan lari cepat (*running*) memiliki frekuensi visual yang sangat mirip, di mana pembeda utamanya hanyalah kecepatan gerak piksel horizontal.

### 4.4 Perbandingan Model: ANN vs LSTM
Dalam eksperimen baseline, kami turut menguji arsitektur temporal **LSTM (Long Short-Term Memory)** dengan 64 unit tersembunyi:
- **Validation Loss ANN:** **0,3438** *(Pemenang/Terpilih)*
- **Validation Loss LSTM:** **0,3790**
- **Kecepatan Inferensi:** Model ANN hanya membutuhkan ~59 ms di CPU, sedangkan LSTM memerlukan komputasi recurrent state yang lebih lambat dan memakan memori lebih besar. Oleh sebab itu, model ANN dipilih sebagai model inti produksi pada aplikasi web.

---

## BAB V: IMPLEMENTASI & HASIL SISTEM WEB

Sistem telah berhasil diimplementasikan penuh:
1. **Live Camera Feed:** Pengguna membuka peramban web pada rute `/live` dan memberikan izin akses webcam.
2. **Real-Time Visual Overlay:** Antarmuka secara interaktif menampilkan *bounding box*, prediksi kelas aksi teratas beserta skor probabilitasnya (*confidence score*), serta grafik latensi.
3. **Robustness & Stability:** Dilengkapi *geometric router* dan *exponential moving average* untuk mencegah perubahan prediksi yang berkedip-kedip (*flickering*).

---

## BAB VI: KESIMPULAN & SARAN

### 6.1 Kesimpulan
1. Proyek Activity Lab berhasil mengimplementasikan *Human Activity Recognition* berbasis Artificial Neural Network (ANN) yang dipadukan dengan *feature extractor* MobileNetV2.
2. Model ANN mencapai performa memuaskan pada dataset KTH dengan **akurasi uji 77,29%** dan **Macro-F1 0,7730**, dengan keunggulan utama pada pengenalan gestur tangan dan pukulan.
3. Arsitektur ANN terbukti lebih ringkas, hemat daya, dan memiliki *validation loss* lebih rendah (0,3438) dibandingkan model LSTM (0,3790), menjadikannya sangat ideal untuk komputasi *edge* atau web real-time.
4. Sistem web berbasis Next.js dan FastAPI berhasil mengintegrasikan model ke dalam antarmuka interaktif yang dapat langsung diuji pengguna melalui kamera laptop.

### 6.2 Saran
1. **Peningkatan Resolusi Temporal:** Menambahkan ekstraksi *optical flow* atau modul *temporal difference* untuk mempertegas perbedaan antara aktivitas *jogging* dan *running*.
2. **Variasi Dataset Lokal:** Melakukan *fine-tuning* lanjutan pada video aktivitas orang Indonesia dengan kondisi ruangan dan pencahayaan rumah sehari-hari.

---

## DAFTAR PUSTAKA & TAUTAN

1. Schuldt, C., Laptev, I., & Caputo, B. (2004). *Recognizing human actions: A local SVM approach*. Proceedings of the 17th International Conference on Pattern Recognition (ICPR'04).
2. Sandler, M., et al. (2018). *MobileNetV2: Inverted Residuals and Linear Bottlenecks*. IEEE/CVF CVPR.
3. Repository GitHub: [https://github.com/Stalker-moment/activity-lab](https://github.com/Stalker-moment/activity-lab)
4. Model Checkpoint & Baseline Config: Folder `trained-models/baseline/`

