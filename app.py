import streamlit as st
import sqlite3, requests, base64, hashlib
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🤖 VK AutoPoster WEB PRO")

# База данных
@st.cache_resource
def get_db():
    conn = sqlite3.connect('data.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, pass TEXT, license TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS settings (email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, msg TEXT)')
    return conn

db = get_db()

SECRET_KEY = b'KatePro2026KatePro2026KatePro2026KateP'

def decrypt_token(token_b64):
    try:
        decoded = base64.b64decode(token_b64)
        result = bytes(a ^ SECRET_KEY[i % len(SECRET_KEY)] for i, a in enumerate(decoded))
        return result.decode()
    except:
        return token_b64

# === ОСНОВНОЙ ИНТЕРФЕЙС ===
tab1, tab2 = st.tabs(["🚀 Авторизация", "⚙️ Настройки"])

with tab1:
    st.subheader("👤 Вход / Регистрация")
    
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Email")
        passwd = st.text_input("Пароль", type="password")
        if st.button("Войти"):
            cur = db.cursor()
            cur.execute("SELECT license FROM users WHERE email=? AND pass=?", 
                       (email, hashlib.sha256(passwd.encode()).hexdigest()))
            user = cur.fetchone()
            if user:
                st.session_state.email = email
                st.success(f"✅ Вошел: {email}")
            else:
                st.error("❌ Неверно")
    
    with col2:
        reg_email = st.text_input("Регистрация Email")
        reg_pass = st.text_input("Регистрация пароль", type="password")
        if st.button("Зарегистрироваться"):
            try:
                cur = db.cursor()
                license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                cur.execute("INSERT INTO users VALUES (?, ?, ?)", 
                           (reg_email, hashlib.sha256(reg_pass.encode()).hexdigest(), license_date))
                db.commit()
                st.session_state.email = reg_email
                st.success("✅ Регистрация OK! Лицензия 7 дней")
            except:
                st.error("❌ Email занят")

with tab2:
    if 'email' in st.session_state:
        st.success(f"👤 {st.session_state.email}")
        
        # Настройки
        cur = db.cursor()
        cur.execute("SELECT tokens, groups, msg FROM settings WHERE email=?", (st.session_state.email,))
        sett = cur.fetchone()
        
        tokens = st.text_area("🔐 Токены Base64", value=sett[0] if sett else "", height=100)
        groups = st.text_input("📂 Группы", value=sett[1] if sett else "-231630927")
        message = st.text_area("📝 Текст поста", value=sett[2] if sett else "Привет от WEB бота!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Сохранить"):
                cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)", 
                           (st.session_state.email, tokens, groups, message))
                db.commit()
                st.success("✅ Сохранено!")
        
        with col2:
            if st.button("🔓 Проверить токены"):
                decoded = decrypt_token(tokens)
                if 'vk1.a.' in decoded:
                    st.success("✅ Токен валиден!")
                else:
                    st.error("❌ Проверь токен")
        
        if st.button("📤 Тестовый пост"):
            token = decrypt_token(tokens)
            if 'vk1.a.' in token:
                r = requests.post("https://api.vk.com/method/wall.post", data={
                    'owner_id': groups,
                    'message': message,
                    'access_token': token,
                    'v': '5.131'
                }).json()
                
                if 'response' in r:
                    st.success(f"✅ Пост #{r['response']['post_id']} отправлен!")
                else:
                    st.error(f"❌ {r}")
            else:
                st.error("❌ Нет токена!")
    else:
        st.warning("👈 Сначала войди или зарегистрируйся!")
