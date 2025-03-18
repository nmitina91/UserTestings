import streamlit as st
import openai
import sqlite3
import time

# Укажи свой API-ключ OpenAI
openai.api_key = "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"

# Задаем пароль для авторизации
AUTH_PASSWORD = "secret123"

st.set_page_config(page_title="Чат с AI", layout="wide")
st.title("🤖 Чат с AI")

# Подключение к базе данных
conn = sqlite3.connect("chat_logs.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если их нет
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        event_type TEXT,
        details TEXT
    )
""")
conn.commit()

# Функция логирования событий в базу
def log_event(event_type, details=""):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO events (timestamp, event_type, details) VALUES (?, ?, ?)", (timestamp, event_type, details))
    conn.commit()

# Инициализация сессии
if "messages" not in st.session_state:
    st.session_state.messages = []
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "auth_time" not in st.session_state:
    st.session_state.auth_time = None
if "restricted_mode" not in st.session_state:
    st.session_state.restricted_mode = False
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False  # Флаг первого сообщения

# Функция авторизации
def authenticate(password):
    if password == AUTH_PASSWORD:
        st.session_state.is_authenticated = True
        st.session_state.auth_time = time.time()
        st.session_state.restricted_mode = False
        st.session_state.message_count = 0
        st.success("✅ Успешная авторизация! Теперь можно писать свободно.")
        log_event("AUTH_SUCCESS", "Успешный вход в чат")
    else:
        st.error("❌ Неверный пароль!")
        log_event("AUTH_FAIL", "Ошибка входа в чат")

# Проверка времени после авторизации
if st.session_state.is_authenticated:
    elapsed_time = time.time() - st.session_state.auth_time
    if elapsed_time > 180:
        st.session_state.restricted_mode = True
        st.warning("⚠️ Время свободного общения истекло. Теперь можно отправлять только предустановленные сообщения.")
        log_event("RESTRICTED_MODE", "Включен режим предустановленных сообщений")

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ограничение сообщений + Авторизация
if st.session_state.message_count >= 20 and not st.session_state.is_authenticated:
    st.warning("🔒 Достигнут лимит сообщений. Авторизуйтесь, чтобы продолжить.")
    password = st.text_input("Введите пароль для доступа:", type="password")
    if st.button("Войти"):
        authenticate(password)
        log_event("AUTH_ATTEMPT", "Попытка авторизации")

# Ограниченный режим сообщений
elif st.session_state.restricted_mode:
    st.warning("⏳ Вы можете отправлять только предустановленные сообщения.")
    predefined_messages = ["Привет!", "Как дела?", "Расскажи что-нибудь интересное!", "Спасибо!", "До свидания!"]
    selected_message = st.selectbox("Выберите сообщение для отправки:", predefined_messages)
    if st.button("Отправить"):
        st.session_state.messages.append({"role": "user", "content": selected_message})
        log_event("MESSAGE_SENT", f"Пользователь отправил сообщение: {selected_message}")

        with st.chat_message("user"):
            st.markdown(selected_message)

        client = openai.OpenAI()  # Создаем клиента OpenAI
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages
        )

        reply = response["choices"][0]["message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": reply})
        log_event("BOT_REPLY", f"Бот ответил: {reply}")

        with st.chat_message("assistant"):
            st.markdown(reply)

# Обычный чат
else:
    prompt = st.chat_input("Напишите сообщение...")
    if prompt:
        if not st.session_state.chat_started:
            log_event("CHAT_STARTED", "Начало нового чата")
            st.session_state.chat_started = True  # Устанавливаем флаг

        st.session_state.message_count += 1
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_event("MESSAGE_SENT", f"Пользователь отправил сообщение: {prompt}")

        with st.chat_message("user"):
            st.markdown(prompt)

        client = openai.OpenAI()  # Создаем клиента OpenAI
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages
        )
        
        reply = response["choices"][0]["message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": reply})
        log_event("BOT_REPLY", f"Бот ответил: {reply}")

        with st.chat_message("assistant"):
            st.markdown(reply)
