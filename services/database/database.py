import redis
from typing import NamedTuple

r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True , db=0)


# Функция для добавления новой книги
def add_book(book_data):
    book_id = r.incr("book_id_counter")# Увеличиваем счетчик книг
    book_key = f"book:{book_id}"# Создаем ключ для хранения книги в Redis
    r.hmset(book_key, book_data)# Сохраняем книгу в Redis
    r.lpush("books", book_key)# Добавляем ключ книги в список всех книг
    return book_id


def delete_book(book_id):
    book_key = f"book:{book_id}"
    r.lrem("books", 0, book_key)
    r.delete(book_key)

def update_book(book_id, book_data):
    book_key = f"book:{book_id}"
    # Обновляем информацию о книге в Redis, используя созданный ключ и новые данные книги
    r.hmset(book_key, book_data)