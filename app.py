import streamlit as st
import sqlite3, requests, base64, hashlib, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="VK AutoPoster PRO")
st.title("🤖 VK AutoPoster PRO v8.2")

SECRET_KEY = b'KatePro2026KatePro2026KatePro2026KateP'

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
if 'initialized' not in st.session_state:
    st.session_state.user = None
    st.session_state.license_date = None
    st.session_state.is_running = False
    st.session_state.post_count = 0
    st.session_state.initialized = True

# АДМИНКА
with st.sidebar:
    st.markdown("### 🔧 АДМИН")
    if st.text_input("Пароль", type="password", key="sidebar_admin_pass") == "kate2026":
        st.success("✅ АДМИН ОК")
        email = st.text_input("Клиент", key="sidebar_admin_email")
        days = st.slider("Дней", 7, 365, 30, key="sidebar_admin_days")
        if st.button("ПРОДЛИТЬ", key="sidebar_admin_prolong"):
            cur = db.cursor()
            new_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            cur.execute("UPDATE users SET license_date=? WHERE email=?", (new_date, email))
            db.commit()
            st.success(f"{email} до {new_date}")

# ЛОГИН ЭКРАН
if not st.session_state.user:
    st.header("🔐 АВТОРИЗАЦИЯ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("ВОЙТИ")
        email = st.text_input("📧 Email", key="login_email_v1")
        passwd = st.text_input("🔑 Пароль", type="password", key="login_pass_v1")
        
        if st.button("✅ ВОЙТИ", key="login_submit_v1"):
            cur = db.cursor()
            cur.execute("SELECT license_date FROM users WHERE email=? AND password=?", 
                       (email, hashlib.sha256(passwd.encode()).hexdigest()))
            user = cur.fetchone()
            if user:
                st.session_state.user = email
                st.session_state.license_date = user[0]
                st.rerun()  # ПЕРЕХОД БЕЗ СООБЩЕНИЙ
            else:
                st.error("❌ Неверно")
    
    with col2:
        st.subheader("РЕГИСТРАЦИЯ")
        reg_email = st.text_input("📧 Email", key="reg_email_v1")
        reg_pass = st.text_input("🔑 Пароль", type="password", key="reg_pass_v1")
        
        if st.button("➕ СОЗДАТЬ", key="reg_submit_v1"):
            try:
                cur = db.cursor()
                license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                pwd_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
                cur.execute("INSERT INTO users VALUES (?, ?, ?)", (reg_email, pwd_hash, license_date))
                db.commit()
                st.session_state.user = reg_email
                st.session_state.license_date = license_date
                st.rerun()  # ПЕРЕХОД БЕЗ СООБЩЕНИЙ
            except:
                st.error("❌ Занят")
else:
    # ГЛАВНЫЙ ЭКРАН - ВСЕ КНОПКИ!
    st.header(f"👤 {st.session_state.user}")
    col_main, col_exit = st.columns([3,1])
    
    with col_main:
        st.info(f"📅 Лицензия: **{st.session_state.license_date}**")
    with col_exit:
        if st.button("🚪 ВЫХОД", use_container_width=True, key="logout_v1"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # НАСТРОЙКИ
    st.subheader("⚙️ НАСТРОЙКИ")
    
    cur = db.cursor()
    cur.execute("SELECT tokens, groups, message, delay FROM settings WHERE email=?", (st.session_state.user,))
    config = cur.fetchone()
    
    col1, col2 = st.columns(2)
    with col1:
        tokens = st.text_area("🔐 ТОКЕНЫ", value=config[0] if config else "", height=100, key="tokens_main")
        groups = st.text_input("📂 ГРУППЫ", value=config[1] if config else "-231630927", key="groups_main")
    
    with col2:
        message = st.text_area("📝 СООБЩЕНИЕ", value=config[2] if config else "Автопостинг v8.2!", height=100, key="msg_main")
        delay = st.slider("⏱️ ЗАДЕРЖКА", 2, 300, config[3] if config else 30, key="delay_main")
    
    # КНОПКИ НАСТРОЕК
    col_save, col_test = st.columns(2)
    with col_save:
        if st.button("💾 СОХРАНИТЬ", use_container_width=True, key="save_main"):
            cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?, ?)",
                       (st.session_state.user, tokens, groups, message, delay))
            db.commit()
            st.success("СОХРАНЕНО!")
    
    with col_test:
        if st.button("🔍 ПРОВЕРИТЬ ТОКЕНЫ", use_container_width=True, key="check_tokens_main"):
            token = decrypt_token(tokens.strip())
            st.info(f"**{'✅ ВАЛИДЕН' if 'vk1.a.' in token else '❌ НЕ ВАЛИДЕН'}**")
    
    # АВТОПОСТИНГ
    st.markdown("---")
    st.subheader("🚀 АВТОПОСТИНГ")
    
    col_start, col_stop, col_status = st.columns(3)
    
    with col_start:
        if st.button("▶️ НАЧАТЬ", use_container_width=True, key="start_posting"):
            tokens_list = [decrypt_token(t.strip()) for t in tokens.split(',') if 'vk1.a.' in decrypt_token(t.strip())]
            groups_list = [g.strip() for g in groups.split(',') if g.strip()]
            if tokens_list and groups_list:
                st.session_state.tokens_list = tokens_list
                st.session_state.groups_list = groups_list
                st.session_state.post_message = message
                st.session_state.post_delay = delay
                st.session_state.is_running = True
                st.session_state.post_count = 0
                st.success("ЗАПУЩЕНО!")
            else:
                st.error("ТОКЕНЫ/ГРУППЫ!")
    
    with col_stop:
        if st.button("⏹️ СТОП", use_container_width=True, key="stop_posting"):
            st.session_state.is_running = False
            st.success("ОСТАНОВЛЕНО!")
    
    with col_status:
        status = "🟢 РАБОТАЕТ" if st.session_state.is_running else "🔴 ОСТАНОВЛЕНО"
        st.metric("Статус", status)
        st.metric("Постов", st.session_state.post_count)
    
    # ТЕСТОВЫЙ ПОСТ
    if st.button("📤 ТЕСТ ПОСТ", use_container_width=True, key="test_post_main"):
        token = decrypt_token(tokens.split(',')[0].strip())
        group = groups.split(',')[0].strip()
        if 'vk1.a.' in token:
            data = {
                'owner_id': group,
                'from_group': 1,
                'message': message,
                'access_token': token,
                'v': '5.131'
            }
            resp = requests.post("https://api.vk.com/method/wall.post", data=data).json()
            if 'response' in resp:
                st.success(f"✅ ПОСТ #{resp['response']['post_id']}")
                st.session_state.post_count += 1
            else:
                st.error(f"❌ {resp}")
        else:
            st.error("❌ ТОКЕН!")

st.markdown("---")
st.caption("🎉 VK AutoPoster PRO v8.2")
