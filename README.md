# 📊 Monitoring Task Tim

Aplikasi web berbasis **Streamlit** untuk memantau tugas harian, mingguan, dan bulanan tim.

## 🌟 Fitur Utama

- **Mode Akses (Hak Akses):**
  - **Viewer (Hanya Melihat):** Pengunjung / anggota umum hanya dapat melihat dashboard, daftar task, dan rekap tanpa bisa mengubah data.
  - **Admin / Editor:** Khusus Bos / Atasan untuk menambah task, mengubah status, progress, dan menambah anggota tim.
- **Dashboard Monitoring:**
  - Ringkasan total task, selesai, berjalan, belum mulai, hold, dan terlambat.
  - Rekap pembagian task per anggota tim (Lando, Rahma, dll.).
  - Rekap task per periode (Daily, Weekly, Monthly).
- **Form Tambah & Edit Task:**
  - Pengisian nama task, PIC, prioritas, deadline, catatan/kendala, dan link bukti Google Drive.
- **Daftar & Filter Task:**
  - Saring task berdasarkan PIC, Jenis Task, dan Status.
- **Pengaturan Tim:**
  - Tambah atau sesuaikan nama anggota tim secara dinamis.

## 🚀 Cara Menjalankan Secara Lokal

1. **Install Python & Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Jalankan Aplikasi Streamlit:**
   ```bash
   streamlit run app.py
   ```

3. **Akses via Browser:**
   Buka `http://localhost:8501`

---

## 🌐 Cara Deploy ke Streamlit Community Cloud (Gratis & Bisa Diakses Semua Anggota)

1. Pastikan repository **`monitoring_task`** di GitHub milik Bos Fazar sudah berisi file:
   - `app.py`
   - `requirements.txt`
   - `README.md`
2. Buka [Streamlit Community Cloud](https://share.streamlit.io/).
3. Login menggunakan akun GitHub.
4. Klik **"New app"**.
5. Pilih repository `fazar01213/monitoring_task`, branch `main`, dan Main file path `app.py`.
6. Klik **"Deploy!"**.
7. Bagikan link aplikasi hasil deploy ke seluruh anggota tim.
