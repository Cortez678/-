import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ТОКЕН ВАШЕГО БОТА (уже вставлен)
BOT_TOKEN = "8171275175:AAFLn_gnh4DWoHwCP5e2j2VhXeFJq6xSVrg"

# Вопросы теста
QUESTIONS = [
    "Критика будет очевидно расстраивать человека, который получает ее в свой адрес",
    "Лучше отказаться от собственных интересов, чтобы угодить другим людям",
    "Чтобы быть счастливым, мне нужно получить одобрение других людей",
    "Если важный для меня человек от меня чего-либо ожидает, я должен это сделать",
    "Моя человеческая ценность очень сильно зависит от того, что обо мне думают другие."
]

# Варианты ответов с их числовыми значениями
OPTIONS = [
    ("Абсолютно согласен", -2),
    ("Отчасти согласен", -1),
    ("Отношусь нейтрально", 0),
    ("Отчасти несогласен", 1),
    ("Абсолютно несогласен", 2)
]

# Состояния для FSM
class TestState(StatesGroup):
    answering = State()
    question_index = State()
    answers = State()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def get_result_text(total_score: int) -> str:
    """Возвращает текст результата на основе итоговой суммы"""
    if -10 <= total_score < 0:
        return (
            f"📊 Ваш результат: {total_score} баллов\n\n"
            "❌ Вы избыточно зависимы, потому что смотрите на себя глазами других.\n\n"
            "Если кто-то оскорбляет или унижает вас, вы автоматически склонны "
            "занижать свою ценность. Так как ваше эмоциональное благополучие "
            "чрезвычайно зависит от того, что, по вашему представлению, люди о вас "
            "думают, вами легко манипулировать, и вы уязвимы для беспокойства и "
            "депрессии, когда другие высказывают критику и злятся на вас."
        )
    elif 0 <= total_score <= 10:
        return (
            f"📊 Ваш результат: {total_score} баллов\n\n"
            "✅ У вас есть независимость и здоровое чувство собственного достоинства, "
            "даже когда вы сталкиваетесь с критикой и неодобрением."
        )
    else:
        return f"📊 Ваш результат: {total_score} баллов"

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Приветственное сообщение и начало теста"""
    await state.clear()
    
    welcome_text = (
        "🧠 *Тест на зависимость от мнения окружающих*\n\n"
        "Этот тест поможет понять, насколько ваша самооценка зависит от того, "
        "что думают о вас другие люди.\n\n"
        "Вам будет предложено 5 утверждений. На каждое нужно ответить, "
        "насколько вы с ним согласны.\n\n"
        "Нажмите /start_test, чтобы начать."
    )
    
    await message.answer(welcome_text, parse_mode="Markdown")
    await message.answer("🚀 Нажмите /start_test для начала теста")

@dp.message(Command("start_test"))
async def start_test(message: types.Message, state: FSMContext):
    """Начинает тест"""
    await state.update_data(question_index=0, answers=[])
    await state.set_state(TestState.answering)
    await ask_question(message, state)

async def ask_question(message: types.Message, state: FSMContext):
    """Задает текущий вопрос с кнопками-ответами"""
    data = await state.get_data()
    index = data.get("question_index", 0)
    
    if index >= len(QUESTIONS):
        # Тест окончен, подводим итоги
        answers_list = data.get("answers", [])
        total_score = sum(answers_list)
        result_text = get_result_text(total_score)
        await message.answer(result_text, parse_mode="Markdown")
        await state.clear()
        return
    
    # Формируем клавиатуру с вариантами ответов
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=text, callback_data=str(score))]
            for text, score in OPTIONS
        ]
    )
    
    question_text = f"📝 *Вопрос {index + 1} из {len(QUESTIONS)}:*\n\n{QUESTIONS[index]}"
    await message.answer(question_text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(TestState.answering)
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает ответ пользователя"""
    score = int(callback.data)
    
    data = await state.get_data()
    answers_list = data.get("answers", [])
    answers_list.append(score)
    
    current_index = data.get("question_index", 0)
    next_index = current_index + 1
    
    await state.update_data(answers=answers_list, question_index=next_index)
    
    # Подтверждаем получение ответа
    await callback.answer("Ответ принят ✓")
    
    # Удаляем кнопки у предыдущего сообщения
    await callback.message.delete()
    
    # Задаем следующий вопрос
    if next_index < len(QUESTIONS):
        await ask_question(callback.message, state)
    else:
        # Если вопросы закончились, подводим итоги
        total_score = sum(answers_list)
        result_text = get_result_text(total_score)
        await callback.message.answer(result_text, parse_mode="Markdown")
        await state.clear()

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Помощь"""
    help_text = (
        "📖 *Команды бота:*\n\n"
        "/start - Приветствие и информация о тесте\n"
        "/start_test - Начать прохождение теста\n"
        "/help - Показать эту справку"
    )
    await message.answer(help_text, parse_mode="Markdown")

async def main():
    """Запуск бота"""
    print("🚀 Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
