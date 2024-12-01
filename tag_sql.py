import sqlite3
import pandas as pd
import time

def change_user_tags(conn, user_id, tags):
    cursor = conn.cursor()

    # Проверяем, есть ли пользователь в таблице
    cursor.execute("SELECT COUNT(*) FROM user_tags WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0] == 0:
        # Добавляем нового пользователя
        cursor.execute("INSERT INTO user_tags (user_id, tags) VALUES (?, ?)", (user_id, tags))
    else:
        # Обновляем теги для существующего пользователя
        cursor.execute("UPDATE user_tags SET tags = ? WHERE user_id = ?", (tags, user_id))
    conn.commit()


def get_user_timetable(conn, user_id):
    cursor = conn.cursor()

    # Получаем события пользователя
    query = """
        SELECT * FROM event_tags AS et JOIN user_event AS ue ON et.event_id = ue.event_id WHERE ue.user_id = ?;
    """
    cursor.execute(query, (user_id,))
    user_timetable = cursor.fetchall()
    user_timetable = [us_tt for us_tt in user_timetable]
    return user_timetable


def get_user_tags(conn, user_id):
    cursor = conn.cursor()

    # Получаем события пользователя
    query = """
        SELECT tags FROM user_tags WHERE user_id = ?;
    """
    cursor.execute(query, (user_id,))
    user_tags = cursor.fetchone()[0]
    return user_tags


def insert_into_timetable(conn, user_id, event_id):
    cursor = conn.cursor()

    # Получаем теги события
    cursor.execute("SELECT tags FROM event_tags WHERE event_id = ?", (event_id,))
    event_tags = cursor.fetchone()
    if event_tags is None:
        raise ValueError(f"Event ID {event_id} not found in event_tags table.")

    # Вставляем данные в таблицу user_event
    cursor.execute(
        "INSERT INTO user_event (user_id, event_id, tags) VALUES (?, ?, ?)",
        (user_id, event_id, event_tags[0]),
    )

    conn.commit()


def rate_event(conn, user_id, event_id, rate):
    cursor = conn.cursor()

    # Обновляем рейтинг события
    cursor.execute(
        "UPDATE user_event SET rate = ? WHERE user_id = ? AND event_id = ?",
        (rate, user_id, event_id),
    )

    conn.commit()

start= time.time()
db_path = 'hahahon.db'
conn = sqlite3.connect(db_path)
conn.close
end = time.time()
print(end-start)