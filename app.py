#!/usr/bin/env python3
"""
🌐 VK AUTOPOSTER WEB PRO v4.1 — ИСПРАВЛЕННАЯ ВЕРСИЯ!
✅ DuplicateWidgetID ФИКС
✅ SQLite + многопользовательский
✅ Работает на телефоне!
"""

import streamlit as st
import sqlite3, requests, time, threading, base64, hashlib
from datetime import datetime, timedelta
import uuid

# 🔥 КЛЮЧИ
SECRET_KEY_XOR = b'KatePro2026KatePro2026KatePro2026KateP'

# Инициализация БД
@st.cache_resource
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, password TEXT, license_until TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS configs (
        id INTEGER PRIMARY KEY, email TEXT, tokens TEXT, groups TEXT,
        delay INTEGER DEFAULT 30, message TEXT, updated_at TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY, email TEXT, group_id TEXT, post_id INTEGER,
        status TEXT, created_at TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# Расшифровка токенов
def decrypt_tokens(tokens_str):
    if not tokens_str: return []
    parts = [t.strip() for t in tokens_str.split(',') if t.strip()]
    tokens = []
    for part in parts:
        try:
            encrypted_bytes = base64.b64decode(part.encode('utf-8'))
            decrypted_bytes = bytearray(b ^ SECRET_KEY_XOR[i % len(SECRET_KEY_XOR)] 
                                      for i, b in enumerate(encrypted_bytes))
            result = decrypted_bytes.decode('utf-8').strip()
            if 'vk1.a.' in result:
                tokens.append(result)
            elif 'vk1.a.' in part:
                tokens.append(part.strip())
        except:
            if 'vk1.a.' in part:
                tokens.append(part.strip())
    return tokens

# Главная страница
st.set_page_config(page_title="VK AutoPoster PRO", layout="wide")
st.title("🔐 VK AutoPoster WEB PRO v4.1")

# Состояние пользователя
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'config_saved' not in st.session_state:
    st.session_state.config_saved = False

# АВТОРИЗАЦИЯ
if not st.session_state.user_email:
    st.markdown("### 📱 Работает на всех устройствах!")
    
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### 🚀 ВХОД")
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔑 Пароль", type="password", key="login_password")
        
        if st.button("✅ ВОЙТИ", use_container_width=True, key="login_btn"):
            cursor = conn.cursor()
            cursor.execute("SELECT email, license_until FROM users WHERE email=? AND password=?",
                          (email, hashlib.sha256(password.encode()).hexdigest()))
            user = cursor.fetchone()
            if user:
                st.session_state.user_email = email
                st.session_state.license_until = user[1]
                st.success(f"✅ Добро пожаловать, {email}!")
                st.rerun()
            else:
                st.error("❌ Неверный email или пароль")
    
    with col2:
        st.markdown("### 👤 РЕГИСТРАЦИЯ")
        reg_email = st.text_input("📧 Email", key="reg_email")
        reg_password = st.text_input("🔑 Пароль", type="password", key="reg_password")
        
        if st.button("📝 ЗАРЕГИСТРИРОВАТЬСЯ", use_container_width=True, key="register_btn"):
            try:
                cursor = conn.cursor()
                pwd_hash = hashlib.sha256(reg_password.encode()).hexdigest()
                cursor.execute("INSERT INTO users (email, password, license_until) VALUES (?, ?, ?)",
                              (reg_email, pwd_hash, (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')))
                conn.commit()
                st.success("✅ Зарегистрирован! Лицензия 7 дней!")
                st.session_state.user_email = reg_email
                st.session_state.license_until = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                st.rerun()
            except:
                st.error("❌ Email уже существует")

# ОСНОВНОЙ ИНТЕРФЕЙС
else:
    st.success(f"👤 {st.session_state.user_email} | 📅 Лицензия до {st.session_state.license_until}")
    
    # Настройки
    cursor = conn.cursor()
    cursor.execute("SELECT tokens, groups, delay, message FROM configs WHERE email=?", 
                  (st.session_state.user_email,))
    config = cursor.fetchone()
    
    col1, col2 = st.columns(2)
    
    with col1:
        tokens_encrypted = st.text_area("🔐 Токены (Base64 или открытые)", 
                                       value=config[0] if config else "", 
                                       height=120, key="tokens_input")
        groups = st.text_input("📂 Группы (через запятую)", 
                              value=config[1] if config else "-231630927", key="groups_input")
    
    with col2:
        delay = st.slider("⏱️ Пауза (сек)", 5, 300, config[2] if config else 30, key="delay_slider")
        message = st.text_area("📝 Текст поста", value=config[3] if config else "Привет от WEB PRO v4.1!", 
                              height=120, key="message_input")
    
    # КНОПКИ
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("💾 СОХРАНИТЬ", use_container_width=True, key="save_config"):
            cursor.execute('''INSERT OR REPLACE INTO configs (email, tokens, groups, delay, message) 
                            VALUES (?, ?, ?, ?, ?)''',
                          (st.session_state.user_email, tokens_encrypted, groups, delay, message))
            conn.commit()
            st.success("✅ Настройки сохранены!")
            st.rerun()
    
    with col_btn2:
        if st.button("🔓 ПРОВЕРИТЬ ТОКЕНЫ", use_container_width=True, key="check_tokens"):
            tokens = decrypt_tokens(tokens_encrypted)
            st.info(f"✅ Найдено {len(tokens)} валидных токенов")
    
    with col_btn3:
        if st.button("📊 СТАТИСТИКА", use_container_width=True, key="stats_btn"):
            cursor.execute("SELECT COUNT(*) FROM posts WHERE email=?", (st.session_state.user_email,))
            total = cursor.fetchone()[0]
            st.metric("Всего постов", total)
    
    # УПРАВЛЕНИЕ ПОСТИНГОМ
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶️ НАЧАТЬ ПОСТИНГ", use_container_width=True, key="start_posting"):
            st.session_state.tokens = decrypt_tokens(tokens_encrypted)
            st.session_state.groups = [g.strip() for g in groups.split(',') if g.strip()]
            st.session_state.is_running = True
            st.session_state.post_count = 0
            st.rerun()
    
    with col_stop:
        if st.button("⏹️ ОСТАНОВИТЬ", use_container_width=True, key="stop_posting"):
            st.session_state.is_running = False
            st.rerun()
    
    # ПОСТИНГ ЛОГИКА
    if st.session_state.get('is_running', False) and st.session_state.get('tokens'):
        st.success("🚀 ПОСТИНГ АКТИВЕН!")
        
        def post_loop():
            tokens = st.session_state.tokens
            groups = st.session_state.groups
            delay_sec = delay
            
            while st.session_state.get('is_running', False):
                for token in tokens:
                    for group in groups:
                        if not st.session_state.get('is_running', False):
                            break
                        
                        try:
                            url = "https://api.vk.com/method/wall.post"
                            data = {
                                'owner_id': group,
                                'message': message[:8000],
                                'access_token': token,
                                'v': '5.131'
                            }
                            r = requests.post(url, data=data, timeout=30).json()
                            
                            if 'response' in r:
                                post_id = r['response']['post_id']
                                cursor.execute("INSERT INTO posts (email, group_id, post_id, status) VALUES (?, ?, ?, ?)",
                                             (st.session_state.user_email, group, post_id, 'success'))
                                st.session_state.post_count += 1
                                st.success(f"✅ Пост #{post_id} → {group}")
                            else:
                                st.error(f"❌ Ошибка VK API: {group}")
                        except Exception as e:
                            st.error(f"🌐 {str(e)[:50]}")
                        
                        time.sleep(delay_sec)
                conn.commit()
        
        if 'post_thread' not in st.session_state:
            st.session_state.post_thread = threading.Thread(target=post_loop, daemon=True)
            st.session_state.post_thread.start()
    
    # ЛОГИ
    st.subheader("📋 Последние посты")
    cursor.execute("SELECT * FROM posts WHERE email=? ORDER BY id DESC LIMIT 10", 
                  (st.session_state.user_email,))
    for post in cursor.fetchall():
        st.write(f"**{post[5]}** | {post[2]} → Пост #{post[3]} | {post[4]}")
