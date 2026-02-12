#!/usr/bin/env python3
"""
🌐 VK AUTOPOSTER WEB PRO v4.0 — БАЗА ДАННЫХ + ЛИЦЕНЗИЯ!
✅ SQLite создаётся САМ
✅ Токены Base64/XOR
✅ Многопользовательский
✅ Работает на телефоне!
"""

import streamlit as st
import sqlite3, requests, time, threading, base64, hashlib
from datetime import datetime, timedelta

# 🔥 ТВОИ КЛЮЧИ (изменить НИКОГДА!)
SECRET_KEY_XOR = b'KatePro2026KatePro2026KatePro2026KateP'

# Инициализация БД (СОЗДАЁТСЯ САМА!)
@st.cache_resource
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Таблицы создаются автоматически
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            license_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            tokens TEXT,
            groups TEXT,
            delay INTEGER DEFAULT 30,
            message TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users (email)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            group_id TEXT,
            post_id INTEGER,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users (email)
        )
    ''')
    
    conn.commit()
    return conn

# Подключение к БД
conn = init_db()

# Функции расшифровки (из твоего EXE)
def xor_decrypt_base64(encrypted_b64):
    try:
        encrypted_bytes = base64.b64decode(encrypted_b64.encode('utf-8'))
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            decrypted_bytes.append(byte ^ SECRET_KEY_XOR[i % len(SECRET_KEY_XOR)])
        result = decrypted_bytes.decode('utf-8').strip()
        return result if 'vk1.a.' in result else None
    except:
        return None

def decrypt_tokens(tokens_str):
    parts = [t.strip() for t in tokens_str.split(',') if t.strip()]
    tokens = []
    for part in parts:
        token = xor_decrypt_base64(part)
        if token:
            tokens.append(token)
        elif 'vk1.a.' in part:
            tokens.append(part.strip())
    return tokens

# Страница авторизации
def login_page():
    st.title("🔐 VK AutoPoster WEB PRO v4.0")
    st.markdown("### 📱 Работает на iOS, Android, Windows, Mac")
    
    col1, col2 = st.columns(2)
    
    with col1:
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Пароль", type="password")
        
        if st.button("🚀 ВОЙТИ", use_container_width=True):
            if email and password:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email=? AND password=?", 
                             (email, hashlib.sha256(password.encode()).hexdigest()))
                user = cursor.fetchone()
                
                if user:
                    st.session_state.user = {'email': email, 'license_until': user[2]}
                    st.session_state.save()
                    st.success("✅ Добро пожаловать!")
                    st.rerun()
                else:
                    st.error("❌ Неверный email/пароль")
            else:
                st.warning("⚠️ Заполни все поля")
    
    with col2:
        st.markdown("---")
        if st.button("👤 РЕГИСТРАЦИЯ", use_container_width=True):
            st.session_state.show_register = True
            st.rerun()

# Регистрация
if st.session_state.get('show_register', False):
    st.title("👤 РЕГИСТРАЦИЯ")
    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Пароль", type="password")
    
    if st.button("✅ ЗАРЕГИСТРИРОВАТЬСЯ", use_container_width=True):
        if email and password:
            try:
                cursor = conn.cursor()
                pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute("INSERT INTO users (email, password, license_until) VALUES (?, ?, ?)",
                             (email, pwd_hash, (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')))
                conn.commit()
                st.success("✅ Зарегистрирован! Лицензия на 7 дней!")
                st.session_state.user = {'email': email}
                st.session_state.save()
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("❌ Email уже существует")
        else:
            st.warning("⚠️ Заполни все поля")

# Главная страница (после входа)
if st.session_state.get('user'):
    st.title(f"🤖 VK AutoPoster PRO")
    st.info(f"👤 {st.session_state.user['email']} | 📅 Лицензия до {st.session_state.user['license_until']}")
    
    # Настройки
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configs WHERE email=?", (st.session_state.user['email'],))
    config = cursor.fetchone()
    
    tokens_encrypted = st.text_area("🔐 Токены (Base64/XOR или открытые)", 
                                  value=config[2] if config else "", height=100)
    groups = st.text_input("📂 Группы (через запятую)", value=config[3] if config else "-231630927")
    delay = st.slider("⏱️ Пауза между постами (сек)", 5, 300, config[4] if config else 30)
    message = st.text_area("📝 Текст поста", value=config[5] if config else "Привет от WEB PRO!", height=100)
    
    # Сохранение настроек
    if st.button("💾 СОХРАНИТЬ НАСТРОЙКИ", use_container_width=True):
        cursor.execute('''INSERT OR REPLACE INTO configs (email, tokens, groups, delay, message) 
                         VALUES (?, ?, ?, ?, ?)''',
                      (st.session_state.user['email'], tokens_encrypted, groups, delay, message))
        conn.commit()
        st.success("✅ Настройки сохранены!")
    
    # Статистика
    col1, col2, col3 = st.columns(3)
    with col1:
        cursor.execute("SELECT COUNT(*) FROM posts WHERE email=?", (st.session_state.user['email'],))
        total_posts = cursor.fetchone()[0]
        st.metric("📊 Всего постов", total_posts)
    
    # Кнопки управления
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ НАЧАТЬ ПОСТИНГ", use_container_width=True):
            st.session_state.tokens = decrypt_tokens(tokens_encrypted)
            st.session_state.groups = [g.strip() for g in groups.split(',') if g.strip()]
            st.session_state.is_running = True
            st.session_state.post_count = total_posts
            st.rerun()
    
    with col_btn2:
        if st.button("⏹️ ОСТАНОВИТЬ", use_container_width=True):
            st.session_state.is_running = False
            st.rerun()
    
    # Постинг
    if st.session_state.get('is_running', False):
        if st.session_state.get('tokens') and st.session_state.get('groups'):
            st.success("🚀 Постинг запущен!")
            
            def post_loop():
                while st.session_state.get('is_running', False):
                    for token in st.session_state.tokens:
                        for group in st.session_state.groups:
                            if not st.session_state.get('is_running', False):
                                break
                                
                            # Отправка поста
                            url = "https://api.vk.com/method/wall.post"
                            data = {
                                'owner_id': group,
                                'message': message[:8000],
                                'access_token': token,
                                'v': '5.131'
                            }
                            
                            try:
                                r = requests.post(url, data=data, timeout=30).json()
                                if 'response' in r:
                                    post_id = r['response']['post_id']
                                    cursor.execute("INSERT INTO posts (email, group_id, post_id, status) VALUES (?, ?, ?, ?)",
                                                 (st.session_state.user['email'], group, post_id, 'success'))
                                    st.session_state.post_count += 1
                                    st.success(f"✅ Пост #{post_id} в {group}")
                                else:
                                    error = r.get('error', {})
                                    st.error(f"❌ [{error.get('error_code',0)}] {group}")
                            except Exception as e:
                                st.error(f"🌐 Ошибка: {str(e)[:50]}")
                            
                            time.sleep(delay)
                    conn.commit()
                st.rerun()
            
            threading.Thread(target=post_loop, daemon=True).start()
        else:
            st.error("⚠️ Добавь токены и группы!")
    
    # Логи постов
    st.subheader("📋 Последние посты")
    cursor.execute("SELECT * FROM posts WHERE email=? ORDER BY created_at DESC LIMIT 20", 
                  (st.session_state.user['email'],))
    posts = cursor.fetchall()
    
    if posts:
        for post in posts:
            st.write(f"**{post[5]}** | {post[2]} → {post[3]} | {post[4]}")
    else:
        st.info("📭 Пока нет постов")

# Главная логика
if 'user' not in st.session_state:
    st.session_state.user = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

if not st.session_state.user:
    login_page()
