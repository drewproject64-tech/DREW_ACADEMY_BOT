import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from telegram.error import NetworkError
import bot

class ContentTests(unittest.TestCase):
    def test_plan_validation_and_totals(self):
        for minutes in (10, 30, 180):
            for days in (1, 5, 7):
                self.assertIn(f'Total study time: {minutes * days}', bot.study_plan(f'{minutes} {days}'))
        for text in ('', '30', '30.5 5', '-10 5', '30 0', '181 7', '30 8', '9'*5000+' 5', '٣٠ ٥'):
            with self.assertRaises(ValueError):
                bot.study_plan(text)

    def test_three_buttons_and_profile(self):
        self.assertEqual([b.text for row in bot.KEYBOARD.keyboard for b in row],
                         ['Lessons', 'Practice quiz', 'Study planner'])
        self.assertLessEqual(len(bot.ABOUT), 120)
        self.assertLessEqual(len(bot.DESCRIPTION), 512)

class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.message = SimpleNamespace(text='', reply_text=AsyncMock())
        self.update = SimpleNamespace(effective_message=self.message)
        self.context = SimpleNamespace(user_data={})

    async def send(self, text):
        self.message.text = text
        await bot.text_message(self.update, self.context)

    async def test_all_three_features_and_switching(self):
        await self.send('Lessons')
        self.assertIn('Practice:', self.message.reply_text.call_args.args[0])
        await self.send('Practice quiz')
        await self.send('Study planner')
        self.assertNotIn('quiz', self.context.user_data)
        await self.send('30 5')
        self.assertIn('150 minutes', self.message.reply_text.call_args.args[0])
        self.assertEqual(self.context.user_data, {})

    async def test_quiz_wrong_right_invalid_and_replay(self):
        for right in (True, False):
            await self.send('Practice quiz')
            correct = self.context.user_data['quiz'][0]
            await self.send('invalid')
            self.assertIn('quiz', self.context.user_data)
            await self.send('ABC'[correct if right else (correct + 1) % 3])
            self.assertIn('Correct.' if right else 'Keep practicing.', self.message.reply_text.call_args.args[0])
            self.assertEqual(self.context.user_data, {})
        await self.send('A')
        self.assertIn('Choose Lessons', self.message.reply_text.call_args.args[0])

    async def test_planner_invalid_then_correct_and_cancel(self):
        await self.send('Study planner')
        await self.send('0 0')
        self.assertTrue(self.context.user_data['planner'])
        await self.send('10 1')
        self.assertIn('Your study plan', self.message.reply_text.call_args.args[0])
        await self.send('Practice quiz')
        await bot.start(self.update, self.context)
        self.assertEqual(self.context.user_data, {})

    async def test_failed_question_delivery_keeps_no_pending_quiz(self):
        self.message.reply_text.side_effect = NetworkError('offline')
        with self.assertRaises(NetworkError):
            await self.send('Practice quiz')
        self.assertNotIn('quiz', self.context.user_data)

    async def test_legacy_buttons_recover(self):
        self.update.callback_query = SimpleNamespace(answer=AsyncMock(side_effect=NetworkError('offline')))
        await bot.legacy_button(self.update, self.context)
        self.assertIn('Welcome', self.message.reply_text.call_args.args[0])

    async def test_profile_setup_and_token_guard(self):
        api = SimpleNamespace(get_me=AsyncMock(return_value=SimpleNamespace(username=bot.USERNAME)),
            set_my_name=AsyncMock(), set_my_short_description=AsyncMock(),
            set_my_description=AsyncMock(), set_my_commands=AsyncMock())
        await bot.setup(SimpleNamespace(bot=api))
        api.set_my_short_description.assert_awaited_once_with(bot.ABOUT)
        api.set_my_description.assert_awaited_once_with(bot.DESCRIPTION)
        api.get_me.return_value = SimpleNamespace(username='wrong_bot')
        with self.assertRaises(RuntimeError):
            await bot.setup(SimpleNamespace(bot=api))
        self.assertEqual(api.set_my_name.await_count, 1)

if __name__ == '__main__':
    unittest.main()
