import streamlit as st
import sqlite3, requests, base64, hashlib, time
from datetime import datetime, timedelta
import io

st.set_page_config(layout="wide", page_title="VK AutoPoster PRO")
st.title("🤖 VK AutoPoster WEB PRO v7.0")

# 🔥 ТВОЙ СЕКРЕТНЫЙ КЛЮЧ (НЕ МЕНЯЙ!)
SECRET_KEY = b'KatePro2026KatePro2026KatePro2026KateP'

# База данных (создаётся САМА!)
@st.cache_resource
def init_db():
    conn = sqlite3.connect('vkbot.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, password TEXT, license_date TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
        email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, message TEXT, photo_url TEXT)''')
    conn.commit()
    return conn

db = init_db()

def decrypt_token(token_b64):
    """XOR расшифровка твоих токенов"""
    try:
        decoded = base64.b64decode(token_b64.encode())
        return bytes(b ^ SECRET_KEY[i % len(SECRET_KEY)] for i, b in enumerate(decoded)).decode()
    except:
        return token_b64

def upload_photo_vk(token, group_id, photo_file):
    """Загрузка фото в VK"""
    try:
        # Получить сервер загрузки
        url = 'https://api.vk.com/method/photos.getWallUploadServer'
        data = {'group_id': abs(int(group_id)), 'access_token': token, 'v': '5.131'}
        resp = requests.post(url, data=data).json()
        upload_url = resp['response']['upload_url']
        
        # Загрузить фото
        files = {'photo': photo_file}
        resp = requests.post(upload_url, files=files).json()
        
        # Сохранить фото
        save_url = 'https://api.vk.com/method/photos.saveWallPhoto'
        data = {
            'group_id': abs(int(group_id)),
            'photo': resp['photo'], 
            'server': resp['server'],
            'hash': resp['hash'],
            'access_token': token,
            'v': '5.131'
        }
        resp = requests.post(save_url, data=data).json()
        photo_id = resp['response'][0]['id']
        owner_id = resp['response'][0]['owner_id']
        return f"photo{owner_id}_{photo_id}"
    except:
        return None

# 🔥 АДМИНКА (твой пароль: kate2026)
if st.sidebar.button("🔧 АДМИН ПАНЕЛЬ"):
    st.session_state.show_admin = True

if st.session_state.get('show_admin', False):
    st.header("🔧 АДМИНКА")
    admin_pass = st.text_input("🔑 Пароль админа", type="password")
    
    if admin_pass == "kate2026":
        st.success("✅ Админ-доступ!")
        
        # Продление лицензии
        client_email = st.text_input("📧 Email клиента")
        license_days = st.slider("📅 Дней лицензии", 7, 365, 30)
        
        if st.button("✅ ПРОДЛИТЬ ЛИЦЕНЗИЮ"):
            cur = db.cursor()
            new_date = (datetime.now() + timedelta(days=license_days)).strftime('%Y-%m-%d')
            cur.execute("UPDATE users SET license_date=? WHERE email=?", (new_date, client_email))
            db.commit()
            st.success(f"✅ {client_email} продлён до {new_date}")
        
        # Все пользователи
        st.subheader("👥 Все клиенты")
        cur = db.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        st.dataframe(users, use_container_width=True)
    else:
        st.warning("❌ Неверный пароль")

# === ОСНОВНОЙ ИНТЕРФЕЙС ===
tab1, tab2 = st.tabs(["👤 Авторизация", "⚙️ Постинг"])

with tab1:
    st.subheader("🔐 Вход / Регистрация")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 ВОЙТИ")
        login_email = st.text_input("📧 Email", key="login_email")
        login_pass = st.text_input("🔑 Пароль", type="password", key="login_pass")
        
        if st.button("✅ ВОЙТИ", key="login_btn"):
            cur = db.cursor()
            cur.execute("SELECT license_date FROM users WHERE email=? AND password=?", 
                       (login_email, hashlib.sha256(login_pass.encode()).hexdigest()))
            user = cur.fetchone()
            if user:
                st.session_state.user = login_email
                st.session_state.license = user[0]
                st.success(f"✅ Добро пожаловать, {login_email}!")
                st.rerun()
            else:
                st.error("❌ Неверный email/пароль")
    
    with col2:
        st.markdown("### ➕ РЕГИСТРАЦИЯ")
        reg_email = st.text_input("📧 Email", key="reg_email")
        reg_pass = st.text_input("🔑 Пароль", type="password", key="reg_pass")
        
        if st.button("📝 ЗАРЕГИСТРИРОВАТЬСЯ", key="reg_btn"):
            try:
                cur = db.cursor()
                license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                pwd_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
                cur.execute("INSERT INTO users VALUES (?, ?, ?)", 
                           (reg_email, pwd_hash, license_date))
                db.commit()
                st.success(f"✅ Зарегистрирован! Лицензия до {license_date}")
                st.session_state.user = reg_email
                st.session_state.license = license_date
                st.rerun()
            except:
                st.error("❌ Email уже существует")

with tab2:
    if 'user' in st.session_state:
        st.success(f"👤 **{st.session_state.user}** | 📅 Лицензия до **{st.session_state.license}**")
        
        st.subheader("⚙️ НАСТРОЙКИ ПОСТИНГА")
        
        # Загрузка настроек
        cur = db.cursor()
        cur.execute("SELECT tokens, groups, message FROM settings WHERE email=?", 
                   (st.session_state.user,))
        config = cur.fetchone()
        
        col1, col2 = st.columns(2)
        
        with col1:
            tokens = st.text_area("🔐 ТОКЕНЫ (Base64/XOR или обычные)", 
                                 value=config[0] if config else "", 
                                 height=100, key="tokens_input")
            groups = st.text_input("📂 ГРУППЫ (через запятую)", 
                                  value=config[1] if config else "-231630927", 
                                  key="groups_input")
        
        with col2:
            message = st.text_area("📝 ТЕКСТ ПОСТА", 
                                  value=config[2] if config else "🚀 Пост из VK AutoPoster PRO v7.0!", 
                                  height=100, key="message_input")
            uploaded_file = st.file_uploader("🖼️ Добавить фото", 
                                           type=['jpg', 'jpeg', 'png'], 
                                           key="photo_uploader")
        
        # Кнопки управления
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 СОХРАНИТЬ НАСТРОЙКИ", key="save_settings"):
                cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?, ?)",
                           (st.session_state.user, tokens, groups, message, ""))
                db.commit()
                st.success("✅ Настройки сохранены!")
        
        with col2:
            if st.button("🔍 ПРОВЕРИТЬ ТОКЕНЫ", key="check_tokens"):
                real_token = decrypt_token(tokens.strip())
                if 'vk1.a.' in real_token:
                    st.success("✅ Токен валиден!")
                else:
                    st.error("❌ Проверь токен!")
        
        with col3:
            if st.button("📤 ТЕСТОВЫЙ ПОСТ", key="test_post"):
                real_token = decrypt_token(tokens.strip())
                if 'vk1.a.' in real_token and groups.strip():
                    group = groups.split(',')[0].strip()
                    
                    # Фото
                    attachments = ""
                    if uploaded_file:
                        photo_attach = upload_photo_vk(real_token, group, uploaded_file)
                        if photo_attach:
                            attachments = photo_attach
                            st.success("✅ Фото загружено!")
                    
                    # Отправка поста
                    url = "https://api.vk.com/method/wall.post"
                    data = {
                        'owner_id': group,
                        'from_group': 1,
                        'message': message[:8000],
                        'attachments': attachments,
                        'access_token': real_token,
                        'v': '5.131'
                    }
                    
                    try:
                        resp = requests.post(url, data=data, timeout=30).json()
                        if 'response' in resp:
                            post_id = resp['response']['post_id']
                            st.success(f"🎉 ПОСТ #{post_id} ОТПРАВЛЕН в {group}!")
                        else:
                            st.error(f"❌ Ошибка VK: {resp.get('error', {}).get('error_msg', 'Неизвестно')}")
                    except Exception as e:
                        st.error(f"🌐 {str(e)[:100]}")
                else:
                    st.error("❌ Добавь токены и группу!")
        
        # Статистика
        st.subheader("📊 СТАТИСТИКА")
        col1, col2 = st.columns(2)
        with col1:
            cur.execute("SELECT COUNT(*) FROM settings WHERE email=?", (st.session_state.user,))
            st.metric("💾 Настроек", cur.fetchone()[0])
        with col2:
            cur.execute("SELECT COUNT(*) FROM users WHERE license_date > date('now')")
            st.metric("👥 Активных", cur.fetchone()[0])
    else:
        st.warning("🔐 Сначала войди или зарегистрируйся!")

st.markdown("---")
st.caption("🎉 VK AutoPoster PRO v7.0 — Полная версия с админкой!")
