import streamlit as st
import sqlite3, requests, base64, hashlib, time
from datetime import datetime, timedelta
import io

st.set_page_config(layout="wide")
st.title("🚀 VK AutoPoster PRO v6.0")

# База данных
@st.cache_resource
def init_db():
    conn = sqlite3.connect('vkbot.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, password TEXT, license_date TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
        email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, message TEXT, photo_url TEXT)''')
    return conn

db = init_db()
SECRET_KEY = b'KatePro2026KatePro2026KatePro2026KateP'

def decrypt_token(token_b64):
    try:
        decoded = base64.b64decode(token_b64.encode())
        return bytes(b ^ SECRET_KEY[i % len(SECRET_KEY)] for i, b in enumerate(decoded)).decode()
    except:
        return token_b64

def upload_photo_vk(token, group_id, photo_file):
    """Загрузка фото в VK"""
    try:
        # 1. Получить сервер для загрузки
        url = 'https://api.vk.com/method/photos.getWallUploadServer'
        data = {'group_id': abs(int(group_id)), 'access_token': token, 'v': '5.131'}
        resp = requests.post(url, data=data).json()
        upload_url = resp['response']['upload_url']
        
        # 2. Загрузить фото
        files = {'photo': photo_file}
        resp = requests.post(upload_url, files=files).json()
        
        # 3. Сохранить фото
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

# === ИНТЕРФЕЙС ===
col1, col2 = st.columns([1,2])

with col1:
    st.subheader("🔐 АВТОРИЗАЦИЯ")
    
    email = st.text_input("📧 Email", key="login_email")
    passwd = st.text_input("🔑 Пароль", type="password", key="login_pass")
    
    if st.button("✅ ВОЙТИ", key="login"):
        cur = db.cursor()
        cur.execute("SELECT license_date FROM users WHERE email=? AND password=?", 
                   (email, hashlib.sha256(passwd.encode()).hexdigest()))
        user = cur.fetchone()
        if user:
            st.session_state.user = email
            st.session_state.license = user[0]
            st.success(f"✅ {email}")
            st.rerun()
        else:
            st.error("❌ Неверно")
    
    # Регистрация
    new_email = st.text_input("📧 Регистрация", key="reg_email")
    new_pass = st.text_input("🔑 Пароль", type="password", key="reg_pass")
    
    if st.button("➕ СОЗДАТЬ", key="register"):
        try:
            cur = db.cursor()
            license_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            cur.execute("INSERT INTO users VALUES (?, ?, ?)", 
                       (new_email, hashlib.sha256(new_pass.encode()).hexdigest(), license_date))
            db.commit()
            st.success("✅ Создан! Лицензия 7 дней")
            st.session_state.user = new_email
            st.session_state.license = license_date
            st.rerun()
        except:
            st.error("❌ Занят")

with col2:
    if 'user' in st.session_state:
        st.success(f"👤 **{st.session_state.user}** | 📅 До: **{st.session_state.license}**")
        
        st.subheader("⚙️ НАСТРОЙКИ")
        
        # Загрузка настроек
        cur = db.cursor()
        cur.execute("SELECT tokens, groups, message, photo_url FROM settings WHERE email=?", 
                   (st.session_state.user,))
        config = cur.fetchone()
        
        tokens = st.text_area("🔐 ТОКЕНЫ", value=config[0] if config else "", height=60, key="tokens")
        groups = st.text_input("📂 ГРУППЫ (через ,)", value=config[1] if config else "-231630927", key="groups")
        message = st.text_area("📝 ТЕКСТ", value=config[2] if config else "Пост из веб-бота!", height=60, key="msg")
        
        uploaded_file = st.file_uploader("🖼️ ФОТО", type=['jpg','png'], key="photo")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 СОХРАНИТЬ", key="save"):
                photo_url = config[3] if config else ""
                cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?, ?)",
                           (st.session_state.user, tokens, groups, message, photo_url))
                db.commit()
                st.success("✅ Сохранено!")
        
        with col2:
            if st.button("🔍 ТЕСТ ТОКЕНОВ", key="test_tokens"):
                real_token = decrypt_token(tokens.strip())
                st.info(f"**Токен:** {'✅ OK' if 'vk1.a.' in real_token else '❌ Нет'}")
        
        with col3:
            if st.button("📤 ТЕСТ ПОСТ", key="test_post"):
                real_token = decrypt_token(tokens.strip())
                if 'vk1.a.' in real_token and groups.strip():
                    group = groups.split(',')[0].strip()
                    
                    # Фото
                    attachments = ""
                    if uploaded_file:
                        photo_attach = upload_photo_vk(real_token, group, uploaded_file)
                        if photo_attach:
                            attachments = photo_attach
                    
                    # Пост
                    url = "https://api.vk.com/method/wall.post"
                    data = {
                        'owner_id': group,
                        'from_group': 1,
                        'message': message,
                        'attachments': attachments,
                        'access_token': real_token,
                        'v': '5.131'
                    }
                    
                    resp = requests.post(url, data=data).json()
                    if 'response' in resp:
                        st.success(f"✅ Пост #{resp['response']['post_id']} → {group}")
                    else:
                        st.error(f"❌ {resp}")
                else:
                    st.error("❌ Токены/группы!")

st.caption("🎉 Лицензию продлеваешь ТЫ: UPDATE users SET license_date='2026-12-31' WHERE email='client@'")
