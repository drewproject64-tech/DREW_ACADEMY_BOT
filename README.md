# DREW ACADEMY

Telegram username: [@DREW_ACADEMY_BOT](https://t.me/DREW_ACADEMY_BOT).

A free English-language educational bot with exactly three learning features:

1. **Lessons** — six original lessons on source checking, account security, clear writing, file organization, active learning and task planning. Each includes a practical exercise.
2. **Practice quiz** — five randomized questions, answer explanations and a final score. Old or repeated answers cannot change the score.
3. **Study planner** — select a topic, 15/30/45/60 minutes per day and 1–7 days. Receive a complete plan directly in the chat.

No AI key, payments, referrals, financial services, forced channel joins or redirect menus. The bot is a standalone educational service and should retain that purpose after advertising review.

## Start locally

Use Python 3.12 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN='your-token-from-BotFather'
python bot.py
```

Do not commit your token. `.env.example` is documentation; the program reads the actual environment, not a `.env` file. Startup validates the bot username before changing the profile, then sets its name, About (short description), Description and command menu from constants in `bot.py`.

## Hosting

Run as one always-on background worker. Build: `pip install -r requirements.txt`. Start: `python bot.py`. Set `BOT_TOKEN` in the host's secret environment settings. Docker is also supported. No HTTP port is exposed: this is a polling bot, not a web service. Keep only one instance per token and remove any previous webhook before switching to polling. Stop any older deployment using this token to avoid polling conflicts.

## Profile and review

Create/register the username through BotFather if you have not already. Add an original DREW ACADEMY profile image through BotFather; this code does not upload an avatar. Deploy and check `/start`, all six lessons, a full quiz and several planner combinations on mobile and desktop before submitting ads. The source code alone does not make the bot live.

About: Learn everyday digital skills with short lessons, practice quizzes and a personal study-plan builder.

The complete Description lives in `bot.py`. Keep English ad text, targeting and destination consistent. Never swap the bot to unrelated offers or conceal content for review. Neither this implementation nor its topic guarantees approval or a review deadline.

Suggested ad text (under 160 characters):

> Learn everyday digital skills with DREW ACADEMY. Explore short lessons, practice quizzes and build a study plan directly in Telegram.

Destination: https://t.me/DREW_ACADEMY_BOT

Official guidance: https://ads.telegram.org/guidelines and https://ads.telegram.org/tos

## Data and operation

Quiz/planner selections live only in memory, keyed by Telegram user ID. `/cancel` clears the current user's session. Restarting clears all sessions. No user database or third-party AI service is used. Telegram and your host still process service traffic and operational metadata. Error logs omit incoming updates and exception strings. `/privacy` explains this in the bot. Idle sessions remain in memory until cleared or restarted; consider expiry if operating at significant scale.

## Verification

```bash
python -m unittest discover -s tests -v
python -m compileall -q bot.py content.py
```
