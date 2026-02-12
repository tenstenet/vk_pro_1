import streamlit as st
import sqlite3, requests, base64, hashlib, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="VK AutoPoster PRO")
st.title("🤖 VK AutoPoster PRO v8.1")

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

# Инициализация состояния
if 'user' not in st.session_state:
    st.session_state.user = None
if 'license_date' not in st.session_state:
    st.session_state.license_date = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'post_count' not in st.session_state:
    st.session_state.post_count = 0

# АДМИНКА - боковая панель
with st.sidebar:
    st.markdown("### 🔧 **АДМИН**")
    admin_pass = st.text_input("Пароль", type="password", key="admin_pass")
    if admin_pass == "kate2026":
        st.success("✅ АДМИН")
        email_input = st.text_input("Клиент email", key="admin_email")
        days_input = st.slider("Дней лицензии", 7, 365, 30, key="admin_days")
        if st.button("✅ ПРОДЛИТЬ", key="admin_prolong"):
            cur = db.cursor()
            new_date = (datetime.now() + timedelta(days=days_input)).strftime('%Y-%m-%d')
            cur.execute("UPDATE users SET license_date=? WHERE email=?", (new_date, email_input))
            db.commit()
            st.success(f"✅ {email_input} до {new_date}")
        
        st.markdown("---")
        if st.button("📊 Все клиенты", key="admin_users"):
            cur = db.cursor()
            cur.execute("SELECT * FROM users ORDER BY license_date DESC")
            st.dataframe(cur.fetchall())

# ОСНОВНОЙ ИНТЕРФЕЙС
if not st.session_state.user:
    st.header("🔐 **ВОЙТИ / РЕГИСТРАЦИЯ**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 **ВОЙТИ**")
        login_email = st.text_input("📧 Email", key="login_email_unique1")
        login_pass = st.text_input("🔑 Пароль", type="password", key="login_pass_unique1")
        
        if st.button("✅ ВОЙТИ", key="login_btn_unique1"):
            cur = db.cursor()
            cur.execute("SELECT license_date FROM users WHERE email=? AND password=?", 
                       (login_email, hashlib.sha256(login_pass.encode()).hexdigest()))
            user = cur.fetchone()
            if user:
                st.session_state.user = login_email
                st.session_state.license_date = user[0]
                st.success(f"✅ Вошли: {login_email}")
            else:
                st.error("❌ Неверные данные")
    
    with col2:
        st.markdown("### ➕ **РЕГИСТРАЦИЯ**")
        reg_email = st.text_input("📧 Email", key="reg_email_unique1")
        reg_pass = st.text_input("🔑 Пароль", type="password", key="reg_pass_unique1")
        
        if st.button("📝 СОЗДАТЬ", key="reg_btn_unique1"):
            try:
                cur = db.cursor()
                license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                pwd_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
                cur.execute("INSERT INTO users VALUES (?, ?, ?)", (reg_email, pwd_hash, license_date))
                db.commit()
                st.success(f"✅ Создан! Лицензия до {license_date}")
                st.session_state.user = reg_email
                st.session_state.license_date = license_date
            except:
                st.error("❌ Email занят")
