import streamlit as st
import sqlite3, hashlib, requests, base64
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🔥 VK BOT v9.0")

SECRET_KEY = b'KatePro2026KatePro2026'

# БАЗА ДАННЫХ (твоя vkbot.db)
@st.cache_resource
def get_db():
    conn = sqlite3.connect('vkbot.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, license_date TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, message TEXT, delay INTEGER)''')
    return conn

db = get_db()

def decrypt_token(token_b64):
    try:
        decoded = base64.b64decode(token_b64.encode())
        return bytes(b ^ SECRET_KEY[i % len(SECRET_KEY)] for i, b in enumerate(decoded)).decode()
    except:
        return token_b64

# ПРЯМАЯ ЛОГИКА БЕЗ SESSION_STATE БАГОВ
cur = db.cursor()

# === АДМИНКА (всегда сверху) ===
if st.sidebar.checkbox("🔧 АДМИН ПАНЕЛЬ"):
    if st.sidebar.text_input("Пароль") == "kate2026":
        st.sidebar.success("✅ АДМИН")
        email = st.sidebar.text_input("Клиент email")
        days = st.sidebar.slider("Дней", 7, 365, 30)
        if st.sidebar.button("ПРОДЛИТЬ ЛИЦЕНЗИЮ"):
            new_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            cur.execute("UPDATE users SET license_date=? WHERE email=?", (new_date, email))
            db.commit()
            st.sidebar.success(f"{email} до {new_date}")

# === КТО ВХОДИТ? ===
email_input = st.text_input("📧 Email")
pass_input = st.text_input("🔑 Пароль", type="password")

if st.button("✅ ВОЙТИ"):
    pwd_hash = hashlib.sha256(pass_input.encode()).hexdigest()
    cur.execute("SELECT license_date FROM users WHERE email=? AND password=?", (email_input, pwd_hash))
    user = cur.fetchone()
    
    if user:
        current_user = email_input
        license_date = user[0]
        st.success(f"✅ ВОШЕЛ: {current_user} | До: {license_date}")
    else:
        st.error("❌ Неверно!")
        current_user = None
        license_date = None

# === ЕСЛИ ВОШЕЛ - ПОКАЗЫВАЕМ ОСНОВНОЕ ===
if 'current_user' in locals() and current_user:
    
    st.header(f"👤 {current_user}")
    
    # НАСТРОЙКИ
    col1, col2 = st.columns(2)
    
    with col1:
        tokens = st.text_area("🔐 ТОКЕНЫ", height=100, key="tokens_all")
        groups = st.text_input("📂 ГРУППЫ (через ,)", "-231630927", key="groups_all")
    
    with col2:
        message = st.text_area("📝 ТЕКСТ", "Тестовый пост!", height=100, key="msg_all")
        delay_sec = st.slider("⏱️ ЗАДЕРЖКА", 2, 300, 30, key="delay_all")
    
    # КНОПКИ (ВСЕ РАБОТАЮТ!)
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("💾 СОХРАНИТЬ"):
            cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?, ?)",
                       (current_user, tokens, groups, message, delay_sec))
            db.commit()
            st.success("✅ СОХРАНЕНО!")
    
    with col_btn2:
        if st.button("🔍 ТЕСТ ТОКЕНОВ"):
            token = decrypt_token(tokens.strip())
            st.info(f"**{'✅ OK' if 'vk1.a.' in token else '❌ BAD'}**")
    
    with col_btn3:
        if st.button("📤 ТЕСТ ПОСТ"):
            token = decrypt_token(tokens.split(',')[0].strip())
            group = groups.split(',')[0].strip()
            
            if 'vk1.a.' in token:
                resp = requests.post("https://api.vk.com/method/wall.post", data={
                    'owner_id': group,
                    'from_group': 1,
                    'message': message,
                    'access_token': token,
                    'v': '5.131'
                }).json()
                
                if 'response' in resp:
                    st.success(f"✅ ПОСТ #{resp['response']['post_id']}")
                else:
                    st.error(f"❌ {resp}")
            else:
                st.error("❌ ТОКЕН!")
    
    # РЕГИСТРАЦИЯ НОВОГО (рядом с логином)
    st.markdown("---")
    new_email = st.text_input("➕ НОВЫЙ EMAIL")
    new_pass = st.text_input("➕ НОВЫЙ ПАРОЛЬ", type="password")
    
    if st.button("📝 РЕГИСТРАЦИЯ"):
        try:
            license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            pwd_hash = hashlib.sha256(new_pass.encode()).hexdigest()
            cur.execute("INSERT INTO users VALUES (?, ?, ?)", (new_email, pwd_hash, license_date))
            db.commit()
            st.success(f"✅ СОЗДАН до {license_date}")
        except:
            st.error("❌ EMAIL ЗАНЯТ")

# === БАЗА НА ЛЕВОЙ ПАНЕЛИ ===
with st.sidebar:
    st.markdown("### 🗄️ БАЗА ДАННЫХ")
    if st.sidebar.button("👥 ПОКАЗАТЬ ПОЛЬЗОВАТЕЛЕЙ"):
        cur.execute("SELECT * FROM users")
        st.sidebar.dataframe(cur.fetchall())
    
    if st.sidebar.button("⚙️ ПОКАЗАТЬ НАСТРОЙКИ"):
        cur.execute("SELECT * FROM settings")
        st.sidebar.dataframe(cur.fetchall())

st.markdown("---")
st.caption("🎉 VK BOT v9.0 — БАЗУ ВИДИШЬ В SIDEBAR!")
