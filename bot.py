import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import config
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State


# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Подключение к БД
conn = sqlite3.connect("students.db")
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        tg_id INTEGER UNIQUE,
        name TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        variant_name TEXT UNIQUE
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        variant_id INTEGER,
        task_number INTEGER,
        image_path TEXT,
        correct_answer TEXT,
        FOREIGN KEY (variant_id) REFERENCES variants(id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        variant_id INTEGER,
        task_number INTEGER,
        answer TEXT,
        is_correct BOOLEAN,
        FOREIGN KEY (user_id) REFERENCES students(tg_id),
        FOREIGN KEY (variant_id) REFERENCES variants(id)
    )
""")
conn.commit()

logging.info("Таблицы БД созданы.")

# Проверяем, какие таблицы есть в базе
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
logging.info(f"Таблицы в базе: {tables}")

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
@dp.message(lambda message: message.text == "🏠 Ко всем действиям")
async def back_to_main_menu(message: types.Message):
    await message.answer("Ты вернулся в главное меню! Выбери действие:", reply_markup=student_keyboard)

# Клавиатура для ученика
student_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Математика"), KeyboardButton(text="Информатика")],
        [KeyboardButton(text="Мои результаты")],
        [KeyboardButton(text="Сбросить состояние")]
    ],
    resize_keyboard=True
)



# Клавиатура после регистрации (выбор предмета)
subject_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Математика")],
        [KeyboardButton(text="Информатика")],
        [KeyboardButton(text="🏠 Ко всем действиям")]
    ],
    resize_keyboard=True
)

# Клавиатура для математики (выбор части)
math_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 часть")],
        [KeyboardButton(text="2 часть")],
        [KeyboardButton(text="🏠 Ко всем действиям")]
    ],
    resize_keyboard=True
)
@dp.message(Command("reset"), StateFilter(None))
async def reset_state(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Состояние сброшено. Теперь ты можешь заново выбирать команды.")

# --- Регистрация ученика ---
# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я тренировочный бот. Чтобы зарегистрироваться, введи команду /register")





import logging
logging.basicConfig(level=logging.INFO)
from aiogram import F

logging.info("Регистрируем хендлер для /results...")
@dp.message(Command("results"), F.text.startswith("/results"))
async def show_results(message: types.Message):
    logging.info("Функция show_results вызвана!")

    if message.from_user.id != ADMIN_ID:
        print("Ошибка: Не администратор")
        await message.answer("Эта команда доступна только администратору.")
        return

    print("Проверяем, есть ли данные в таблицах...")

    # Проверяем, есть ли записи в user_answers
    cursor.execute("SELECT COUNT(*) FROM user_answers")
    count_user_answers = cursor.fetchone()[0]
    print(f"Всего записей в user_answers: {count_user_answers}")

    # Проверяем, есть ли записи в tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count_tasks = cursor.fetchone()[0]
    print(f"Всего записей в tasks: {count_tasks}")

    # Проверяем, есть ли записи в students
    cursor.execute("SELECT COUNT(*) FROM students")
    count_students = cursor.fetchone()[0]
    print(f"Всего записей в students: {count_students}")

    # Проверяем, есть ли записи в variants
    cursor.execute("SELECT COUNT(*) FROM variants")
    count_variants = cursor.fetchone()[0]
    print(f"Всего записей в variants: {count_variants}")

    print("Запрос в БД...")
    cursor.execute("""
        SELECT students.name, variants.variant_name, 
               (SELECT COUNT(*) FROM tasks WHERE tasks.variant_id = variants.id) AS total_tasks,
               SUM(CASE WHEN user_answers.answer = tasks.correct_answer THEN 1 ELSE 0 END) as correct_answers
        FROM variants
        JOIN students ON students.tg_id = user_answers.user_id
        LEFT JOIN user_answers ON variants.id = user_answers.variant_id
        LEFT JOIN tasks ON tasks.variant_id = variants.id AND tasks.task_number = user_answers.task_number
        GROUP BY students.name, variants.variant_name, total_tasks;
    """)

    results = cursor.fetchall()
    print(f"Результаты запроса: {results}")

    if not results:
        print("Ошибка: В БД нет результатов")
        await message.answer("Пока нет данных о прохождении вариантов.")
    else:
        text = "\n".join([f"{name} — {variant}: {correct}/{total}" for name, variant, total, correct in results])
        await message.answer(f"📊 *Результаты всех учеников:*\n{text}", parse_mode="Markdown")




# Обработчик команды /register
@dp.message(Command("register"))
async def register(message: types.Message, state: FSMContext):
    cursor.execute("SELECT * FROM students WHERE tg_id = ?", (message.from_user.id,))
    user = cursor.fetchone()

    if user:
        await message.answer("Ты уже зарегистрирован!", reply_markup=student_keyboard)
    else:
        await message.answer("Напиши своё имя:")
        await state.set_state(RegisterState.waiting_for_name)
class RegisterState(StatesGroup):
    waiting_for_name = State()
@dp.message(RegisterState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    cursor.execute("INSERT INTO students (tg_id, name) VALUES (?, ?)", (message.from_user.id, name))
    conn.commit()

    await message.answer(f"Спасибо, {name}! Ты зарегистрирован ✅", reply_markup=student_keyboard)
    await state.clear()  # Очищаем состояние



# Получаем имя ученика и записываем в базу
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    cursor.execute("INSERT INTO students (tg_id, name) VALUES (?, ?)", (message.from_user.id, name))
    conn.commit()

    await message.answer(f"Спасибо, {name}! Ты зарегистрирован ✅", reply_markup=subject_keyboard)

    await state.clear()  # Сбрасываем состояние, чтобы выйти из режима выбора варианта



# Обработчик нажатия "Математика"
@dp.message(lambda message: message.text == "Математика")
async def math_selected(message: types.Message):
    await message.answer("Выбери часть:", reply_markup=math_keyboard)

# --- Управление вариантами (админ) ---
ADMIN_ID = 156985269

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import F

# Определяем состояния для FSM
from aiogram.fsm.state import State, StatesGroup

class SolveVariantState(StatesGroup):
    solving_task = State()

class AddVariantState(StatesGroup):
    waiting_for_variant_name = State()
    waiting_for_images = State()
    waiting_for_answers = State()

# Админ начинает добавление варианта
@dp.message(Command("add_variant"))
async def add_variant(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
    await state.clear()

    await message.answer("Введите название варианта:")
    await state.set_state(AddVariantState.waiting_for_variant_name)

# Админ вводит название варианта
@dp.message(AddVariantState.waiting_for_variant_name)
async def process_variant_name(message: types.Message, state: FSMContext):
    variant_name = message.text.strip()

    # Добавляем вариант в базу данных
    cursor.execute("INSERT INTO variants (variant_name) VALUES (?)", (variant_name,))
    conn.commit()

    # Получаем ID нового варианта
    cursor.execute("SELECT id FROM variants WHERE variant_name = ?", (variant_name,))
    variant_id = cursor.fetchone()[0]

    # Сохраняем ID варианта в FSM
    await state.update_data(variant_id=variant_id, task_number=1)

    await message.answer(f"Вариант '{variant_name}' добавлен! Теперь отправь 12 изображений (одно за другим).")
    await state.set_state(AddVariantState.waiting_for_images)

# Обработчик получения изображений
import os
@dp.message(AddVariantState.waiting_for_images)
async def process_task_images(message: types.Message, state: FSMContext):
    data = await state.get_data()
    variant_id = data["variant_id"]
    task_number = data["task_number"]

    images_dir = "images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    local_path = f"{images_dir}/variant_{variant_id}_task_{task_number}.jpg"

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path

    await bot.download_file(file_path, local_path)

    cursor.execute(
        "INSERT INTO tasks (variant_id, task_number, image_path) VALUES (?, ?, ?)",
        (variant_id, task_number, local_path)
    )
    conn.commit()

    if task_number < 12:
        await state.update_data(task_number=task_number + 1)
        await message.answer(f"Задание {task_number} сохранено! Отправьте следующее изображение.")
    else:
        await message.answer("✅ Все 12 заданий загружены! Теперь введи правильные ответы по очереди.")
        await state.update_data(task_number=1) # Убедимся, что номер задания установлен
        await state.set_state(AddVariantState.waiting_for_answers)
        print(await state.get_state())  # Проверим, что состояние зафиксировалось


# --- Выбор варианта учеником ---
@dp.message(lambda message: message.text == "1 часть")
async def choose_variant(message: types.Message):
    cursor.execute("SELECT v.id, v.variant_name FROM variants v")
    variants = cursor.fetchall()

    if not variants:
        await message.answer("Пока нет доступных вариантов.")
        return

    variant_buttons = []
    for variant_id, variant_name in variants:
        # Получаем количество верных ответов
        cursor.execute("""
            SELECT COUNT(*) FROM user_answers ua
            JOIN tasks t ON ua.variant_id = t.variant_id AND ua.task_number = t.task_number
            WHERE ua.user_id = ? AND ua.variant_id = ? AND ua.answer = t.correct_answer
        """, (message.from_user.id, variant_id))
        correct_count = cursor.fetchone()[0]

        # Получаем общее число заданий
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE variant_id = ?", (variant_id,))
        total_tasks = cursor.fetchone()[0]

        # Формируем статус
        if correct_count == 0 and total_tasks > 0:
            status = "❌"  # Не решён или все ошибки
        else:
            status = f"✅ {correct_count}/{total_tasks}"

        # Добавляем вариант с его статусом
        variant_buttons.append([KeyboardButton(text=f"{variant_name} ({status})")])

    # **Здесь добавляем кнопку "🏠 Ко всем действиям"**
    variant_buttons.append([KeyboardButton(text="🏠 Ко всем действиям")])

    variant_keyboard = ReplyKeyboardMarkup(keyboard=variant_buttons, resize_keyboard=True)
    await message.answer("Выбери вариант:", reply_markup=variant_keyboard)



@dp.message(lambda message: message.text == "2 часть")
async def part_2_selected(message: types.Message):
    await message.answer("Ты выбрал 2 часть! (здесь будет функционал)")


async def send_task(message, state: FSMContext):
    data = await state.get_data()
    tasks = data["tasks"]
    current_task = data["current_task"]

    if current_task < len(tasks):
        task_number, image_path = tasks[current_task]

        from aiogram.types import FSInputFile
        photo = FSInputFile(image_path)  # Создаём объект FSInputFile

        await message.answer_photo(photo=photo, caption=f"Задание {task_number}")
        await message.answer("Введите ответ или нажмите 'Пропустить'", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True
        ))

        # ✅ Убеждаемся, что состояние установлено!
        await state.set_state(SolveVariantState.solving_task)

    else:
        await message.answer("✅ Все задания пройдены! Подсчитываем результаты...")
        await check_results(message, state)
        await state.clear()


@dp.message(SolveVariantState.solving_task)  # ✅ Фильтр по состоянию
async def process_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    tasks = data["tasks"]
    current_task = data["current_task"]
    variant_id = data["variant_id"]

    task_number, image_path = tasks[current_task]

    # Если ученик нажал "Пропустить", идём дальше
    if message.text.strip().lower() == "пропустить":
        await state.update_data(current_task=current_task + 1)
        await send_task(message, state)
        return

    # ✅ Сохраняем ответ ученика
    cursor.execute(
        "INSERT INTO user_answers (user_id, variant_id, task_number, answer) VALUES (?, ?, ?, ?)",
        (message.from_user.id, variant_id, task_number, message.text.strip())
    )
    conn.commit()

    # ✅ Переход к следующему заданию
    await state.update_data(current_task=current_task + 1)
    await send_task(message, state)

import logging
logging.basicConfig(level=logging.INFO)

from aiogram.filters.state import StateFilter  # Добавь этот импорт!

@dp.message(StateFilter(AddVariantState.waiting_for_answers))  # Фильтр на состояние!
async def process_correct_answers(message: types.Message, state: FSMContext):
    logging.info(f"ВЫЗОВ ОБРАБОТКИ ОТВЕТА: {message.text}, Состояние: {await state.get_state()}")

    data = await state.get_data()
    variant_id = data.get("variant_id")
    task_number = data.get("task_number", 1)

    logging.info(f"Поступил ответ: {message.text} для задания {task_number}, вариант {variant_id}")
    print(await state.get_state())  # Проверяем текущее состояние

    correct_answer = message.text.strip()

    cursor.execute(
        "UPDATE tasks SET correct_answer = ? WHERE variant_id = ? AND task_number = ?",
        (correct_answer, variant_id, task_number)
    )
    conn.commit()

    if task_number < 12:
        await state.update_data(task_number=task_number + 1)
        await message.answer(f"Ответ для задания {task_number} сохранён. Введи следующий.")
    else:
        await message.answer("✅ Все правильные ответы сохранены! Вариант готов для учеников.")
        await state.clear()

import re
# Показываем результаты ученика
@dp.message(lambda message: message.text == "Мои результаты")
async def show_user_results(message: types.Message):
    cursor.execute("""
        SELECT v.variant_name, 
               (SELECT COUNT(*) FROM tasks WHERE tasks.variant_id = v.id) AS total_tasks,
               COUNT(a.id) as total_answers,
               SUM(CASE WHEN a.answer = t.correct_answer THEN 1 ELSE 0 END) as correct_answers
        FROM variants v
        LEFT JOIN user_answers a ON v.id = a.variant_id AND a.user_id = ?
        LEFT JOIN tasks t ON t.variant_id = v.id AND t.task_number = a.task_number
        WHERE v.id IN (SELECT variant_id FROM user_answers WHERE user_id = ?)
        GROUP BY v.variant_name, total_tasks;
    """, (message.from_user.id, message.from_user.id))
    results = cursor.fetchall()

    if not results:
        await message.answer("Ты пока не решал ни одного варианта.")
    else:
        text = "\n".join([f"{variant} — {correct}/{total}" for variant, total, answered, correct in results])
        await message.answer(f"📊 *Твои результаты:*\n{text}", parse_mode="Markdown")


# Сброс состояния
@dp.message(lambda message: message.text == "Сбросить состояние")
async def reset_state(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Состояние сброшено. Теперь ты можешь заново выбирать варианты.", reply_markup=student_keyboard)


async def show_variant_results(message: types.Message, variant_id: int):
    cursor.execute("SELECT task_number, correct_answer FROM tasks WHERE variant_id = ?", (variant_id,))
    correct_answers = {task_number: answer for task_number, answer in cursor.fetchall()}

    cursor.execute("""
        SELECT task_number, answer FROM user_answers
        WHERE user_id = ? AND variant_id = ?
    """, (message.from_user.id, variant_id))
    user_answers = {task_number: answer for task_number, answer in cursor.fetchall()}

    correct_count = 0
    incorrect_tasks = []
    result_text = "📊 *Результаты решения:*\n"

    for task_number, correct_answer in correct_answers.items():
        user_answer = user_answers.get(task_number, "—")
        is_correct = (user_answer == correct_answer)

        if is_correct:
            correct_count += 1
            result_text += f"✅ {task_number}. *{user_answer}* (правильно)\n"
        else:
            result_text += f"❌ {task_number}. *{user_answer}* (неверно, должно быть: {correct_answer})\n"
            incorrect_tasks.append(task_number)

    result_text += f"\n🎯 *Итог:* {correct_count} / {len(correct_answers)} заданий верно."
    await message.answer(result_text, parse_mode="Markdown")

    # Отправляем фото заданий с ошибками
    if incorrect_tasks:
        await message.answer("📌 Вот задания, где были ошибки:")
        for task_number in incorrect_tasks:
            cursor.execute("""
                SELECT image_path FROM tasks
                WHERE variant_id = ? AND task_number = ?
            """, (variant_id, task_number))
            image_path = cursor.fetchone()

            if image_path:
                from aiogram.types import FSInputFile
                await message.answer_photo(FSInputFile(image_path[0]), caption=f"❌ Ошибка в задании {task_number}")


async def start_test(message: types.Message, state: FSMContext, variant_id: int):
    cursor.execute("SELECT task_number, image_path FROM tasks WHERE variant_id = ? ORDER BY task_number", (variant_id,))
    tasks = cursor.fetchall()

    if not tasks:
        await message.answer("Этот вариант пока пуст.")
        return

    await state.update_data(variant_id=variant_id, tasks=tasks, current_task=0)
    await send_task(message, state)
    await state.set_state(SolveVariantState.solving_task)






# Команда /students для администратора (замени на свой ID)
ADMIN_ID = 156985269  # Твой Telegram ID

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Состояния для прохождения варианта
class SolveVariantState(StatesGroup):
    solving_task = State()

@dp.message()
async def start_variant(message: types.Message, state: FSMContext):
    variant_name = message.text.split(" (")[0]  # Убираем статус (❌ или ✅)
    logging.info(f"Выбран вариант: {variant_name}")

    cursor.execute("SELECT id FROM variants WHERE variant_name = ?", (variant_name,))
    variant = cursor.fetchone()

    if not variant:
        await message.answer("Такого варианта нет. Выберите из списка.")
        return

    variant_id = variant[0]

    # Проверяем, решал ли ученик этот вариант
    cursor.execute("""
        SELECT COUNT(*) FROM user_answers
        WHERE user_id = ? AND variant_id = ?
    """, (message.from_user.id, variant_id))
    answers_count = cursor.fetchone()[0]

    if answers_count > 0:
        # Ученик уже решал этот вариант – показываем результаты
        await show_variant_results(message, variant_id)


    else:
        # Ученик еще не решал – запускаем тест
        await start_test(message, state, variant_id)


async def send_task(message, state):
    data = await state.get_data()
    tasks = data["tasks"]
    current_task = data["current_task"]

    if current_task < len(tasks):
        task_number, image_path = tasks[current_task]
        from aiogram.types import FSInputFile  # Добавь импорт

        photo = FSInputFile(image_path)  # Создаём объект FSInputFile
        await message.answer_photo(photo=photo, caption=f"Задание {task_number}")

        await message.answer("Введите ответ или нажмите 'Пропустить'", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True
        ))
    else:
        await message.answer("✅ Все задания пройдены! Подсчитываем результаты...")
        await check_results(message, state)
        await state.clear()

@dp.message(SolveVariantState.solving_task)
async def process_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    tasks = data["tasks"]
    current_task = data["current_task"]
    variant_id = data["variant_id"]

    task_number, image_path = tasks[current_task]

    # Если ученик нажал "Пропустить", идём дальше
    if message.text == "Пропустить":
        await state.update_data(current_task=current_task + 1)
        await send_task(message, state)
        return

    # Сохраняем ответ ученика
    cursor.execute(
        "INSERT INTO user_answers (user_id, variant_id, task_number, answer) VALUES (?, ?, ?, ?)",
        (message.from_user.id, variant_id, task_number, message.text)
    )
    conn.commit()

    # Переход к следующему заданию
    await state.update_data(current_task=current_task + 1)
    await send_task(message, state)

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
@dp.message(lambda message: message.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    subject_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Математика")],
            [KeyboardButton(text="Информатика")],
            [KeyboardButton(text="🏠 Ко всем действиям")]
        ],
        resize_keyboard=True
    )
    await message.answer("Вы вернулись в главное меню! Выберите предмет:", reply_markup=subject_keyboard)

async def check_results(message, state):
    data = await state.get_data()
    variant_id = data["variant_id"]

    cursor.execute("SELECT task_number, correct_answer FROM tasks WHERE variant_id = ?", (variant_id,))
    correct_answers = {task_number: answer for task_number, answer in cursor.fetchall()}

    cursor.execute(
        "SELECT task_number, answer FROM user_answers WHERE user_id = ? AND variant_id = ?",
        (message.from_user.id, variant_id)
    )
    user_answers = {task_number: answer for task_number, answer in cursor.fetchall()}

    correct_count = 0
    result_text = "📊 *Результаты решения:*\n"

    for task_number, correct_answer in correct_answers.items():
        user_answer = user_answers.get(task_number, "—")
        is_correct = (user_answer == correct_answer)

        if is_correct:
            correct_count += 1
            result_text += f"✅ {task_number}. *{user_answer}* (правильно)\n"
        else:
            result_text += f"❌ {task_number}. *{user_answer}* (неверно, должно быть: {correct_answer})\n"

    result_text += f"\n🎯 *Итог:* {correct_count} / {len(correct_answers)} заданий верно."

    # Создаём кнопку "Главное меню"
    main_menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
        resize_keyboard=True
    )

    await message.answer(result_text, parse_mode="Markdown", reply_markup=main_menu_keyboard)
    await state.clear()  # Очищаем состояние после завершения теста


from aiogram.filters import StateFilter  # Добавь импорт


@dp.message(Command("students"))
async def show_students(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return

    cursor.execute("SELECT name FROM students")
    students = cursor.fetchall()

    if not students:
        await message.answer("Пока нет зарегистрированных учеников.")
    else:
        text = "\n".join([f"- {name}" for (name,) in students])
        await message.answer(f"Список учеников:\n{text}")



@dp.message(lambda message: not message.text.startswith("/"))
async def start_variant(message: types.Message, state: FSMContext):
    variant_name = message.text.split(" (")[0]  # Убираем статус из названия варианта
    logging.info(f"Выбран вариант: {variant_name}")

    # Проверяем, существует ли такой вариант в БД
    cursor.execute("SELECT id FROM variants WHERE variant_name = ?", (variant_name,))
    variant = cursor.fetchone()

    if not variant:
        await message.answer("Такого варианта нет. Выберите из списка.")
        return

    variant_id = variant[0]

    # Проверяем, решал ли ученик этот вариант
    cursor.execute("""
        SELECT COUNT(*) FROM user_answers
        WHERE user_id = ? AND variant_id = ?
    """, (message.from_user.id, variant_id))
    answers_count = cursor.fetchone()[0]

    if answers_count > 0:
        # Ученик уже проходил этот вариант – сразу показываем результаты
        await show_results(message, variant_id)
    else:
        # Ученик еще не решал – запускаем тест
        await start_test(message, state, variant_id)




# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
s = []

