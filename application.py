from flask import Flask, render_template, request, redirect, url_for, session
from services.interface import *
from services.database.database import *
import redis

r = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True , db=0)
app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route("/")
def index():
    return render_template('index.html')

#Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Получаем  данные о пользователе из формы
        username = request.form['username']
        password = request.form['password']
        password2 = request.form['password2']
        email = request.form['email']
        # Добавление информации из форм в ключи Redis
        r.set('users', username)
        r.set('pass', password)
        r.set('pass2', password2)
        r.set('email', email)
        # Валидция , сравнение паролей
        if r.get('pass') == r.get('pass2'):
            return redirect(url_for('login'))
        else:
            return "<h3>Пароли не совпадают<h3>"
    return render_template('register.html')

#Страница авторизации
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if r.get('users') == username and r.get('pass') == password:
            session['users'] = username
            return redirect(url_for('profile'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

# Главная страница пользователя со списком книг , их редактированием , добавлением , удалением и поиском
@app.route('/profile',methods=['GET'])
def profile():
    if 'users' in session:
        username = session['users']
        books = []
        # Получаем список всех ключей книг из Redis
        for book_key in r.lrange("books", 0, -1):
             # Получаем информацию о книге по ключу из Redis
            book = r.hgetall(book_key)
             # Извлекаем идентификатор книги из ключа и добавляем его в словарь с информацией о книге
            book_id = book_key.split(':')[1]
            book['id'] = book_id
            # Добавляем книгу в список книг для отображения на странице
            books.append(book)

    return render_template('profile.html',username=username , books=books)
    
# Страница добавления новой книги
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # Получаем  данные о книге из формы
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        year = request.form['year']
        publisher = request.form['publisher']
        description = request.form['description']

        book_data = {
            'title': title,
            'author': author,
            'genre': genre,
            'year': year,
            'publisher': publisher,
            'description': description
        }
        # Добавляем новую книгу, используя функцию add_book()
        add_book(book_data)
        return redirect(url_for('profile'))

    return render_template("add.html")
 

# Удаление книги
@app.route('/delete/<int:book_id>')
def delete(book_id):
    delete_book(book_id)
    return redirect(url_for('profile'))

# Страница редактирования книги
@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit(book_id):
    # Создаем ключ книги на основе полученного идентификатора
    book_key = f"book:{book_id}"
    if request.method == 'POST':
        # Получаем обновленные данные о книге из формы
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        year = request.form['year']
        publisher = request.form['publisher']
        description = request.form['description']

        book_data = {
            'title': title,
            'author': author,
            'genre': genre,
            'year': year,
            'publisher': publisher,
            'description': description
        }
        #обращаемся к функции update_book которая находится в services.database.database.py
        update_book(book_id, book_data)
        return redirect(url_for('profile'))

    book = r.hgetall(book_key)
    return render_template('edit.html', book=book, book_id=book_id)

# Страница поиска книг по всем атрибутам книги
@app.route('/search', methods=['GET', 'POST'])
def search():
    search_results = []
    error = None

    if request.method == 'POST':
        # Получаем поисковый запрос из формы
        search_query = request.form['search_query']
        # Ищем книги, которые содержат атрибуты(заголовок, автор, жанр, издательство и т.д)
        for book_key in r.lrange("books", 0, -1):
            #Итерируемся по всем ключам книг, хранящимся в Redis.
            book = r.hgetall(book_key)
            #Получаем информацию о книге из Redis, используя текущий ключ book_key.
            book_id = book_key.split(':')[1]
            #Извлекаем идентификатор книги из ключа book_key.
            book['id'] = book_id
            #Добавляем идентификатор книги в словарь book с информацией о книге.

            if search_query.lower() in book['title'].lower() or search_query.lower() in book['author'].lower() or \
                search_query.lower() in book['genre'].lower() or search_query.lower() in book['publisher'].lower():
                #Проверяем, содержится ли в поисковом запросе (в нижнем регисте) наши атрибуты
                search_results.append(book)
                #Добавляем текущую книгу в список результатов поиска search_results.
        
        # Если книги не найдены, показываем сообщение об ошибке
        if not search_results:
            error = "Книга не найдена"

    return render_template('search.html', books=search_results, error=error)


#выход из сессии
@app.route('/logout')
def logout():
    session.pop('users', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT
    )