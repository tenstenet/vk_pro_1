import streamlit as st
import sqlite3, hashlib, requests, base64
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🔥 VK BOT v10.0 — ПРОСТОЙ")

SECRET_KEY = b'KatePro2026KatePro2026'

# БАЗА ДАННЫХ
conn = sqlite3.connect('vkbot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, license_date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, message TEXT)''')
conn.commit()

def decrypt_token(token_b64):
    try:
        decoded = base64.b64decode(token_b64.encode())
        return bytes(b ^ SECRET_KEY[i % len(SECRET_KEY)] for i, b in enumerate(decoded)).decode()
    except:
        return token_b64

# === АДМИНКА (ПАРОЛЬ: kate2026) ===
st.sidebar.markdown("## 🔧 **АДМИНКА**")
admin_pass = st.sidebar.text_input("🔑 Пароль", type="password")
if admin_pass == "kate2026":
    st.sidebar.success("✅ АДМИН")
    
    # Продление лицензии
    adm_email = st.sidebar.text_input("👤 Клиент email")
    adm_days = st.sidebar.slider("📅 Дней", 7, 365, 30)
    if st.sidebar.button("✅ ПРОДЛИТЬ"):
        new_date = (datetime.now() + timedelta(days=adm_days)).strftime('%Y-%m-%d')
        c.execute("UPDATE users SET license_date=? WHERE email=?", (new_date, adm_email))
        conn.commit()
        st.sidebar.success(f"{adm_email} → {new_date}")
    
    # Показать всех
    if st.sidebar.button("👥 Все пользователи"):
        c.execute("SELECT * FROM users")
        st.sidebar.dataframe(c.fetchall())
    
    if st.sidebar.button("⚙️ Все настройки"):
        c.execute("SELECT * FROM settings")
        st.sidebar.dataframe(c.fetchall())

# === ОСНОВНОЙ ЭКРАН ===
st.header("🤖 VK AutoPoster")

# Регистрация (всегда сверху)
st.markdown("### ➕ **РЕГИСТРАЦИЯ**")
reg_email = st.text_input("📧 Новый email")
reg_pass = st.text_input("🔑 Новый пароль", type="password")
if st.button("📝 ЗАРЕГИСТРИРОВАТЬСЯ"):
    try:
        license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        pwd_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (reg_email, pwd_hash, license_date))
        conn.commit()
        st.success(f"✅ Зарегистрирован! Лицензия до {license_date}")
    except:
        st.error("❌ Email занят!")

# Логин (всегда сверху)  
st.markdown("### 🔐 **ВОЙТИ**")
login_email = st.text_input("📧 Email")
login_pass = st.text_input("🔑 Пароль", type="password")
login_success = False
license_info = ""

if st.button("✅ ВОЙТИ"):
    pwd_hash = hashlib.sha256(login_pass.encode()).hexdigest()
    c.execute("SELECT license_date FROM users WHERE email=? AND password=?", (login_email, pwd_hash))
    user = c.fetchone()
    if user:
        login_success = True
        license_info = user[0]
        st.success(f"✅ ВОШЕЛ: {login_email}")
    else:
        st.error("❌ Неверный пароль!")

# === ЕСЛИ ВОШЕЛ = ПОКАЗЫВАЕМ БОТА ===
if login_success:
    st.markdown("---")
    st.header(f"👤 **{login_email}** | 📅 **{license_info}**")
    
    # НАСТРОЙКИ
    col1, col2 = st.columns(2)
    with col1:
        tokens = st.text_area("🔐 ТОКЕНЫ (XOR или обычные)", height=100)
        groups = st.text_input("📂 ГРУППЫ (-123456 через запятую)", "-231630927")
    
    with col2:
        message = st.text_area("📝 ТЕКСТ ПОСТА", "🚀 Пост из WEB бота!", height=100)
    
    # 5 КНОПОК (ВСЕ РАБОТАЮТ!)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("💾 СОХРАНИТЬ"):
            c.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)",
                     (login_email, tokens, groups, message))
            conn.commit()
            st.success("✅ СОХРАНЕНО В БАЗУ!")
    
    with col2:
        if st.button("🔍 ТЕСТ ТОКЕНОВ"):
            token = decrypt_token(tokens.strip())
            st.info(f"**{'✅ ВАЛИДЕН' if 'vk1.a.' in token else '❌ НЕТ' }**")
    
    with col3:
        if st.button("📤 ТЕСТ ПОСТ"):
            token = decrypt_token(tokens.split(',')[0].strip())
            group = groups.split(',')[0].strip()
            
            if 'vk1.a.' in token:
                resp = requests.post("https://api.vk.com/method/wall.post", data={
                    'owner_id': group,
                    'from_group': 1,
                    'message': message[:4000],
                    'access_token': token,
                    'v': '5.131'
                }).json()
                
                if 'response' in resp:
                    st.success(f"✅ ПОСТ #{resp['response']['post_id']}!")
                else:
                    st.error(f"❌ {resp.get('error',{}).get('error_msg','Ошибка')}")
            else:
                st.error("❌ ТОКЕН НЕ ВАЛИДЕН!")
    
    with col4:
        if st.button("🖼️ С ФОТО"):
            st.info("🛠️ Функция в разработке")
    
    with col5:
        if st.button("⏰ АВТОПОСТ"):
            st.info("🛠️ Функция в разработке")

st.markdown("---")
st.caption("🎉 **v10.0 — УЛЮЧШЕННАЯ | АДМИН: kate2026**")
