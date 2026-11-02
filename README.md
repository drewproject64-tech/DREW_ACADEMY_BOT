# DREW ACADEMY

A simple educational bot for [@DREW_ACADEMY_BOT](https://t.me/DREW_ACADEMY_BOT).

## Three tools

1. **Lessons**: tap once to receive a digital skills lesson and exercise. Tap again for another lesson.
2. **Practice quiz**: tap once, then reply A, B or C. Receive the answer and an explanation. Each quiz is one question.
3. **Study planner**: enter daily minutes and days, such as `30 5`. Receive total study time and a daily review/practice/reflection split. Accepts 10–180 minutes and 1–7 days.

The persistent keyboard has exactly three buttons. Commands `/lessons`, `/quiz` and `/planner` provide the same tools. `/start`, `/help`, `/cancel` and `/privacy` support navigation and transparency. There are no nested topic menus, multi-question scores, payments, referrals or external redirects. Old inline buttons return users to the new menu.

## Run

Use Python 3.12 or newer. Install `pip install -r requirements.txt`, set `BOT_TOKEN` in the environment, then run `python bot.py`. `.env.example` is documentation; `.env` files are not loaded automatically. Docker is supported.

The name, About and complete Description are constants in `bot.py` and are applied on startup. The token must belong to @DREW_ACADEMY_BOT. Upload a profile image using BotFather.

Run one always-on background worker per token. Stop old polling instances. No HTTP port is required. Keep the educational purpose consistent before and after ad review.

## Data

Only the current question or planner mode is kept in memory. `/cancel`, switching tools and restarting clear the session. There is no user database or external AI service. Telegram and hosting providers process service traffic. Do not send sensitive information.

## Verify before advertising

Run `python -m unittest discover -s tests -v`. After deployment, send `/start` and test each button on mobile and desktop. A passing local test does not prove the live bot is reachable. Telegram decides approval; simplifying the bot does not guarantee it.

Matching ad text (under 160 characters):

> Learn digital skills with DREW ACADEMY. Read short lessons, answer practice questions and calculate a daily study plan directly in Telegram.

Destination: https://t.me/DREW_ACADEMY_BOT
