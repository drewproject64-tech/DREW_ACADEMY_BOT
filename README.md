# DREW ACADEMY

Three free text tools for @DREW_ACADEMY_BOT:

1. Text statistics: count words, characters and non-empty lines. Words use a Unicode word pattern that includes internal apostrophes and hyphens; counts may differ from a word processor.
2. Text cleanup: trim lines, collapse extra horizontal whitespace, and keep at most one blank line between paragraphs.
3. Case converter: choose uppercase, lowercase or title case, then paste text. Title case follows Python's Unicode rules and is not a grammar correction tool.

Tap /start for the three-button keyboard. `/stats text`, `/clean text` and `/case text` also work; `/case text` defaults to lowercase. Plain text without a selection returns statistics. Selected tools stay active for repeated inputs; `/cancel` clears the selection. Non-text messages receive instructions. Old inline buttons reopen the current menu.

## Setup

Python 3.12+, `pip install -r requirements.txt`, set `BOT_TOKEN` in the environment, run `python bot.py`. Docker is supported. Use one always-on worker per token. Never commit the token. `.env.example` is documentation; environment variables must actually be set by the host.

Name, About and complete Description are in `bot.py` and apply at startup. The token must belong to @DREW_ACADEMY_BOT. Add a profile image with BotFather. No user text is saved in a database or sent to AI services; Telegram and the host still process traffic. Only tool choices are kept in server memory.

## Verification

`python -m unittest discover -s tests -v`

After deploying, test /start and all three tools on mobile and desktop before requesting ad review. Code tests do not prove that the live bot is reachable. This is a permanent text-utility redesign; do not conceal or swap the service for unrelated offers after review. Telegram decides approval.

Matching ad text:

Count words and characters, clean extra spacing and change text case with DREW ACADEMY. Use three text tools directly in Telegram.

Destination: https://t.me/DREW_ACADEMY_BOT
