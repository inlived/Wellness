import pytesseract
from PIL import Image
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

    cursor.execute('''
        INSERT INTO general_blood_test (hemoglobin)
        VALUES (?)
    ''', (data.get('hemoglobin'),))
    conn.commit()
    conn.close()


# Функция для обработки распознанного текста и извлечения данных анализов
def process_recognized_text(text):
    # Пример регулярных выражений для извлечения показателей общего анализа крови
    general_blood_test_data = {'hemoglobin': re.search(r'Гемоглобин[:\s]+(\d+\.?\d*)', text)}

    # Используем регулярные выражения для поиска значений

    # Преобразуем найденные значения в числа, если они найдены
    general_blood_test_data = {k: float(v.group(1)) if v else None for k, v in general_blood_test_data.items()}

    # Вставляем данные в базу данных в зависимости от типа анализа
    if any(general_blood_test_data.values()):
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
            # print(f"Распознанный текст с изображения {image_path}:\n{recognized_text}\n")
    else:
        print("Изображения не выбраны")
