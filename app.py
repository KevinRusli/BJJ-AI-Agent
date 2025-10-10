import openai
import os
from dotenv import load_dotenv
import json
from datetime import datetime, time, timedelta
import requests
import streamlit as st 
from typing import Optional
from config import SYSTEM_PROMPT, OPENAI_MODEL, MAX_TOKENS

# Muat variabel lingkungan dari .env file
load_dotenv()

# Pastikan API Key OpenAI sudah diatur sebagai environment variable
# Untuk deployment di Streamlit Cloud, gunakan st.secrets atau environment variables
try:
    # Coba dari st.secrets dulu (untuk Streamlit Cloud)
    if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
        openai_api_key = st.secrets["OPENAI_API_KEY"]
    else:
        # Fallback ke environment variable (untuk local development)
        openai_api_key = os.environ["OPENAI_API_KEY"]
    
    openai_client = openai.OpenAI(api_key=openai_api_key) 
except (KeyError, AttributeError):
    st.error("OPENAI_API_KEY tidak ditemukan. Untuk Streamlit Cloud, set di Secrets. Untuk local, set di .env file.")
    st.stop() 

# --- URL Google Apps Script ---
try:
    # Coba dari st.secrets dulu (untuk Streamlit Cloud)
    if hasattr(st, 'secrets') and 'APPS_SCRIPT_WEB_APP_URL' in st.secrets:
        APPS_SCRIPT_WEB_APP_URL = st.secrets["APPS_SCRIPT_WEB_APP_URL"]
    else:
        # Fallback ke environment variable (untuk local development)
        APPS_SCRIPT_WEB_APP_URL = os.environ["APPS_SCRIPT_WEB_APP_URL"]
except (KeyError, AttributeError):
    st.error("APPS_SCRIPT_WEB_APP_URL tidak ditemukan. Untuk Streamlit Cloud, set di Secrets. Untuk local, set di .env file.")
    st.stop() 

# --- BJJ Class scheduling constants ---
OPERATING_START_HOUR = 7    # 7 pagi (sesuai Google Apps Script)
OPERATING_END_HOUR = 21     # 9 malam (21:00) (sesuai Google Apps Script)
CLASS_DURATION_MINUTES = 60 # Durasi kelas BJJ sesuai Google Apps Script (60 menit)
TRIAL_FEE = 0 # Trial class gratis

# --- Fungsi Validasi Jam Operasional ---
def is_within_operating_hours(tanggal_str: str, jam_str: str) -> bool:
    """Memeriksa apakah waktu yang diminta berada dalam jam operasional."""
    try:
        requested_datetime = datetime.strptime(f"{tanggal_str} {jam_str}", "%Y-%m-%d %H:%M")
        
        # Cek jam saja
        if not (time(OPERATING_START_HOUR, 0) <= requested_datetime.time() <= time(OPERATING_END_HOUR, 0)):
            return False
            
        return True
    except ValueError:
        return False # Format tanggal/jam tidak valid

# Fungsi placeholder untuk decorator tool
def tool(func):
    func.is_tool = True
    return func

@tool
def book_trial_class(nama_klien: str, kontak_klien: str, tanggal: str, jam: str, jenis_kelas: str, catatan_tambahan: Optional[str] = "") -> str:
    """
    Mencatat booking trial class BJJ ke Google Sheets.
    Args:
        nama_klien (str): Nama lengkap klien yang melakukan booking.
        kontak_klien (str): Nomor telepon atau alamat email klien.
        tanggal (str): Tanggal booking dalam format YYYY-MM-DD.
        jam (str): Jam booking dalam format HH:MM (24 jam).
        jenis_kelas (str): Jenis kelas BJJ (GI Intro, GI Beginner, dll).
        catatan_tambahan (Optional[str]): Catatan tambahan mengenai booking.
    """
    try:
        requested_date = datetime.strptime(tanggal, "%Y-%m-%d").date()
        today = datetime.now().date()
        if requested_date < today:
            return f"Tanggal '{tanggal}' sudah berlalu. Pilih tanggal hari ini atau ke depan ya! 📅"
        
        datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")
    except ValueError:
        return f"Format tanggal atau jam kurang tepat. Gunakan format YYYY-MM-DD dan HH:MM ya! 😊"

    if not is_within_operating_hours(tanggal, jam):
        return f"Maaf, jam {jam} di luar operasional kami (Pukul {OPERATING_START_HOUR}:00 - {OPERATING_END_HOUR}:00). Pilih waktu di antara jam operasional ya! ⏰"

    availability_response = check_class_availability(tanggal, jam, jenis_kelas)
    if "tidak tersedia" in availability_response.lower() or "slot sudah terisi" in availability_response.lower():
        return availability_response 

    payload = {
        "action": "create_booking", 
        "nama_klien": nama_klien,
        "kontak_klien": kontak_klien,
        "tanggal": tanggal,
        "waktu": jam,
        "catatan_klien": f"Trial Class - {jenis_kelas}. {catatan_tambahan}".strip()
    }

    try:
        response = requests.post(APPS_SCRIPT_WEB_APP_URL, json=payload)
        response.raise_for_status() 
        
        script_response = response.json() 

        if script_response.get("status") == "success":
            return f"✅ Trial class booking berhasil!\n\n👤 Nama: {nama_klien}\n📅 Tanggal: {tanggal}\n⏰ Jam: {jam}\n🥋 Kelas: {jenis_kelas}\n\n🆓 Trial class GRATIS untuk new member!"
        else:
            error_message = script_response.get('message', 'Terjadi kesalahan tidak diketahui di sistem booking.')
            return f"❌ Gagal booking: {error_message}"
    except requests.exceptions.RequestException as e:
        st.error(f"[Backend Error] Error calling Apps Script webhook for book_trial_class: {e}")
        return f"🔧 Terjadi masalah koneksi. Mohon coba lagi nanti atau hubungi admin."
    except json.JSONDecodeError as e:
        st.error(f"[Backend Error] Error decoding JSON from Apps Script for book_trial_class: {e}, Response content: {response.text}")
        return "🔧 Respon sistem tidak valid. Mohon coba lagi atau hubungi admin."