else:
    # ГЛАВНАЯ СТРАНИЦА ПОЛЬЗОВАТЕЛЯ
    st.header(f"👤 **{st.session_state.user}**")
    st.info(f"📅 Лицензия до: **{st.session_state.license_date}**")
    
    # КНОПКА ВЫХОДА
    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("🚪 ВЫХОД", use_container_width=True, key="logout_btn"):
            st.session_state.user = None
            st.session_state.license_date = None
            st.session_state.is_running = False
            st.rerun()
    
    st.subheader("⚙️ **НАСТРОЙКИ ПОСТИНГА**")
    
    # Загрузка настроек
    cur = db.cursor()
    cur.execute("SELECT tokens, groups, message, delay FROM settings WHERE email=?", (st.session_state.user,))
    config = cur.fetchone()
    
    col_settings1, col_settings2 = st.columns(2)
    
    with col_settings1:
        tokens = st.text_area("🔐 **ТОКЕНЫ** (Base64/XOR через запятую)", 
                             value=config[0] if config else "", height=80, key="tokens_field")
        groups = st.text_input("📂 **ГРУППЫ** (-123456 через запятую)", 
                              value=config[1] if config else "-231630927", key="groups_field")
    
    with col_settings2:
        message = st.text_area("📝 **ТЕКСТ ПОСТА**", 
                              value=config[2] if config else "🚀 Автопостинг из WEB PRO v8.1!", 
                              height=80, key="message_field")
        delay = st.slider("⏱️ **ЗАДЕРЖКА** (сек)", 2, 300, config[3] if config else 30, key="delay_field")
    
    # КНОПКИ НАСТРОЕК
    col_save, col_check = st.columns(2)
    with col_save:
        if st.button("💾 **СОХРАНИТЬ**", use_container_width=True, key="save_btn"):
            cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?, ?)",
                       (st.session_state.user, tokens, groups, message, delay))
            db.commit()
            st.success("✅ **НАСТРОЙКИ СОХРАНЕНЫ!**")
    
    with col_check:
        if st.button("🔍 **ПРОВЕРИТЬ ТОКЕНЫ**", use_container_width=True, key="check_btn"):
            tokens_list = []
            for t in tokens.split(','):
                real_token = decrypt_token(t.strip())
                if 'vk1.a.' in real_token:
                    tokens_list.append(real_token)
            st.info(f"✅ **{len(tokens_list)} валидных токенов** готово к постингу!")
    
    # УПРАВЛЕНИЕ АВТОПОСТИНГОМ
    st.markdown("---")
    st.subheader("🚀 **АВТОПОСТИНГ 24/7**")
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if st.button("▶️ **НАЧАТЬ АВТОПОСТИНГ**", use_container_width=True, key="start_auto"):
            tokens_list = []
            for t in tokens.split(','):
                real_token = decrypt_token(t.strip())
                if 'vk1.a.' in real_token:
                    tokens_list.append(real_token)
            
            groups_list = [g.strip() for g in groups.split(',') if g.strip()]
            
            if tokens_list and groups_list:
                st.session_state.tokens_list = tokens_list
                st.session_state.groups_list = groups_list
                st.session_state.post_message = message
                st.session_state.post_delay = delay
                st.session_state.is_running = True
                st.session_state.post_count = 0
                st.success("🚀 **АВТОПОСТИНГ ЗАПУЩЕН!**")
            else:
                st.error("❌ **Добавь токены и группы!**")
    
    with col2:
        if st.button("⏹️ **ОСТАНОВИТЬ**", use_container_width=True, key="stop_auto"):
            st.session_state.is_running = False
            st.success("🛑 **ОСТАНОВЛЕНО!**")
    
    with col3:
        status = "🟢 **АКТИВЕН**" if st.session_state.is_running else "🔴 **СТОП**"
        st.metric("📊 Статус", status)
        st.metric("📈 Постов", st.session_state.post_count)
    
    # ТЕСТОВЫЙ ПОСТ
    if st.button("📤 **ТЕСТОВЫЙ ПОСТ**", use_container_width=True, key="test_post_btn"):
        if tokens and groups:
            token = decrypt_token(tokens.split(',')[0].strip())
            group = groups.split(',')[0].strip()
            
            if 'vk1.a.' in token:
                data = {
                    'owner_id': group,
                    'from_group': 1,
                    'message': message[:4000],
                    'access_token': token,
                    'v': '5.131'
                }
                
                try:
                    resp = requests.post("https://api.vk.com/method/wall.post", data=data, timeout=20).json()
                    if 'response' in resp:
                        st.success(f"✅ **ПОСТ #{resp['response']['post_id']}** отправлен в {group}!")
                        st.session_state.post_count += 1
                    else:
                        st.error(f"❌ **VK API:** {resp.get('error', {}).get('error_msg', 'Ошибка')}")
                except Exception as e:
                    st.error(f"🌐 **{str(e)[:60]}**")
            else:
                st.error("❌ **Токен недействителен!**")
        else:
            st.error("❌ **Заполни токены и группы!**")
    
    # СТАТУС АВТОПОСТИНГА
    if st.session_state.is_running:
        st.balloons()
        st.markdown("**🎉 АВТОПОСТИНГ РАБОТАЕТ! Задержка: {} сек**".format(st.session_state.post_delay))

st.markdown("---")
st.caption("🎉 **VK AutoPoster PRO v8.1 — Полная версия!**")
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

