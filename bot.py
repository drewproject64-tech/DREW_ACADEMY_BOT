"""Three simple educational tools for @DREW_ACADEMY_BOT."""
import logging
import os
import random
import httpx
from telegram import BotCommand, ReplyKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.request import HTTPXRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from content import LESSONS

NAME = 'DREW ACADEMY'
USERNAME = 'DREW_ACADEMY_BOT'
ABOUT = 'Short digital skills lessons, one-question practice quizzes and a simple study-plan calculator.'
DESCRIPTION = (
    'DREW ACADEMY offers three free educational tools directly in Telegram.\n\n'
    'Lessons: read a short digital skills lesson with a practical exercise.\n'
    'Practice quiz: answer one question and receive an explanation.\n'
    'Study planner: enter daily minutes and study days to calculate a plan.\n\n'
    'Tap Start and choose a button. No registration or payment is required.'
)
KEYBOARD = ReplyKeyboardMarkup([['Lessons'], ['Practice quiz'], ['Study planner']], resize_keyboard=True)
LOG = logging.getLogger(__name__)


def study_plan(text):
    parts = text.split()
    if len(parts) != 2 or any(not value.isascii() or not value.isdigit() for value in parts):
        raise ValueError('Enter two whole numbers: daily minutes and days. Example: 30 5')
    # Check length before int conversion, including maliciously oversized numbers.
    if any(len(value) > 3 for value in parts):
        raise ValueError('Choose 10–180 minutes per day and 1–7 days.')
    minutes, days = map(int, parts)
    if not 10 <= minutes <= 180 or not 1 <= days <= 7:
        raise ValueError('Choose 10–180 minutes per day and 1–7 days.')
    review = minutes // 3
    practice = minutes - review - 2
    return (f'Your study plan\n\n{minutes} minutes per day for {days} day(s).\n'
            f'Total study time: {minutes * days} minutes.\n\n'
            f'Each day:\n{review} minutes: read or recall a lesson.\n'
            f'{practice} minutes: complete its exercise or practice questions.\n'
            '2 minutes: write what you learned and your next step.\n\n'
            'Use Lessons to choose material, then Practice quiz to check your understanding.')


async def reply(message, text):
    await message.reply_text(text, reply_markup=KEYBOARD)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await reply(update.effective_message,
                'Welcome to DREW ACADEMY. Choose one of three free tools:\n\n'
                'Lessons — read a short digital skills lesson.\n'
                'Practice quiz — answer one question with feedback.\n'
                'Study planner — calculate a study plan.\n\n'
                'Tap a button below. You can also use /lessons, /quiz or /planner.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update.effective_message,
                'Choose a button or use /lessons, /quiz or /planner.\n'
                'For a quiz, reply A, B or C. For a plan, reply with minutes and days, such as 30 5.\n'
                '/cancel clears your current question or plan. /privacy explains data handling.')


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update.effective_message,
                'The bot keeps only your current quiz answer or planner mode in server memory. '
                'It does not create a user database or send inputs to AI services. '
                '/cancel clears your session; restarting the service also clears sessions. '
                'Telegram and the hosting provider process service traffic under their policies. '
                'Do not send passwords, login codes or sensitive personal information.')


async def lesson(message, context):
    context.user_data.clear()
    title = random.choice(list(LESSONS))
    await reply(message, f'{title}\n\n{LESSONS[title][0]}\n\nTap Lessons for another lesson.')


async def quiz(message, context):
    context.user_data.clear()
    title = random.choice(list(LESSONS))
    question, choices, correct, explanation = LESSONS[title][1]
    # Commit session state only after Telegram accepts the question.
    await reply(message, question + '\n\n' + '\n'.join(
        f'{letter}. {choice}' for letter, choice in zip('ABC', choices)) + '\n\nReply A, B or C.')
    context.user_data['quiz'] = (correct, choices[correct], explanation)


async def planner(message, context):
    context.user_data.clear()
    await reply(message, 'Enter your daily study minutes and number of days.\n\n'
                'Example: 30 5 means 30 minutes a day for 5 days.\n'
                'Choose 10–180 minutes and 1–7 days.')
    context.user_data['planner'] = True


async def feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.effective_message.text.split()[0].split('@')[0].lower()
    await {'/lessons': lesson, '/quiz': quiz, '/planner': planner}[command](update.effective_message, context)


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = (message.text or '').strip()
    action = {'lessons': lesson, 'practice quiz': quiz, 'study planner': planner}.get(text.lower())
    if action:
        await action(message, context)
    elif 'quiz' in context.user_data:
        if text.upper() not in ('A', 'B', 'C'):
            await reply(message, 'Please reply A, B or C, or tap a tool to switch.')
            return
        correct, answer, explanation = context.user_data['quiz']
        right = 'ABC'.index(text.upper()) == correct
        await reply(message, f"{'Correct.' if right else 'Keep practicing.'} Answer: {answer}\n\n{explanation}\n\nTap Practice quiz for another question.")
        context.user_data.clear()
    elif context.user_data.get('planner'):
        try:
            result = study_plan(text)
        except ValueError as error:
            await reply(message, str(error))
            return
        await reply(message, result)
        context.user_data.clear()
    else:
        await reply(message, 'Choose Lessons, Practice quiz or Study planner below. Use /help for instructions.')


async def legacy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Old messages may still contain inline buttons from the previous version.
    try:
        await update.callback_query.answer()
    except TelegramError:
        pass
    if update.effective_message:
        await start(update, context)


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        await reply(update.effective_message, 'Please use a menu button or /start. The tools accept text messages.')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    LOG.error('Telegram operation failed (%s)', type(context.error).__name__)
    if isinstance(update, Update) and update.effective_message:
        try:
            await reply(update.effective_message, 'The request could not be completed. Please try again or use /start.')
        except TelegramError:
            LOG.error('Recovery message could not be sent')


async def setup(application: Application):
    me = await application.bot.get_me()
    if (me.username or '').lower() != USERNAME.lower():
        raise RuntimeError('BOT_TOKEN must belong to @DREW_ACADEMY_BOT.')
    await application.bot.set_my_name(NAME)
    await application.bot.set_my_short_description(ABOUT)
    await application.bot.set_my_description(DESCRIPTION)
    await application.bot.set_my_commands([BotCommand(c, d) for c, d in [
        ('start', 'Open the three-tool menu'), ('lessons', 'Read a digital skills lesson'),
        ('quiz', 'Answer one practice question'), ('planner', 'Calculate a study plan'),
        ('help', 'Read instructions'), ('cancel', 'Clear your current session'), ('privacy', 'Read data information')]])
    LOG.warning('Profile configured for @%s; starting polling', me.username)


def api_request():
    return HTTPXRequest(connect_timeout=10, read_timeout=20, write_timeout=20,
                        httpx_kwargs={'transport': httpx.AsyncHTTPTransport(retries=2)})


def build_application(token):
    app = (Application.builder().token(token).request(api_request())
           .get_updates_request(api_request()).post_init(setup).build())
    app.add_handler(CommandHandler(['start', 'cancel'], start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('privacy', privacy))
    app.add_handler(CommandHandler(['lessons', 'quiz', 'planner'], feature))
    app.add_handler(CallbackQueryHandler(legacy_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.add_handler(MessageHandler(filters.ALL, fallback))
    app.add_error_handler(error_handler)
    return app


def main():
    token = os.environ.get('BOT_TOKEN', '').strip()
    if not token:
        raise SystemExit('Set BOT_TOKEN in the hosting environment before starting.')
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    build_application(token).run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
