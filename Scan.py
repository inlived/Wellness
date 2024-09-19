import pytesseract
from PIL import Image
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import sqlite3
import re

# Функция для выбора нескольких файлов пользователем
def upload_images():
    file_paths = filedialog.askopenfilenames(
        title="Выберите изображения",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
    )
    if file_paths:
        return file_paths
    else:
        return None


# Функция для распознавания текста с изображения
def ocr_image(path):
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img, lang='rus+eng')  # Замените 'eng' на нужный вам язык
        return text
    except Exception as e:
        print(f"Ошибка при обработке изображения {path}: {e}")


def create_database():
    conn = sqlite3.connect('medical_tests.db')
    cursor = conn.cursor()

    # Дропаем таблицу для дебага
    cursor.execute(''' drop table if exists general_blood_test ''')

    # Создаем таблицу для общих анализов крови
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS general_blood_test (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hemoglobin REAL,
        date DATE DEFAULT CURRENT_DATE
    )
    ''')
    conn.commit()
    conn.close()


# Функция для подключения к базе данных
def connect_db():
    return sqlite3.connect('medical_tests.db')


# Функция для добавления данных общего анализа крови в базу данных
def insert_general_blood_test(data):
    conn = connect_db()
    cursor = conn.cursor()

    # Преобразуем объект 'date' в строку формата 'YYYY-MM-DD' перед вставкой
    hemoglobin = data.get('hemoglobin')

    date = data.get('date')
    if date:
        date = date.strftime('%Y-%m-%d')  # Преобразуем объект 'date' в строку

    columns = ['hemoglobin']  # Обязательные данные
    values = [hemoglobin]  # Обязательные значения

    # Добавляем дату, если она есть
    if date:
        columns.append('date')
        values.append(date)

    # Формируем динамический запрос с подстановкой столбцов и значений
    query = f'''
            INSERT INTO general_blood_test ({', '.join(columns)})
            VALUES ({', '.join(['?'] * len(values))})
        '''

    cursor.execute(query, values)
    conn.commit()
    conn.close()

# Функция для обработки распознанного текста и извлечения данных анализов
def process_recognized_text(text):
    # Регулярное выражение для даты взятия анализа
    date_regex = r'''(?:Дата\s*(?:взятия\s*(?:биоматериала|анализа|образца)|анализа|приёма|сдачи|исследования|получения|регистрации\s*заказа))\s*[:\-]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})  # Формат даты'''

    # Регулярное выражение для извлечения показателей общего анализа крови
    general_blood_test_data = {
        'hemoglobin': re.search(r'Гемоглобин[:\s]+(\d+\.?\d*)', text, re.IGNORECASE),
        'date': re.search(date_regex, text, re.IGNORECASE)
    }

    # Преобразуем найденные значения в числа (для гемоглобина)
    if general_blood_test_data['hemoglobin']:
        general_blood_test_data['hemoglobin'] = float(general_blood_test_data['hemoglobin'].group(1))

    # Преобразуем найденную дату в строку или объект даты
    if general_blood_test_data['date']:
        date_str = general_blood_test_data['date'].group(1)
        try:
            # Преобразуем строку в объект даты
            general_blood_test_data['date'] = datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError:
            # Если формат отличается, например, '12/09/23', попробуем другой формат
            general_blood_test_data['date'] = datetime.strptime(date_str, '%d/%m/%y').date()

    # Вставляем данные в базу данных, если есть валидные значения
    if general_blood_test_data['hemoglobin']:
        insert_general_blood_test(general_blood_test_data)
        print("Данные общего анализа крови добавлены.")

# Основной скрипт
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Скрыть главное окно tkinter

    # Вызов функции загрузки файлов
    image_paths = upload_images()
    recognized_text = ""
    create_database()
    if image_paths:
        # Пройти по каждому выбранному изображению и распознать текст
        for image_path in image_paths:
            recognized_text = ocr_image(image_path)
            process_recognized_text(recognized_text)
            # Это пример текста, который был распознан из фото
            # recognized_text = "Гемоглобин: 135"
            # Вывод текста в консоль для дебага
            print(f"Распознанный текст с изображения {image_path}:\n{recognized_text}\n")
    else:
        print("Изображения не выбраны")
