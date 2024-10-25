import pytesseract
from PIL import Image
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import re
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter

# Стилизация графика
plt.style.use('ggplot')

# Создаём главное окно
root = tk.Tk()
root.title("Анализ медицинских данных")
root.geometry("900x600")

# Настраиваем фон окна
root.configure(bg='#f4f4f9')

# Настраиваем subplot для графика
fig, ax = plt.subplots()
fig.patch.set_facecolor('#f4f4f9')
canvas = FigureCanvasTkAgg(fig, master=root)

def initialize():
    create_database()
    create_gui()
    display_table_and_plot()
    check_last_test_date()
    root.mainloop()

def style_graph():
    ax.set_facecolor('#f4f4f9')
    ax.grid(color='gray', linestyle=':', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.tick_params(axis='x', colors='#333333', labelsize=10)
    ax.tick_params(axis='y', colors='#333333', labelsize=10)
    ax.set_xlabel('Дата', fontsize=12, color='#333333', labelpad=10)
    ax.set_ylabel('Показатели', fontsize=12, color='#333333', labelpad=10)

def create_gui():
    style_graph()
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().pack()
    button = tk.Button(root, text="Выбрать файл", command=upload_images,
                       bg='#3498db', fg='white', font=('Helvetica', 12), padx=10, pady=5)
    button.pack(expand=True, anchor='center')
    button.place(relx=0.1, rely=0.05, anchor='center')

def upload_images():
    file_paths = filedialog.askopenfilenames(
        title="Выберите изображения",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
    )
    if file_paths:
        scan_files(file_paths)
    else:
        return None

def scan_files(image_paths):
    if image_paths:
        for image_path in image_paths:
            recognized_text = ocr_image(image_path)
            process_recognized_text(recognized_text)
        display_table_and_plot()
    else:
        print("Изображения не выбраны")

def ocr_image(path):
    try:
        img = Image.open(path).convert('L')
        text = pytesseract.image_to_string(img, lang='rus', config='--psm 4')
        return text
    except Exception as e:
        print(f"Ошибка при обработке изображения {path}: {e}")

def create_database():
    conn = sqlite3.connect('medical_tests.db')
    cursor = conn.cursor()
    # Дропаем таблицу для дебага
    # cursor.execute(''' drop table if exists general_blood_test ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS general_blood_test (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hemoglobin REAL,
        wbc REAL,
        plt REAL,
        rbc REAL,
        date DATE DEFAULT CURRENT_DATE
    )
    ''')
    conn.commit()
    conn.close()

def connect_db():
    return sqlite3.connect('medical_tests.db')

def insert_general_blood_test(data):
    conn = connect_db()
    cursor = conn.cursor()
    date = data.get('date')
    if date:
        date = date.strftime('%Y-%m-%d')

    columns = ['hemoglobin', 'wbc', 'plt', 'rbc']
    values = [data.get('hemoglobin'), data.get('wbc'), data.get('plt'), data.get('rbc')]

    if date:
        columns.append('date')
        values.append(date)

    query = f'''
        INSERT INTO general_blood_test ({', '.join(columns)})
        VALUES ({', '.join(['?'] * len(values))})
    '''
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def process_recognized_text(text):
    date_regex = r'(?:Дата|Дата и время)\s*(?:взятия\s*(?:биоматериала|анализа|образца)|анализа|приёма|сдачи|исследования|получения|регистрации\s*(?:заказа)|)\s*[:\-]?\s*(\d{1,2}[.\-\/]\d{1,2}[.\-\/]\d{2,4})'
    hemoglobin_regex = r'Гемоглобин\s*(?:\(\w*\d*\)|)[:\s:\-]+(\d+\.?\d*)'
    wbc_regex = r'Лейкоциты\s*(?:\(\w*\d*\)|)[:\s:\-]+(\d+\.?\d*)'
    plt_regex = r'Тромбоциты\s*(?:\(\w*\d*\)|)[:\s:\-]+(\d+\.?\d*)'
    rbc_regex = r'Эритроциты\s*(?:\(\w*\d*\)|)[:\s:\-]+(\d+\.?\d*)'

    general_blood_test_data = {
        'hemoglobin': re.search(hemoglobin_regex, text, re.IGNORECASE),
        'wbc': re.search(wbc_regex, text, re.IGNORECASE),
        'plt': re.search(plt_regex, text, re.IGNORECASE),
        'rbc': re.search(rbc_regex, text, re.IGNORECASE),
        'date': re.search(date_regex, text, re.IGNORECASE)
    }

    for key in ['hemoglobin', 'wbc', 'plt', 'rbc']:
        if general_blood_test_data[key]:
            general_blood_test_data[key] = float(general_blood_test_data[key].group(1))

    if general_blood_test_data['date']:
        date_str = general_blood_test_data['date'].group(1)
        try:
            general_blood_test_data['date'] = datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError:
            general_blood_test_data['date'] = datetime.strptime(date_str, '%d/%m/%y').date()

    if any(general_blood_test_data[key] for key in ['hemoglobin', 'wbc', 'plt', 'rbc']):
        insert_general_blood_test(general_blood_test_data)
        print("Данные общего анализа крови добавлены.")

def get_blood_test_data():
    conn = sqlite3.connect('medical_tests.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT hemoglobin, wbc, plt, rbc, date
        FROM general_blood_test
        WHERE date IS NOT NULL
        ORDER BY date
    ''')
    data = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(data, columns=['hemoglobin', 'wbc', 'plt', 'rbc', 'date'])
    df['date'] = pd.to_datetime(df['date'])
    return df

def display_table_and_plot():
    df = get_blood_test_data()
    ax.clear()
    style_graph()
    if not df.empty:
        ax.plot(df['date'], df['hemoglobin'], marker='d', linestyle=':', color='#2c3e50', label="Гемоглобин")
        ax.plot(df['date'], df['wbc'], marker='o', linestyle='-', color='#e74c3c', label="Лейкоциты")
        ax.plot(df['date'], df['plt'], marker='s', linestyle='--', color='#3498db', label="Тромбоциты")
        ax.plot(df['date'], df['rbc'], marker='^', linestyle='-.', color='#2ecc71', label="Эритроциты")
        ax.legend(loc='upper right', frameon=False)
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        canvas.draw()

# Функция для проверки последнего анализа и создания напоминания
def check_last_test_date():
    conn = connect_db()
    cursor = conn.cursor()

    # Получаем дату последнего анализа из базы данных
    cursor.execute('''
        SELECT MAX(date)
        FROM general_blood_test
    ''')
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        last_test_date = datetime.strptime(result[0], '%Y-%m-%d').date()

        # Рассчитываем разницу между сегодняшней датой и датой последнего анализа
        days_since_last_test = (datetime.now().date() - last_test_date).days

        # Если прошло больше 6 месяцев (примерно 180 дней), выводим напоминание
        if days_since_last_test > 180:
            messagebox.showwarning("Напоминание", "Пора сдать анализы! Последний анализ был сделан более 6 месяцев назад.")
    else:
        # Если данных о последних анализах нет, можно предложить пользователю загрузить данные
        messagebox.showinfo("Напоминание", "Данных об анализах нет. Пожалуйста, загрузите результаты анализов.")


if __name__ == "__main__":
    initialize()