import sqlite3
import os

# Путь к базе данных
db_path = os.path.join(os.path.dirname(__file__), 'app', 'events.db')

def check_categories():
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем все категории
        cursor.execute("SELECT id, name, description FROM categories")
        categories = cursor.fetchall()
        
        print(f"Найдено категорий: {len(categories)}")
        for category in categories:
            print(f"ID: {category[0]}, Name: {category[1]}, Description: {category[2]}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_categories() 