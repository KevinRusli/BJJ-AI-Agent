import openai
import os
from dotenv import load_dotenv
import streamlit as st 
from config import SYSTEM_PROMPT, OPENAI_MODEL, MAX_TOKENS

# Muat variabel lingkungan dari .env file
load_dotenv()

# Pastikan API Key OpenAI sudah diatur sebagai environment variable
try:
    openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"]) 
except KeyError:
    st.error("OPENAI_API_KEY environment variable not set. Please create a .env file or set it in your system.")
    st.stop() 

# --- Fungsi Utama Chatbot untuk BJJ (Tanpa Tool Calling) ---
def get_chatbot_response(user_prompt: str, chat_history: list = None) -> str:
    """
    Mengirimkan prompt pengguna ke OpenAI GPT model dan mengembalikan respons
    untuk GRIND Jiujitsu Indonesia BJJ chatbot.
    """
    if chat_history is None:
        chat_history = []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL, 
            messages=messages,
            max_tokens=MAX_TOKENS 
        )
        return response.choices[0].message.content

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
st.markdown("Saya siap bantu Anda seputar informasi Brazilian Jiu-Jitsu, kelas, pricing, dan lokasi kami.")

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