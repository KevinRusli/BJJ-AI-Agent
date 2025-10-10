# 🥋 Chatbot GRIND Jiujitsu Indonesia

Selamat datang di Chatbot resmi GRIND Jiujitsu Indonesia! Chatbot ini dirancang untuk membantu calon member dan member dengan informasi tentang Brazilian Jiu-Jitsu, kelas, pricing, lokasi, jadwal, dan pertanyaan umum lainnya.

## Fitur Utama ✨

* **Informasi Kelas**: Mendapatkan detail lengkap tentang semua kelas BJJ yang tersedia (GI Intro, GI Beginner, GI Advance, Kids Class, dll).
* **Pricing & Membership**: Informasi pricing untuk Regular Membership, Kids Class, Private Class, dan Walk-in.
* **Lokasi & Jadwal**: Detail lokasi 7 gym GRIND di seluruh Indonesia beserta jadwal training.
* **FAQ BJJ**: Jawaban atas pertanyaan umum tentang Brazilian Jiu-Jitsu.
* **Trial Class Info**: Informasi tentang free trial class untuk new members.

## Teknologi yang Digunakan 🛠️

* **Python**: Bahasa pemrograman utama.
* **Streamlit**: Untuk membangun antarmuka web chatbot.
* **OpenAI GPT Models**: Otak di balik percakapan cerdas chatbot.
* **Knowledge Base System**: Comprehensive BJJ information database.

## Cara Menggunakan 🧑‍💻

### Persyaratan

Pastikan Anda memiliki Python 3.8+ terinstal.

### Local Development

1.  Clone repositori ini:
    ```bash
    git clone https://github.com/USERNAME_ANDA/chatbot-grind-jiujitsu-indonesia.git
    cd chatbot-grind-jiujitsu-indonesia
    ```
    *(Ganti `USERNAME_ANDA` dengan username GitHub Anda)*

2.  Buat virtual environment (disarankan):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Di Linux/macOS
    # atau `venv\Scripts\activate` di Windows
    ```

3.  Instal dependensi:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi Environment Variables:**
    Copy file `.env.example` ke `.env` dan isi dengan nilai yang sebenarnya:
    ```
    OPENAI_API_KEY="sk-YOUR_OPENAI_API_KEY_HERE"
    APPS_SCRIPT_WEB_APP_URL="https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
    ```

### Streamlit Cloud Deployment

1. **Push ke GitHub:** Pastikan semua file sudah di-push ke repository GitHub Anda

2. **Deploy ke Streamlit Cloud:**
   - Buka [share.streamlit.io](https://share.streamlit.io)
   - Connect dengan GitHub repository Anda
   - Pilih repository dan branch (biasanya `main`)
   - Set main file path: `app.py`

3. **Set Secrets di Streamlit Cloud:**
   - Buka App settings > Secrets
   - Tambahkan secrets dalam format TOML:
   ```toml
   OPENAI_API_KEY = "sk-your-openai-api-key-here"
   APPS_SCRIPT_WEB_APP_URL = "https://script.google.com/macros/s/your-script-id/exec"
   ```

4. **Google Apps Script Setup:**
   - Copy kode Google Apps Script yang disediakan
   - Buat Google Apps Script project baru
   - Deploy sebagai Web App dengan akses "Anyone"
   - Copy URL deployment ke APPS_SCRIPT_WEB_APP_URL

### Menjalankan Aplikasi

```bash
streamlit run app.py