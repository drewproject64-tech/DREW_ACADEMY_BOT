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

    def profile_api(self, matching=True):
        return SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(username=bot.USERNAME)),
            get_my_name=AsyncMock(return_value=SimpleNamespace(name=bot.NAME if matching else 'Old name')),
            get_my_short_description=AsyncMock(return_value=SimpleNamespace(short_description=bot.ABOUT if matching else 'Old about')),
            get_my_description=AsyncMock(return_value=SimpleNamespace(description=bot.DESCRIPTION if matching else 'Old description')),
            get_my_commands=AsyncMock(return_value=bot.command_list() if matching else []),
            set_my_name=AsyncMock(), set_my_short_description=AsyncMock(),
            set_my_description=AsyncMock(), set_my_commands=AsyncMock())

    async def test_unchanged_profile_never_writes(self):
        self.assertLessEqual(len(bot.ABOUT), 120)
        self.assertLessEqual(len(bot.DESCRIPTION), 512)
        api = self.profile_api()
        await bot.setup(SimpleNamespace(bot=api))
        for name in ('set_my_name', 'set_my_short_description', 'set_my_description', 'set_my_commands'):
            getattr(api, name).assert_not_awaited()

    async def test_changed_profile_applies_about_and_description(self):
        api = self.profile_api(False)
        await bot.setup(SimpleNamespace(bot=api))
        self.assertEqual(api.set_my_short_description.call_args.args[0], bot.ABOUT)
        self.assertEqual(api.set_my_description.call_args.args[0], bot.DESCRIPTION)
        self.assertEqual(api.set_my_commands.call_args.args[0], bot.command_list())

    async def test_rate_limited_profile_does_not_abort_startup(self):
        from telegram.error import RetryAfter
        from datetime import timedelta
        for cooldown in (8217, timedelta(seconds=8217)):
            for method in ('get_my_name', 'set_my_name', 'get_my_short_description',
                           'set_my_short_description', 'get_my_description', 'set_my_description',
                           'get_my_commands', 'set_my_commands'):
                api = self.profile_api(False)
                getattr(api, method).side_effect = RetryAfter(cooldown)
                await bot.setup(SimpleNamespace(bot=api))
                self.assertEqual(getattr(api, method).await_count, 1)

    async def test_network_error_does_not_abort_profile_setup(self):
        from telegram.error import NetworkError
        api = self.profile_api(False)
        api.set_my_name.side_effect = NetworkError('connection failed')
        await bot.setup(SimpleNamespace(bot=api))
        api.set_my_name.assert_awaited_once()

    async def test_wrong_bot_still_refused(self):
        api = self.profile_api()
        api.get_me.return_value = SimpleNamespace(username='other_bot')
        with self.assertRaises(RuntimeError):
            await bot.setup(SimpleNamespace(bot=api))
        api.get_my_name.assert_not_awaited()
