import streamlit as st
import sqlite3, requests, base64, hashlib, time, threading
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="VK AutoPoster PRO")
st.title("🤖 VK AutoPoster PRO v8.0 — АВТОПОСТИНГ!")

SECRET_KEY = b'KatePro2026KatePro2026KatePro2026KateP'

# База данных
@st.cache_resource
def init_db():
    conn = sqlite3.connect('vkbot.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, password TEXT, license_date TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
        email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, message TEXT, delay INTEGER)''')
    return conn

db = init_db()

def decrypt_token(token_b64):
    try:
        decoded = base64.b64decode(token_b64.encode())
        return bytes(b ^ SECRET_KEY[i % len(SECRET_KEY)] for i, b in enumerate(decoded)).decode()
    except:
        return token_b64

# Инициализация
if 'user' not in st.session_state: st.session_state.user = None
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'post_count' not in st.session_state: st.session_state.post_count = 0

# АДМИНКА
with st.sidebar:
    if st.button("🔧 АДМИН"):
        st.session_state.show_admin = True

if st.session_state.get('show_admin', False):
    st.header("🔧 АДМИНКА")
    if st.text_input("Пароль", type="password") == "kate2026":
        email = st.text_input("Клиент email")
        days = st.number_input("Дней", 1, 365, 30)
        if st.button("ПРОДЛИТЬ"):
            cur = db.cursor()
            new_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            cur.execute("UPDATE users SET license_date=? WHERE email=?", (new_date, email))
            db.commit()
            st.success(f"✅ {email} до {new_date}")

# ЛОГИН
if not st.session_state.user:
    st.header("🔐 АВТОРИЗАЦИЯ")
    col1, col2 = st.columns(2)
    
    with col1:
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Пароль", type="password")
        if st.button("✅ ВОЙТИ"):
            cur = db.cursor()
            cur.execute("SELECT license_date FROM users WHERE email=? AND password=?", 
                       (email, hashlib.sha256(password.encode()).hexdigest()))
            user = cur.fetchone()
            if user:
                st.session_state.user = email
                st.session_state.license = user[0]
                st.success(f"✅ {email}")
    
    with col2:
        reg_email = st.text_input("📧 Регистрация")
        reg_pass = st.text_input("🔑 Пароль", type="password")
        if st.button("➕ СОЗДАТЬ"):
            try:
                cur = db.cursor()
                license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                cur.execute("INSERT INTO users VALUES (?, ?, ?)", 
                           (reg_email, hashlib.sha256(reg_pass.encode()).hexdigest(), license_date))
                db.commit()
                st.success(f"✅ Создан до {license_date}")
            except:
                st.error("❌ Уже есть")
else:
    # ГЛАВНЫЙ ЭКРАН
    col_info, col_exit = st.columns([3,1])
    with col_info:
        st.success(f"👤 **{st.session_state.user}** | 📅 **{st.session_state.license}**")
    with col_exit:
        if st.button("🚪 ВЫХОД", use_container_width=True):
            st.session_state.user = None
            st.session_state.is_running = False
            st.rerun()
    
    st.subheader("⚙️ НАСТРОЙКИ")
    
    # Настройки
    cur = db.cursor()
    cur.execute("SELECT tokens, groups, message, delay FROM settings WHERE email=?", (st.session_state.user,))
    config = cur.fetchone()
    
    col1, col2 = st.columns(2)
    with col1:
        tokens = st.text_area("🔐 ТОКЕНЫ", value=config[0] if config else "", height=80, key="tokens")
        groups = st.text_input("📂 ГРУППЫ (через ,)", value=config[1] if config else "-231630927", key="groups")
    
    with col2:
        message = st.text_area("📝 ТЕКСТ", value=config[2] if config else "🚀 Автопостинг работает!", height=80, key="msg")
        delay = st.slider("⏱️ ЗАДЕРЖКА (сек)", 10, 300, config[3] if config else 30, key="delay")
    
    col_save, col_test = st.columns(2)
    with col_save:
        if st.button("💾 СОХРАНИТЬ", use_container_width=True):
            cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?, ?)",
                       (st.session_state.user, tokens, groups, message, delay))
            db.commit()
            st.success("✅ Сохранено!")
    
    with col_test:
        if st.button("🔍 ПРОВЕРИТЬ ТОКЕНЫ", use_container_width=True):
            token = decrypt_token(tokens.strip())
            st.info(f"**Статус:** {'✅ ВАЛИДЕН' if 'vk1.a.' in token else '❌ НЕ ВАЛИДЕН'}")
    
    # УПРАВЛЕНИЕ ПОСТИНГОМ
    st.subheader("🚀 АВТОПОСТИНГ")
    
    col_start, col_stop, col_status = st.columns([2,2,2])
    
    with col_start:
        if st.button("▶️ НАЧАТЬ АВТОПОСТИНГ", use_container_width=True):
            st.session_state.tokens_list = [decrypt_token(t.strip()) for t in tokens.split(',') if 'vk1.a.' in decrypt_token(t.strip())]
            st.session_state.groups_list = [g.strip() for g in groups.split(',') if g.strip()]
            st.session_state.post_message = message
            st.session_state.post_delay = delay
            st.session_state.is_running = True
            st.session_state.post_count = 0
            st.success("🚀 ЗАПУЩЕНО!")
    
    with col_stop:
        if st.button("⏹️ ОСТАНОВИТЬ", use_container_width=True):
            st.session_state.is_running = False
            st.success("🛑 ОСТАНОВЛЕНО!")
    
    with col_status:
        status = "🟢 АКТИВЕН" if st.session_state.is_running else "🔴 ОСТАНОВЛЕН"
        st.metric("Статус", status)
        st.metric("📊 Постов", st.session_state.post_count)
    
    # АВТОПОСТИНГ ЛОГИКА
    if st.session_state.is_running and hasattr(st.session_state, 'tokens_list'):
        st.info("**🎉 АВТОПОСТИНГ РАБОТАЕТ!**")
        
        def auto_post():
            while st.session_state.is_running:
                for token in st.session_state.tokens_list:
                    for group in st.session_state.groups_list:
                        if not st.session_state.is_running:
                            break
                        
                        try:
                            data = {
                                'owner_id': group,
                                'from_group': 1,
                                'message': st.session_state.post_message[:4000],
                                'access_token': token,
                                'v': '5.131'
                            }
                            resp = requests.post("https://api.vk.com/method/wall.post", data=data, timeout=20).json()
                            
                            if 'response' in resp:
                                st.session_state.post_count += 1
                                st.success(f"✅ #{resp['response']['post_id']} → {group}")
                            else:
                                st.error(f"❌ {group}: {resp.get('error', {}).get('error_msg', '')}")
                        except Exception as e:
                            st.error(f"🌐 {str(e)[:50]}")
                        
                        time.sleep(st.session_state.post_delay)
                
                if st.session_state.is_running:
                    st.rerun()
        
        if 'post_thread' not in st.session_state:
            st.session_state.post_thread = threading.Thread(target=auto_post, daemon=True)
            st.session_state.post_thread.start()
    
    # ЛОГИ
    st.subheader("📋 ПОСЛЕДНИЕ ДЕЙСТВИЯ")
    if st.session_state.post_count > 0:
        st.success(f"🎉 Всего постов: **{st.session_state.post_count}**")
