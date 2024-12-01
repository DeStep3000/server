from flask import Flask, request, jsonify
from flask_cors import CORS  # Импортируем CORS
from rec_sys_sql import rec_sys  # Импортируйте функцию rec_sys
import sqlite3
import tag_sql

app = Flask(__name__)
CORS(app)  # Применяем CORS ко всем маршрутам

# Путь к базе данных
DB_PATH = 'hahahon.db'


# === API для сохранения тегов пользователя ===
@app.route('/save-tags', methods=['POST'])
def save_tags():
    data = request.json  # Получение данных из POST-запроса
    user_id = data.get('user_id')
    selected_tags = data.get('tags', [])
    print('selected_tags', selected_tags)

    if not user_id or not selected_tags:
        return jsonify({"status": "error", "message": "user_id или tags отсутствуют"}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            selected_tags = ', '.join(selected_tags)
            cursor = conn.cursor()
            # Проверяем, есть ли пользователь в таблице
            cursor.execute("SELECT COUNT(*) FROM user_tags WHERE user_id = ?", (user_id,))
            if cursor.fetchone()[0] == 0:
                # Добавляем нового пользователя
                cursor.execute("INSERT INTO user_tags (user_id, tags) VALUES (?, ?)", (user_id, selected_tags))
            else:
                # Обновляем теги для существующего пользователя
                cursor.execute("UPDATE user_tags SET tags = ? WHERE user_id = ?", (selected_tags, user_id))
            conn.commit()
        return jsonify({"status": "success", "message": "Tags saved successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# === API для получения рекомендаций ===
@app.route('/recommend', methods=['GET'])
def recommendations_api():
    try:
        user_id = int(request.args.get('user_id'))
        print(f"Получен запрос для user_id: {user_id}")
        recommendations = rec_sys(DB_PATH, user_id)
        print("Рекомендации:", recommendations)
        return jsonify({'status': 'success', 'recommendations': recommendations})
    except Exception as e:
        print("Ошибка API:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500


# === API для обновления расписания пользователя ===
@app.route('/update_timetable', methods=['POST'])
def update_timetable():
    data = request.json
    print(data)
    user_id = data.get('user_id')
    event_id = data.get('event_id')
    tags = data.get('tags', [])
    action = data.get('action')  # "add" или "remove"

    if not user_id or not event_id or not action:
        return jsonify({"status": "error", "message": "user_id, event_id или action отсутствуют"}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if action == "add":
                cursor.execute(
                    "INSERT INTO user_event (user_id, event_id, tags) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                    (user_id, event_id, tags))
            elif action == "remove":
                cursor.execute("DELETE FROM user_event WHERE user_id = ? AND event_id = ?",
                               (user_id, event_id))
            else:
                return jsonify({"status": "error", "message": "Некорректное значение action"}), 400

            conn.commit()
        return jsonify({"status": "success", "message": f"Event {action}ed successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def get_user_timetable(conn, user_id):
    cursor = conn.cursor()

    # Выполняем SQL-запрос для получения данных
    query = """
        SELECT * FROM event_tags AS et
        JOIN user_event AS ue ON et.event_id = ue.event_id
        WHERE ue.user_id = ?;
    """
    cursor.execute(query, (user_id,))

    # Извлекаем названия столбцов
    column_names = [description[0] for description in cursor.description]

    # Преобразуем результат запроса в список словарей
    user_timetable = [
        dict(zip(column_names, row)) for row in cursor.fetchall()
    ]
    return user_timetable


@app.route('/get_user_timetable', methods=['GET'])
def get_user_timetable_route():
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        timetable = get_user_timetable(conn, user_id)
        conn.close()
        return jsonify({"timetable": timetable})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def rate_event(conn, user_id, event_id, rate):
    cursor = conn.cursor()

    # Обновляем рейтинг события
    cursor.execute(
        "UPDATE user_event SET rate = ? WHERE user_id = ? AND event_id = ?",
        (rate, user_id, event_id),
    )
    conn.commit()


@app.route('/rate_event', methods=['POST'])
def rate_event_route():
    try:
        # Получаем данные из запроса
        data = request.get_json()
        user_id = data.get("user_id")
        event_id = data.get("event_id")
        rate = data.get("rate")

        if not all([user_id, event_id, rate]):
            return jsonify({"error": "user_id, event_id, and rate are required"}), 400

        # Обновляем рейтинг события
        conn = sqlite3.connect(DB_PATH)
        rate_event(conn, user_id, event_id, rate)
        conn.close()

        return jsonify({"message": "Event rated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