@tool
def cancel_booking(nama_klien: str, tanggal: str, jam: str) -> str:
    """
    Mengirim detail pembatalan booking ke Google Apps Script untuk dihapus dari Google Sheets.
    """
    try:
        requested_date = datetime.strptime(tanggal, "%Y-%m-%d").date()
        today = datetime.now().date()
        if requested_date < today:
            return f"Tanggal '{tanggal}' sudah berlalu. Booking yang sudah lewat tidak bisa dibatalkan ya! 📅"
            
        datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")
    except ValueError:
        return f"Format tanggal atau jam kurang tepat. Gunakan format YYYY-MM-DD dan HH:MM ya! 😊"

    payload = {
        "action": "delete_booking", 
        "nama_klien": nama_klien,
        "tanggal": tanggal,
        "waktu": jam, 
    }
    
    try:
        response = requests.post(APPS_SCRIPT_WEB_APP_URL, json=payload)
        response.raise_for_status() 
        
        script_response = response.json()

        if script_response.get("status") == "success":
            return f"✅ Booking berhasil dibatalkan!\n\n👤 Nama: {nama_klien}\n📅 Tanggal: {tanggal}\n⏰ Jam: {jam}\n\nJika ingin book lagi, tinggal chat aja ya! 😊"
        else:
            error_message = script_response.get('message', 'Terjadi kesalahan tidak diketahui saat membatalkan booking.')
            return f"❌ Gagal membatalkan: {error_message}"

    except requests.exceptions.RequestException as e:
        st.error(f"[Backend Error] Error calling Apps Script webhook for cancel_booking: {e}")
        return f"🔧 Terjadi masalah koneksi. Mohon coba lagi nanti atau hubungi admin."
    except json.JSONDecodeError as e:
        st.error(f"[Backend Error] Error decoding JSON from Apps Script for cancel_booking: {e}, Response content: {response.text}")
        return "🔧 Respon sistem tidak valid. Mohon coba lagi atau hubungi admin."

