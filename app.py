import streamlit as st
import sqlite3
import requests
import base64
import hashlib
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🔥 VK WEB BOT — РАБОТАЕТ!")

# База данных
conn = sqlite3.connect('bot.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS users 
                (email TEXT PRIMARY KEY, password TEXT, license_date TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS settings 
                (email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, message TEXT)''')
conn.commit()

SECRET_KEY = b'KatePro2026KatePro2026KatePro2026KateP'

def decrypt_token(token_b64):
    try:
        decoded = base64.b64decode(token_b64.encode())
        result = bytes(b ^ SECRET_KEY[i % len(SECRET_KEY)] for i, b in enumerate(decoded))
        return result.decode('utf-8')
    except:
        return token_b64

# === ОСНОВНОЙ ИНТЕРФЕЙС ===
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("👤 АВТОРИЗАЦИЯ")
    
    # Вход
    email = st.text_input("📧 Email", key="email_login")
    password = st.text_input("🔑 Пароль", type="password", key="pass_login")
    
    if st.button("🚀 ВОЙТИ", key="btn_login"):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", 
                      (email, hashlib.sha256(password.encode()).hexdigest()))
        user = cursor.fetchone()
        if user:
            st.session_state['current_user'] = email
            st.success(f"✅ Вошел: {email}")
            st.rerun()
        else:
            st.error("❌ Неверно!")
    
    # Регистрация
    st.markdown("---")
    new_email = st.text_input("📧 Новый email", key="new_email")
    new_pass = st.text_input("🔑 Новый пароль", type="password", key="new_pass")
    
    if st.button("➕ РЕГИСТРАЦИЯ", key="btn_register"):
        try:
            cursor = conn.cursor()
            license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            pwd_hash = hashlib.sha256(new_pass.encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?, ?, ?)", 
                          (new_email, pwd_hash, license_date))
            conn.commit()
            st.success(f"✅ Зарегистрирован {new_email}! Лицензия до {license_date}")
            st.session_state['current_user'] = new_email
            st.rerun()
        except:
            st.error("❌ Email занят!")

with col2:
    st.subheader("⚙️ НАСТРОЙКИ БОТА")
    
    if 'current_user' in st.session_state:
        user_email = st.session_state['current_user']
        st.info(f"👤 **{user_email}**")
        
        # Загрузка настроек
        cursor = conn.cursor()
        cursor.execute("SELECT tokens, groups, message FROM settings WHERE email=?", (user_email,))
        config = cursor.fetchone()
        
        tokens = st.text_area("🔐 ТОКЕНЫ Base64", 
                             value=config[0] if config else "", 
                             height=80, key="tokens_field")
        
        groups = st.text_input("📂 ГРУППЫ (через запятую)", 
                              value=config[1] if config else "-231630927", 
                              key="groups_field")
        
        message = st.text_area("📝 ТЕКСТ ПОСТА", 
                              value=config[2] if config else "Привет от веб-бота!", 
                              height=80, key="message_field")
        
        col_save, col_test = st.columns(2)
        
        with col_save:
            if st.button("💾 СОХРАНИТЬ", key="save_settings"):
                cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)",
                              (user_email, tokens, groups, message))
                conn.commit()
                st.success("✅ Сохранено!")
        
        with col_test:
            if st.button("📤 ТЕСТ ПОСТ", key="test_post"):
                if tokens.strip():
                    token = decrypt_token(tokens)
                    if 'vk1.a.' in token:
                        try:
                            response = requests.post("https://api.vk.com/method/wall.post", data={
                                'owner_id': groups.split(',')[0].strip(),
                                'message': message[:4000],
                                'access_token': token,
                                'v': '5.131'
                            }, timeout=15).json()
                            
                            if 'response' in response:
                                post_id = response['response']['post_id']
                                st.success(f"✅ 🎉 ПОСТ #{post_id} ОТПРАВЛЕН!")
                                cursor.execute("INSERT INTO posts VALUES (?, ?, ?, ?)",
                                             (user_email, groups.split(',')[0].strip(), post_id, 'success'))
                                conn.commit()
                            else:
                                st.error(f"❌ VK: {response.get('error', {}).get('error_msg', 'Ошибка')}")
                        except Exception as e:
                            st.error(f"🌐 {str(e)[:60]}")
                    else:
                        st.error("❌ Токен не расшифровался!")
                else:
                    st.error("⚠️ Вставь токены!")
    else:
        st.warning("🔐 **Сначала войди или зарегистрируйся слева!**")

st.markdown("---")
st.caption("🚀 VK Web Bot PRO v5.0 — 100% работает!")
