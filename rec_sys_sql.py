import numpy as np
import sqlite3
from sklearn.metrics.pairwise import cosine_similarity
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix
from threadpoolctl import threadpool_limits

# === Функция для получения рекомендаций по ALS ===
def get_als_recommendations(user_interests, event_interests, factors=10, iterations=10, regularization=0.1, top_n=5):
    threadpool_limits(1, "blas")  # Ограничение потоков для работы с библиотеками BLAS

    # Разреженная матрица взаимодействий
    user_section_matrix = csr_matrix(user_interests @ event_interests.T)

    als_model = AlternatingLeastSquares(
        factors=factors, iterations=iterations, regularization=regularization
    )
    als_model.fit(user_section_matrix)

    als_scores = als_model.recommend(
        0, user_section_matrix, N=top_n, filter_already_liked_items=False
    )
    als_event_scores = np.zeros(event_interests.shape[0])
    for idx, event_id in enumerate(als_scores[0]):
        als_event_scores[event_id] = als_scores[1][idx]

    # Нормализация ALS-оценок
    als_event_scores /= np.max(als_event_scores) if np.max(als_event_scores) > 0 else 1

    return als_event_scores


# === Функция для получения рекомендаций на основе косинусного сходства ===
def get_cosine_recommendations(user_ratings, user_event_interests, event_interests):
    if len(user_ratings) == 0:
        return np.zeros(event_interests.shape[0])

    user_profile = np.dot(user_ratings, user_event_interests).astype(float)
    norm = np.linalg.norm(user_profile)
    if norm == 0:
        return np.zeros(event_interests.shape[0])  # Возврат нулевых оценок при отсутствии профиля

    user_profile /= norm  # Нормализация профиля пользователя
    cosine_scores = cosine_similarity([user_profile], event_interests)[0]

    # Нормализация косинусных оценок
    cosine_scores /= np.max(cosine_scores) if np.max(cosine_scores) > 0 else 1

    return cosine_scores


# === Гибридная рекомендация ===
def get_hybrid_recommendations(als_scores, cosine_scores, alpha=0.7):
    if als_scores is None or np.all(als_scores == 0):
        return cosine_scores if cosine_scores is not None else np.zeros_like(als_scores)
    if cosine_scores is None or np.all(cosine_scores == 0):
        return als_scores
    return alpha * als_scores + (1 - alpha) * cosine_scores


def get_recommendation(user_interests, event_interests, user_event_interests, user_ratings):
    als_event_scores = get_als_recommendations(user_interests, event_interests, top_n=10)
    cosine_scores = get_cosine_recommendations(user_ratings, user_event_interests, event_interests)
    final_scores = get_hybrid_recommendations(als_event_scores, cosine_scores, alpha=0.7)

    return als_event_scores, cosine_scores, final_scores


# === Преобразование тегов в вектор ===
def trans_tag_list_into_vector(tags, all_tags):
    return [1 if tag in tags else 0 for tag in all_tags]


# === Получение данных для рекомендаций ===
def get_data_from_db(conn, user_id):
    all_tags = [
        "музыка", "искусство", "театр", "кино", "наука",
        "образование", "экскурсии", "детям", "спорт",
        "литература", "кулинария", "танцы"
    ]

    cursor = conn.cursor()

    # Получение тегов пользователя
    cursor.execute("SELECT tags FROM user_tags WHERE user_id = ?;", (user_id,))
    user_tags = cursor.fetchone()[0]
    user_tags = trans_tag_list_into_vector(user_tags.split(', '), all_tags)
    print('user_tags',user_tags)

    # Преобразование тегов событий
    cursor.execute("SELECT tags FROM event_tags order by event_id;")
    event_tags = [trans_tag_list_into_vector(row[0].split(','), all_tags) for row in cursor.fetchall()]
    print('event_tags',event_tags)

    # Теги и оценки событий, посещенных пользователем
    cursor.execute("SELECT tags, rate FROM user_event WHERE user_id = ? AND rate is not Null;", (user_id,))
    user_event_data = cursor.fetchall()
    user_event_tags = [trans_tag_list_into_vector(row[0].split(','), all_tags) for row in user_event_data]
    rates = [row[1] for row in user_event_data]
    print('user_event_tags',user_event_tags)
    print('rates',rates)

    return user_tags, event_tags, user_event_tags, rates


# === Основная функция рекомендаций ===
def rec_sys(db_path, user_id):
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(db_path)

        # Получение данных
        user_tags, event_tags, user_event_tags, rates = get_data_from_db(conn, user_id)
        user_tags, event_tags = np.array(user_tags), np.array(event_tags)
        user_event_tags, rates = np.array(user_event_tags), np.array(rates)

        # Получение рекомендаций
        als, cos, final_scores = get_recommendation(user_tags, event_tags, user_event_tags, rates)

        # Отладочный вывод
        print("ALS scores:", als)
        print("Cosine scores:", cos)
        print("Final scores:", final_scores)

        # Топ-10 рекомендаций
        recommendations = np.argsort(-final_scores)[:5]
        print('recs', recommendations)
        result = []

        cursor = conn.cursor()

        # Получаем названия столбцов таблицы event_tags
        cursor.execute("PRAGMA table_info(event_tags);")
        column_names = [col[1] for col in cursor.fetchall()]

        # Формируем список словарей с данными
        for rec in recommendations:
            cursor.execute("SELECT * FROM event_tags WHERE event_id = ?;", (int(rec),))
            events = cursor.fetchall()

            # Преобразуем каждую строку в dict
            for event in events:
                result.append(dict(zip(column_names, event)))

        conn.close()

        # Возвращаем результат в виде списка словарей
        return result
    except Exception as e:
        print(f"Error in recommendation system: {e}")
        return []



# === Пример использования ===
db_path = 'hahahon.db'
user_id = 2  # ID пользователя
recommendations = rec_sys(db_path, user_id)
print("Рекомендации:", recommendations)