@tool
def check_class_availability(tanggal: str, jam: str, jenis_kelas: str = "") -> str:
    """
    Memeriksa ketersediaan slot waktu tertentu untuk booking kelas BJJ di Google Sheets.
    """
    try:
        requested_date = datetime.strptime(tanggal, "%Y-%m-%d").date()
        today = datetime.now().date()
        if requested_date < today:
            return f"Tanggal '{tanggal}' sudah berlalu. Pilih tanggal hari ini atau ke depan ya! 📅"
            
        datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")
    except ValueError:
        return f"Format tanggal atau jam kurang tepat. Gunakan format YYYY-MM-DD dan HH:MM ya! 😊"
    
    if not is_within_operating_hours(tanggal, jam):
        return f"Maaf, jam {jam} di luar operasional kami (Pukul {OPERATING_START_HOUR}:00 - {OPERATING_END_HOUR}:00). Pilih waktu di antara jam operasional ya! ⏰"

    payload = {
        "action": "check_availability", 
        "tanggal": tanggal,
        "waktu": jam, 
        "durasi_menit": CLASS_DURATION_MINUTES 
    }

    try:
        response = requests.post(APPS_SCRIPT_WEB_APP_URL, json=payload)
        response.raise_for_status() 
        
        script_response = response.json()

        if script_response.get("status") == "success":
            is_available = script_response.get("available", False)
            if is_available:
                return f"✅ Slot {tanggal} jam {jam} tersedia! Mau booking sekarang? 😊"
            else:
                return f"❌ Maaf, slot {tanggal} jam {jam} sudah terisi. Coba pilih waktu lain ya! 🕐"
        else:
            error_message = script_response.get('message', 'Terjadi kesalahan tidak diketahui saat memeriksa ketersediaan.')
            return f"🔧 Gagal cek ketersediaan: {error_message}"
    except requests.exceptions.RequestException as e:
        st.error(f"[Backend Error] Error calling Apps Script webhook for check_class_availability: {e}")
        return f"🔧 Terjadi masalah koneksi. Mohon coba lagi nanti atau hubungi admin."
    except json.JSONDecodeError as e:
        st.error(f"[Backend Error] Error decoding JSON from Apps Script for check_class_availability: {e}, Response content: {response.text}")
        return "🔧 Respon sistem tidak valid. Mohon coba lagi atau hubungi admin." 

        st.error(f"[Backend Error] Error decoding JSON from Apps Script for check_class_availability: {e}, Response content: {response.text}")
        return "Maaf, respon tidak valid dari sistem pengecekan ketersediaan."

# --- Definisi Tools untuk OpenAI ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "book_trial_class", 
            "description": "Mencatat booking trial class BJJ ke Google Sheets. Trial class GRATIS untuk new members.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nama_klien": {
                        "type": "string",
                        "description": "Nama lengkap klien yang melakukan booking trial class.",
                    },
                    "kontak_klien": {
                        "type": "string",
                        "description": "Nomor telepon atau alamat email klien, wajib untuk konfirmasi.",
                    },
                    "tanggal": {
                        "type": "string",
                        "description": f"Tanggal booking yang diinginkan dalam format YYYY-MM-DD. PASTIKAN TAHUN ADALAH TAHUN SAAT INI ({datetime.now().year}) atau MASA DEPAN. Contoh: {datetime.now().year}-10-15",
                    },
                    "jam": {
                        "type": "string",
                        "description": "Jam booking yang diinginkan dalam format HH:MM (24 jam). Contoh: 19:00 untuk jam 7 malam.",
                    },
                    "jenis_kelas": {
                        "type": "string",
                        "description": "Jenis kelas BJJ yang ingin di-trial. Pilihan: GI Intro Class, GI Beginner, GI Advance, Kids Class A (4-9 tahun), Kids Class B (8-14 tahun), No GI Session.",
                    },
                    "catatan_tambahan": { 
                        "type": "string",
                        "description": "Catatan tambahan mengenai booking, seperti preferensi atau hal khusus lainnya. Jika tidak ada, biarkan kosong.",
                        "default": ""
                    }
                },
                "required": ["nama_klien", "kontak_klien", "tanggal", "jam", "jenis_kelas"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking", 
            "description": "Mencari dan menghapus jadwal booking trial class BJJ dari Google Sheets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nama_klien": {
                        "type": "string",
                        "description": "Nama klien yang bookingnya ingin dibatalkan.",
                    },
                    "tanggal": {
                        "type": "string",
                        "description": f"Tanggal booking yang ingin dibatalkan dalam format YYYY-MM-DD. PASTIKAN TAHUN ADALAH TAHUN SAAT INI ({datetime.now().year}) atau MASA DEPAN. Contoh: {datetime.now().year}-10-15",
                    },
                    "jam": {
                        "type": "string",
                        "description": "Jam booking yang ingin dibatalkan dalam format HH:MM (24 jam).",
                    },
                },
                "required": ["nama_klien", "tanggal", "jam"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_class_availability", 
            "description": f"Memeriksa ketersediaan slot waktu tertentu untuk booking kelas BJJ di Google Sheets. Durasi kelas adalah {CLASS_DURATION_MINUTES} menit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tanggal": {
                        "type": "string",
                        "description": f"Tanggal yang ingin diperiksa ketersediaannya dalam format YYYY-MM-DD. PASTIKAN TAHUN ADALAH TAHUN SAAT INI ({datetime.now().year}) atau MASA DEPAN. Contoh: {datetime.now().year}-10-15",
                    },
                    "jam": {
                        "type": "string",
                        "description": "Jam yang ingin diperiksa ketersediaannya dalam format HH:MM (24 jam).",
                    },
                    "jenis_kelas": {
                        "type": "string",
                        "description": "Jenis kelas BJJ (opsional). Contoh: GI Intro Class, GI Beginner, dll.",
                        "default": ""
                    },
                },
                "required": ["tanggal", "jam"],
            },
        },
    },
]

