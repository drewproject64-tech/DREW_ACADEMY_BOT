"""DREW ACADEMY: three educational features, without external AI services."""
import logging
import os
import secrets
from telegram import BotCommand, InlineKeyboardButton as Button, InlineKeyboardMarkup as Markup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from content import LESSONS, make_plan

NAME = 'DREW ACADEMY'
USERNAME = 'DREW_ACADEMY_BOT'
ABOUT = 'Learn everyday digital skills with short lessons, practice quizzes and a personal study-plan builder.'
DESCRIPTION = (
    'Welcome to DREW ACADEMY, a free educational bot for everyday digital skills and study habits.\n\n'
    '1. Lessons: explore source checking, account security, clear writing, file organization, active learning and task planning.\n'
    '2. Practice quizzes: answer questions and read explanations.\n'
    '3. Study planner: choose a topic, daily study time and number of days to create a practical plan.\n\n'
    'Use /start to begin. No registration or payment is required.'
)
TOPICS = list(LESSONS)
LOG = logging.getLogger(__name__)


def keyboard(rows):
    return Markup([[Button(label, callback_data=data) for label, data in row] for row in rows])


def menu():
    return keyboard([[('Lessons', 'lessons')], [('Practice quiz', 'quiz')], [('Study planner', 'planner')]])


def topics(prefix):
    return keyboard([[(topic, f'{prefix}:{i}')] for i, topic in enumerate(TOPICS)] + [[('Main menu', 'menu')]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(
        'Welcome to DREW ACADEMY. Learn everyday digital skills and build useful study habits. Choose one of three tools:', reply_markup=menu())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        '/lessons — select a short lesson\n/quiz — practice five questions with explanations\n/planner — build a 1–7 day study plan\n'
        '/cancel — clear your current session\n/privacy — how data is handled\n\nUse the buttons below to begin.', reply_markup=menu())


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        'This bot uses your Telegram user ID to keep quiz and planner choices in server memory while it runs. '
        'It does not save a user database, send learning inputs to AI services, or request payments or contact details. '
        'Use /cancel to clear your session. Sessions also disappear when the bot restarts. '
        'Telegram processes messages under its own privacy policy. Hosting providers may process operational metadata. '
        'Please do not send passwords, login codes or sensitive personal information.')


async def feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.effective_message.text.split()[0].split('@')[0][1:]
    context.user_data.clear()
    if command == 'lessons':
        await update.effective_message.reply_text('Choose a lesson:', reply_markup=topics('lesson'))
    elif command == 'quiz':
        await begin_quiz(update.effective_message, context)
    else:
        await update.effective_message.reply_text('Choose your study topic:', reply_markup=topics('plan'))


async def begin_quiz(message, context):
    context.user_data.clear()
    context.user_data['quiz'] = {'items': secrets.SystemRandom().sample(TOPICS, 5), 'position': 0, 'score': 0, 'nonce': secrets.token_hex(4)}
    await ask_question(message, context)


