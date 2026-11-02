import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
import bot

class ToolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.message = SimpleNamespace(text='', reply_text=AsyncMock())
        self.update = SimpleNamespace(effective_message=self.message)
        self.context = SimpleNamespace(user_data={})

    async def send(self, text):
        self.message.text = text
        await bot.text_message(self.update, self.context)

    async def test_default_stats(self):
        await self.send('Hello world\nNew line')
        self.assertIn('Words: 4', self.message.reply_text.call_args.args[0])
        self.assertIn('Non-empty lines: 2', self.message.reply_text.call_args.args[0])

    async def test_cleanup_and_switching(self):
        await self.send('Text cleanup')
        await self.send('  Hello   world  \n\n\n line ')
        self.assertEqual(self.message.reply_text.call_args.args[0], 'Hello world\n\nline')
        await self.send('Text statistics')
        await self.send('a b')
        self.assertIn('Words: 2', self.message.reply_text.call_args.args[0])

    async def test_cases_and_validation(self):
        for style, expected in [('upper', 'HELLO WORLD'), ('lower', 'hello world'), ('title', 'Hello World')]:
            await self.send('Case converter')
            await self.send('bad choice')
            self.assertNotIn('style', self.context.user_data)
            await self.send(style)
            await self.send('hELLo wORLD')
            self.assertEqual(self.message.reply_text.call_args.args[0], expected)

    async def test_commands_and_cancel(self):
        self.message.text = '/clean@DREW_ACADEMY_BOT   a   b'
        await bot.feature(self.update, self.context)
        self.assertEqual(self.message.reply_text.call_args.args[0], 'a b')
        await bot.start(self.update, self.context)
        self.assertEqual(self.context.user_data, {})

    async def test_emoji_long_output_is_split(self):
        text = '😀' * 4096
        await bot.reply(self.message, text)
        parts = [call.args[0] for call in self.message.reply_text.call_args_list]
        self.assertEqual(''.join(parts), text)
        self.assertTrue(all(len(p.encode('utf-16-le')) // 2 <= 3500 for p in parts))

    async def test_empty_text(self):
        await self.send('   ')
        self.assertIn('non-space', self.message.reply_text.call_args.args[0])

    async def test_profile(self):
        self.assertLessEqual(len(bot.ABOUT), 120)
        self.assertLessEqual(len(bot.DESCRIPTION), 512)
        api = SimpleNamespace(get_me=AsyncMock(return_value=SimpleNamespace(username=bot.USERNAME)),
            set_my_name=AsyncMock(), set_my_short_description=AsyncMock(), set_my_description=AsyncMock(), set_my_commands=AsyncMock())
        await bot.setup(SimpleNamespace(bot=api))
        api.set_my_short_description.assert_awaited_once_with(bot.ABOUT)
        api.set_my_description.assert_awaited_once_with(bot.DESCRIPTION)