# --- Fungsi Utama Chatbot dengan Tool Calling untuk BJJ ---
def get_chatbot_response(user_prompt: str, chat_history: list = None) -> str:
    """
    Mengirimkan prompt pengguna ke OpenAI GPT model dan mengembalikan respons,
    dengan kemampuan memanggil tool untuk interaksi dengan Google Sheets via Google Apps Script
    untuk GRIND Jiujitsu Indonesia BJJ chatbot.
    """
    if chat_history is None:
        chat_history = []

    messages = [
        {"role": "system", "content": f"""
        {SYSTEM_PROMPT}
        
        **BOOKING FEATURES:**
        ✅ Trial class booking (GRATIS!)
        ✅ Check ketersediaan slot  
        ✅ Cancel booking
        
        **BOOKING FLOW:**
        1. Tanya nama, kontak, tanggal, jam, jenis kelas
        2. Convert format: tanggal ke YYYY-MM-DD, jam ke HH:MM
        3. Jam operasional: 07:00-21:00 daily
        4. Durasi kelas: 60 menit
        5. Sukses booking → kasih info lokasi & contact
        
        **STYLE GUIDE:**
        - Max 2-3 kalimat per response
        - Pakai emoji yang tepat
        - Friendly & antusias! 
        - Info panjang → pecah jadi beberapa chat
        """}
    ]

    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL, 
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=MAX_TOKENS 
        )
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            tool_calls = response_message.tool_calls
            
            # Mengubah response_message menjadi dictionary yang eksplisit
            assistant_message_for_history = {
                "role": response_message.role,
                "content": response_message.content,
                "tool_calls": [tc.model_dump() for tc in tool_calls]
            }
            messages.append(assistant_message_for_history)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Panggil fungsi yang sesuai
                if function_name == "book_trial_class":
                    function_response = book_trial_class(**function_args)
                elif function_name == "cancel_booking":
                    function_response = cancel_booking(**function_args)
                elif function_name == "check_class_availability":
                    function_response = check_class_availability(**function_args)
                else:
                    function_response = f"Fungsi {function_name} tidak dikenali."
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

            final_response = openai_client.chat.completions.create(
                model=OPENAI_MODEL, 
                messages=messages,
                max_tokens=MAX_TOKENS
            )
            return final_response.choices[0].message.content
        else:
            return response_message.content

    except openai.APIConnectionError as e:
        st.error(f"Koneksi ke layanan AI gagal. Mohon periksa koneksi internet Anda.")
        print(f"[Backend Error] OpenAI API Connection Error: {e}") 
        return "Maaf, ada masalah koneksi dengan layanan AI. Mohon coba lagi nanti."
    except openai.RateLimitError as e:
        st.warning(f"Sistem sedang sibuk, mohon coba lagi sebentar.")
        print(f"[Backend Error] OpenAI Rate Limit Error: {e}")
        return "Maaf, batas penggunaan saya sudah tercapai. Mohon coba lagi sebentar."
    except openai.APIStatusError as e:
        st.error(f"Ada masalah dari layanan AI. Mohon coba lagi nanti.")
        print(f"[Backend Error] OpenAI API Status Error: Status Code {e.status_code} - Response: {e.response}")
        return f"Maaf, ada masalah dari layanan AI. Mohon coba lagi nanti."
    except Exception as e:
        st.error(f"Terjadi kesalahan yang tidak terduga. Kami sedang mengatasinya.")
        print(f"[Backend Error] Unexpected error in get_chatbot_response: {e}")
        return f"Maaf, terjadi kesalahan internal. Mohon coba lagi nanti."

# --- Streamlit UI ---
st.set_page_config(page_title="GRIND Jiujitsu Indonesia Chatbot", page_icon="🥋")
st.title("Selamat Datang di GRIND Jiujitsu Indonesia! 🥋")
st.markdown("Saya siap bantu Anda seputar informasi Brazilian Jiu-Jitsu, kelas, pricing, lokasi kami, dan **booking trial class GRATIS**! 🆓")

# Inisialisasi chat history di session state jika belum ada
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan pesan dari chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input dari pengguna
user_prompt = st.chat_input("Ada yang bisa saya bantu tentang GRIND BJJ?")
if user_prompt:
    # Tambahkan pesan pengguna ke chat history
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Dapatkan respons dari chatbot
    with st.chat_message("assistant"):
        with st.spinner("Sedang memproses..."):
            filtered_chat_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages
                if msg["role"] in ["user", "assistant"]
            ]

            full_response = get_chatbot_response(user_prompt, filtered_chat_history)
            st.markdown(full_response)
    
    # Tambahkan respons chatbot ke chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})