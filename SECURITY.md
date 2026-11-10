# Privasi dan keamanan deployment

Default host hanya loopback. Backend tidak memiliki login aplikasi; CORS bukan kontrol akses. Public deployment memerlukan gateway autentikasi, HTTPS, rate limiting per user/IP, pembatasan origin, dan kebijakan retensi yang jelas.

Body kamera tidak ditulis ke disk oleh kode backend. Frame dan landmark tetap melewati memori server dan respons; administrator proxy dapat mengubah logging. Hindari request-body logging dan jangan memasukkan video pribadi dalam issue GitHub. Font Google pada frontend dapat menghubungi layanan font eksternal; ganti dengan font lokal bila memerlukan deployment sepenuhnya offline.

Untuk laporan masalah keamanan, gunakan kanal privat pengelola repository. Jangan membuka issue publik yang memuat token, rekaman pengguna, atau contoh eksploit terhadap deployment aktif.
