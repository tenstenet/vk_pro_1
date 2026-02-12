#!/usr/bin/env python3
"""
🌐 VK AUTOPOSTER WEB PRO v4.2 — 100% DuplicateWidgetID ФИКС!
✅ Уникальные ключи для ВСЕХ виджетов
✅ Регистрация + база данных
✅ Токены Base64/XOR
"""

import streamlit as st
import sqlite3, requests, time, threading, base64, hashlib
from datetime import datetime, timedelta

# 🔥 КЛЮЧИ
SECRET_KEY_XOR = b'KatePro2026KatePro2026KatePro2026KateP'

# Инициализация БД (один раз)
@st.cache_resource
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, password TEXT, license_until TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS configs (
        email TEXT PRIMARY KEY, tokens TEXT, groups TEXT, delay INTEGER, message TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# Расшифровка
def decrypt_tokens(tokens_str):
    if not tokens_str: return []
    parts = [t.strip() for t in tokens_str.split(',') if t.strip()]
    tokens = []
    for part in parts:
        try:
            encrypted_bytes = base64.b64decode(part.encode())
            decrypted = bytes(b ^ SECRET_KEY_XOR[i % len(SECRET_KEY_XOR)] 
                            for i, b in enumerate(encrypted_bytes))
            result = decrypted.decode().strip()
            if 'vk1.a.' in result: tokens.append(result)
        except: pass
        if 'vk1.a.' in part: tokens.append(part.strip())
    return tokens

st.set_page_config(page_title="VK AutoPoster", layout="wide")

# Главная логика БЕЗ функций (чтобы избежать DuplicateWidgetID)
st.title("🔐 VK AutoPoster WEB PRO v4.2")

# Инициализация сессии
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'page' not in st.session_state: st.session_state.page = 'login'

# === ЛОГИН ===
if st.session_state.page == 'login':
    st.markdown("### 📱 Работает на iOS/Android/Windows/Mac")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 ВХОД")
        login_email = st.text_input("📧 Email", key="login_email_unique")
        login_pass = st.text_input("🔑 Пароль", type="password", key="login_pass_unique")
        
        if st.button("✅ ВОЙТИ", key="login_btn_unique"):
            cursor = conn.cursor()
            cursor.execute("SELECT email, license_until FROM users WHERE email=? AND password=?",
                          (login_email, hashlib.sha256(login_pass.encode()).hexdigest()))
            user = cursor.fetchone()
            if user:
                st.session_state.user_email = login_email
                st.session_state.license_until = user[1]
                st.session_state.page = 'main'
                st.success("✅ Вход выполнен!")
                st.rerun()
            else:
                st.error("❌ Неверные данные")
    
    with col2:
        st.markdown("### 👤 РЕГИСТРАЦИЯ")
        reg_email = st.text_input("📧 Email", key="reg_email_unique")
        reg_pass = st.text_input("🔑 Пароль", type="password", key="reg_pass_unique")
        
        if st.button("📝 РЕГИСТРАЦИЯ", key="reg_btn_unique"):
            try:
                pwd_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (email, password, license_until) VALUES (?, ?, ?)",
                              (reg_email, pwd_hash, (datetime.now()+timedelta(days=7)).strftime('%Y-%m-%d')))
                conn.commit()
                st.session_state.user_email = reg_email
                st.session_state.license_until = (datetime.now()+timedelta(days=7)).strftime('%Y-%m-%d')
                st.session_state.page = 'main'
                st.success("✅ Регистрация успешна! Лицензия 7 дней!")
                st.rerun()
            except:
                st.error("❌ Email уже существует")

# === ГЛАВНАЯ СТРАНИЦА ===
elif st.session_state.page == 'main':
    st.success(f"👤 {st.session_state.user_email} | 📅 Лицензия: {st.session_state.license_until}")
    
    # Загрузка настроек
    cursor = conn.cursor()
    cursor.execute("SELECT tokens, groups, delay, message FROM configs WHERE email=?", 
                  (st.session_state.user_email,))
    config = cursor.fetchone()
    
    col1, col2 = st.columns(2)
    with col1:
        tokens_input = st.text_area("🔐 Токены (Base64/XOR)", 
                                   value=config[0] if config else "", height=100, key="tokens_main")
        groups_input = st.text_input("📂 Группы", value=config[1] if config else "-231630927", 
                                   key="groups_main")
    
    with col2:
        delay_input = st.slider("⏱️ Пауза (сек)", 5, 300, config[2] if config else 30, key="delay_main")
        message_input = st.text_area("📝 Текст поста", value=config[3] if config else "Тест WEB PRO!", 
                                    height=100, key="message_main")
    
    # Кнопки сохранения и проверки
    col_save, col_check = st.columns(2)
    with col_save:
        if st.button("💾 СОХРАНИТЬ", key="save_main"):
            cursor.execute("INSERT OR REPLACE INTO configs VALUES (?, ?, ?, ?, ?)",
                          (st.session_state.user_email, tokens_input, groups_input, delay_input, message_input))
            conn.commit()
            st.success("✅ Сохранено!")
    
    with col_check:
        if st.button("🔓 ПРОВЕРИТЬ ТОКЕНЫ", key="check_main"):
            tokens = decrypt_tokens(tokens_input)
            st.info(f"✅ Токенов найдено: **{len(tokens)}**")
    
    # Управление постингом
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶️ НАЧАТЬ", key="start_main") and tokens_input.strip():
            st.session_state.tokens = decrypt_tokens(tokens_input)
            st.session_state.groups = [g.strip() for g in groups_input.split(',')]
            st.session_state.is_running = True
            st.session_state.post_count = 0
            st.success("🚀 Постинг запущен!")
    
    with col_stop:
        if st.button("⏹️ ОСТАНОВИТЬ", key="stop_main"):
            st.session_state.is_running = False
            st.success("🛑 Остановлено!")
    
    # Постинг
    if st.session_state.get('is_running', False) and st.session_state.get('tokens'):
        st.balloons()
        st.info("**🚀 АКТИВНЫЙ ПОСТИНГ**")
        
        # Простая логика постинга (без потоков для простоты)
        if st.button("📤 ОТПРАВИТЬ ТЕСТОВЫЙ ПОСТ", key="test_post"):
            token = st.session_state.tokens[0]
            group = st.session_state.groups[0]
            try:
                r = requests.post("https://api.vk.com/method/wall.post", data={
                    'owner_id': group, 'message': message_input[:4000],
                    'access_token': token, 'v': '5.131'
                }).json()
                if 'response' in r:
                    st.success(f"✅ Пост #{r['response']['post_id']} отправлен!")
                else:
                    st.error(f"❌ {r.get('error', {}).get('error_msg', 'Ошибка')}")
            except Exception as e:
                st.error(f"🌐 {str(e)[:100]}")
    
    # История постов
    st.markdown("### 📊 История")
    cursor.execute("SELECT * FROM posts WHERE email=? ORDER BY id DESC LIMIT 10", (st.session_state.user_email,))
    posts = cursor.fetchall()
    if posts:
        for post in posts:
            st.write(f"*{post[5]}* | {post[2]} → #{post[3]}")
    else:
        st.info("📭 Постов пока нет")