async def ask_question(message, context):
    state = context.user_data['quiz']
    question, options, _, _ = LESSONS[state['items'][state['position']]][1]
    await message.reply_text(f"Question {state['position'] + 1}/5\n\n{question}", reply_markup=keyboard(
        [[(option, f"answer:{state['nonce']}:{state['position']}:{i}")] for i, option in enumerate(options)] + [[('Main menu', 'menu')]]))


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ''
    message = query.message
    if message is None:
        return
    if data == 'menu':
        context.user_data.clear()
        await message.reply_text('Choose a learning tool:', reply_markup=menu())
    elif data in ('lessons', 'planner', 'quiz'):
        context.user_data.clear()
        if data == 'quiz':
            await begin_quiz(message, context)
        else:
            await message.reply_text('Choose a topic:', reply_markup=topics('lesson' if data == 'lessons' else 'plan'))
    elif data.startswith(('lesson:', 'plan:')):
        prefix, raw = data.split(':')
        if not raw.isdigit() or not 0 <= int(raw) < len(TOPICS):
            return
        topic = TOPICS[int(raw)]
        if prefix == 'lesson':
            await message.reply_text(f'{topic}\n\n{LESSONS[topic][0]}', reply_markup=keyboard([[('More lessons', 'lessons')], [('Practice quiz', 'quiz')], [('Main menu', 'menu')]]))
        else:
            context.user_data.clear()
            context.user_data['plan_topic'] = topic
            await message.reply_text('How many minutes per day?', reply_markup=keyboard([[(str(n), f'minutes:{n}') for n in (15, 30, 45, 60)], [('Main menu', 'menu')]]))
    elif data.startswith('minutes:'):
        raw = data.split(':')[1]
        if 'plan_topic' not in context.user_data or raw not in ('15', '30', '45', '60'):
            await message.reply_text('Please start a new plan.', reply_markup=menu())
            return
        context.user_data['plan_minutes'] = int(raw)
        await message.reply_text('How many days?', reply_markup=keyboard([[(str(n), f'days:{n}') for n in range(1, 5)], [(str(n), f'days:{n}') for n in range(5, 8)], [('Main menu', 'menu')]]))
    elif data.startswith('days:'):
        raw = data.split(':')[1]
        if not raw.isdigit() or not 1 <= int(raw) <= 7 or 'plan_minutes' not in context.user_data:
            await message.reply_text('Please start a new plan.', reply_markup=menu())
            return
        plan = make_plan(context.user_data['plan_topic'], context.user_data['plan_minutes'], int(raw))
        context.user_data.clear()
        await message.reply_text(plan, reply_markup=menu())
    elif data.startswith('answer:'):
        parts = data.split(':')
        state = context.user_data.get('quiz')
        if len(parts) != 4 or not state or parts[1] != state['nonce'] or parts[2] != str(state['position']) or parts[3] not in ('0', '1', '2'):
            await message.reply_text('That question is no longer active. Use /quiz for a fresh quiz.')
            return
        _, options, correct, explanation = LESSONS[state['items'][state['position']]][1]
        right = int(parts[3]) == correct
        state['score'] += int(right)
        state['position'] += 1
        await query.edit_message_reply_markup(reply_markup=None)
        await message.reply_text(f"{'Correct.' if right else 'Keep practicing.'} Answer: {options[correct]}\n\n{explanation}")
        if state['position'] == len(state['items']):
            score = state['score']
            context.user_data.clear()
            await message.reply_text(f'Quiz complete: {score}/5. Review the lessons and try again whenever you like.', reply_markup=menu())
        else:
            await ask_question(message, context)


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text('Please choose a tool below, or use /help. Use /cancel to clear your current session.', reply_markup=menu())


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Do not log update contents or exception strings: these can contain private input or token URLs.
    LOG.error('Update failed (%s)', type(context.error).__name__)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text('Something went wrong. Please try /start again.')
        except Exception:
            LOG.error('Could not deliver recovery message')


async def setup(application: Application):
    me = await application.bot.get_me()
    if (me.username or '').lower() != USERNAME.lower():
        raise RuntimeError('BOT_TOKEN belongs to a different bot; use the token for DREW_ACADEMY_BOT.')
    await application.bot.set_my_name(NAME)
    await application.bot.set_my_short_description(ABOUT)
    await application.bot.set_my_description(DESCRIPTION)
    await application.bot.set_my_commands([BotCommand(c, d) for c, d in [
        ('start', 'Open the learning menu'), ('lessons', 'Read digital skills lessons'),
        ('quiz', 'Practice five questions'), ('planner', 'Build a study plan'),
        ('help', 'How to use the bot'), ('privacy', 'Data and privacy information'), ('cancel', 'Clear your session')]])


def main():
    token = os.environ.get('BOT_TOKEN', '').strip()
    if not token:
        raise SystemExit('Set BOT_TOKEN to the token from BotFather before starting.')
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    app = Application.builder().token(token).post_init(setup).build()
    app.add_handler(CommandHandler(['start', 'cancel'], start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('privacy', privacy))
    app.add_handler(CommandHandler(['lessons', 'quiz', 'planner'], feature))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.ALL, fallback))
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
