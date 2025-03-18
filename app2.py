import os
import streamlit as st
import requests
import sqlite3
import time

# Получаем API-ключ из Streamlit Secrets
gigachat_api_key = st.secrets["GIGACHAT_API_KEY"]

# URL API GigaChat
GIGACHAT_API_URL = "https://gigachat.sbercloud.ru/api/v1/chat/completions"

# Настройка приложения
st.set_page_config(page_title="Чат с GigaChat", layout="wide")
st.title("🤖 Чат с GigaChat")

# Подключение к базе данных SQLite
conn = sqlite3.connect("chat_logs.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы логов, если её нет
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        event_type TEXT,
        details TEXT
    )
""")
conn.commit()

# Функция логирования событий
def log_event(event_type, details=""):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO events (timestamp, event_type, details) VALUES (?, ?, ?)", (timestamp, event_type, details))
    conn.commit()

# Храним состояние сессии
if "messages" not in st.session_state:
    st.session_state.messages = []
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False
if "gpt_role" not in st.session_state:
    st.session_state.gpt_role = "Обычный ассистент"

# Выбор роли GigaChat в боковой панели
st.sidebar.subheader("Настройки GigaChat")
role_options = {
    "Обычный ассистент": "Ты – полезный AI, который отвечает на вопросы.",
    "Учитель": "Ты – терпеливый учитель, объясняющий сложные темы простыми словами.",
    "Шутник": "Ты – веселый комик, отвечающий с юмором.",
    "Психолог": "Ты – эмпатичный психолог, поддерживающий пользователя.",
    "Строгий наставник": "Ты – строгий коуч, который мотивирует к действию."
}
selected_role = st.sidebar.selectbox("Выбери роль GigaChat", list(role_options.keys()))

# Если роль изменилась, обновляем систему сообщений
if selected_role != st.session_state.gpt_role:
    st.session_state.gpt_role = selected_role
    st.session_state.messages = [{"role": "system", "content": role_options[selected_role]}]
    log_event("ROLE_CHANGED", f"Роль изменена на: {selected_role}")

st.sidebar.write(f"🔹 Текущая роль: **{selected_role}**")

# Функция отправки запроса к GigaChat API
def get_gigachat_response(messages):
    headers = {
        "Authorization": f"Bearer {gigachat_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "GigaChat",  # Можно заменить на конкретную версию модели
        "messages": messages
    }

    response = requests.post(GIGACHAT_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка: {response.json()}"

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Обычный чат
prompt = st.chat_input("Напишите сообщение...")
if prompt:
    if not st.session_state.chat_started:
        log_event("CHAT_STARTED", "Начало нового чата")
        st.session_state.chat_started = True

    st.session_state.message_count += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    log_event("MESSAGE_SENT", f"Пользователь отправил сообщение: {prompt}")

    with st.chat_message("user"):
        st.markdown(prompt)

    # Отправляем запрос в GigaChat API
    reply = get_gigachat_response(st.session_state.messages)
    
    st.session_state.messages.append({"role": "assistant", "content": reply})
    log_event("BOT_REPLY", f"GigaChat ответил: {reply}")

    with st.chat_message("assistant"):
        st.markdown(reply)
