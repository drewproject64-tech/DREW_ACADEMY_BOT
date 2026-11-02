"""Three simple text tools for @DREW_ACADEMY_BOT."""
import logging
import os
import re
import httpx
from telegram import BotCommand, ReplyKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.request import HTTPXRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

NAME = 'DREW ACADEMY'
USERNAME = 'DREW_ACADEMY_BOT'
ABOUT = 'Count words and characters, clean extra spacing and convert text case directly in Telegram.'
DESCRIPTION = (
    'DREW ACADEMY provides three free text tools.\n\n'
    'Text statistics: count words, characters and non-empty lines.\n'
    'Text cleanup: remove extra spaces and tidy line spacing.\n'
    'Case converter: choose uppercase, lowercase or title case.\n\n'
    'Tap Start, select a tool and paste your text. No registration or payment is required.'
)
TOOLS = {'Text statistics': 'stats', 'Text cleanup': 'clean', 'Case converter': 'case'}
KEYBOARD = ReplyKeyboardMarkup([[name] for name in TOOLS], resize_keyboard=True)
LOG = logging.getLogger(__name__)


def text_stats(text):
    words = re.findall(r"\w+(?:['’-]\w+)*", text, flags=re.UNICODE)
    return (f'Words: {len(words)}\nCharacters (including spaces): {len(text)}\n'
            f'Characters (excluding whitespace): {sum(not c.isspace() for c in text)}\n'
            f'Non-empty lines: {sum(bool(line.strip()) for line in text.splitlines())}')


def clean_text(text):
    lines = [re.sub(r'[^\S\n]+', ' ', line).strip() for line in text.splitlines()]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()


async def reply(message, text):
    # Keep each message within Telegram's UTF-16 length limit, including emoji.
    chunks, chunk, size = [], '', 0
    for char in text:
        units = len(char.encode('utf-16-le')) // 2
        if size + units > 3500:
            chunks.append(chunk)
            chunk, size = '', 0
        chunk += char
        size += units
    if chunk:
        chunks.append(chunk)
    for part in chunks:
        await message.reply_text(part, reply_markup=KEYBOARD, parse_mode=None)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await reply(update.effective_message,
        'Welcome to DREW ACADEMY. Choose a free text tool, then paste your text.\n\n'
        'Text statistics — count words, characters and lines.\n'
        'Text cleanup — remove extra spacing.\n'
        'Case converter — uppercase, lowercase or title case.\n\n'
        'Commands: /stats, /clean, /case. Use /cancel to reset.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update.effective_message,
        'Tap a tool and paste text, or send /stats text, /clean text or /case text.\n'
        'The case converter asks for UPPER, lower or Title before you paste.\n'
        'A text message without a selected tool returns statistics. /cancel resets the tool. '
        'Only text is supported. /privacy explains data handling.')


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update.effective_message,
        'Your text is processed on the bot server and is not saved to a user database or sent to AI services. '
        'Only your selected tool and case preference are kept in memory. /cancel clears them. '
        'Telegram and hosting providers process service traffic under their policies. '
        'Do not submit private passwords, login codes or sensitive information.')


async def choose(message, context, mode):
    context.user_data.clear()
    context.user_data['mode'] = mode
    if mode == 'case':
        await reply(message, 'Choose a case: reply UPPER, lower or Title. Then paste your text.')
    else:
        await reply(message, 'Paste the text you want to ' + ('count.' if mode == 'stats' else 'clean.'))


async def process(message, context, text):
    if not text.strip():
        await reply(message, 'Please send text containing at least one non-space character.')
        return
    mode = context.user_data.get('mode', 'stats')
    if mode == 'stats':
        result = text_stats(text)
    elif mode == 'clean':
        result = clean_text(text)
    else:
        style = context.user_data.get('style', 'lower')
        result = {'upper': str.upper, 'lower': str.lower, 'title': str.title}[style](text)
    await reply(message, result)


async def feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command, _, payload = update.effective_message.text.partition(' ')
    mode = {'/stats': 'stats', '/clean': 'clean', '/case': 'case'}[command.split('@')[0].lower()]
    await choose(update.effective_message, context, mode)
    if payload.strip():
        if mode == 'case':
            context.user_data['style'] = 'lower'
            await reply(update.effective_message, 'Using lowercase for /case text. Tap Case converter to choose another case.')
        await process(update.effective_message, context, payload)


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text or ''
    mode = next((value for label, value in TOOLS.items() if label.lower() == text.strip().lower()), None)
    if mode:
        await choose(message, context, mode)
    elif context.user_data.get('mode') == 'case' and 'style' not in context.user_data:
        style = text.strip().lower()
        if style not in ('upper', 'lower', 'title'):
            await reply(message, 'Please reply UPPER, lower or Title first, or tap another tool.')
            return
        context.user_data['style'] = style
        await reply(message, 'Now paste your text to convert to ' + style + ' case.')
    else:
        await process(message, context, text)


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
        ('start', 'Open the three-tool menu'), ('stats', 'Count words and characters'),
        ('clean', 'Clean extra spacing'), ('case', 'Convert text case'),
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
    app.add_handler(CommandHandler(['stats', 'clean', 'case'], feature))
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
