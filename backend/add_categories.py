import sqlite3
import os

# Путь к базе данных
db_path = os.path.join(os.path.dirname(__file__), 'app', 'events.db')

# Категории для добавления
CATEGORIES = [
    ("CONFERENCE", "Конференция"),
    ("SEMINAR", "Семинар"),
    ("WORKSHOP", "Мастер-класс"),
    ("EXHIBITION", "Выставка"),
    ("CONCERT", "Концерт"),
    ("FESTIVAL", "Фестиваль"),
    ("SPORTS", "Спортивное мероприятие"),
    ("OTHER", "Другое")
]

def add_categories():
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли таблица categories
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        if not cursor.fetchone():
            print("Таблица categories не найдена")
            return
        
        # Добавляем категории
        for code, name in CATEGORIES:
            # Проверяем, существует ли уже такая категория
            cursor.execute("SELECT id FROM categories WHERE name = ?", (code,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO categories (name, description) VALUES (?, ?)",
                    (code, name)
                )
                print(f"Добавлена категория: {code} - {name}")
            else:
                print(f"Категория {code} уже существует")
        
        conn.commit()
        print("Категории успешно добавлены!")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_categories() 