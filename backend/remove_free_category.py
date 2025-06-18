import sqlite3
import os

# Путь к базе данных
db_path = os.path.join(os.path.dirname(__file__), 'app', 'events.db')

def remove_free_category():
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Удаляем категорию FREE
        cursor.execute("DELETE FROM categories WHERE name = 'FREE'")
        deleted_count = cursor.rowcount
        
        if deleted_count > 0:
            print(f"Удалена категория FREE")
        else:
            print("Категория FREE не найдена")
        
        conn.commit()
        print("Операция завершена!")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    remove_free_category() 