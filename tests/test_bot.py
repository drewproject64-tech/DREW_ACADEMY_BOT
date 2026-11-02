import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
import bot
from telegram.error import NetworkError, BadRequest
from content import LESSONS, make_plan

class ContentTests(unittest.TestCase):
    def test_all_plans_and_profile_limits(self):
        self.assertLessEqual(len(bot.ABOUT), 120)
        self.assertLessEqual(len(bot.DESCRIPTION), 512)
        for topic in LESSONS:
            for minutes in (15, 30, 45, 60):
                for days in range(1, 8):
                    plan = make_plan(topic, minutes, days)
                    self.assertIn(f'Day {days}:', plan)
                    self.assertNotIn(f'Day {days + 1}:', plan)
                    self.assertLess(len(plan), 4096)
        for args in [('invalid', 15, 1), (bot.TOPICS[0], 0, 1), (bot.TOPICS[0], 15, 8)]:
            with self.assertRaises(ValueError):
                make_plan(*args)

class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.message = SimpleNamespace(reply_text=AsyncMock())
        self.context = SimpleNamespace(user_data={})

    async def click(self, data):
        query = SimpleNamespace(data=data, message=self.message, answer=AsyncMock(), edit_message_reply_markup=AsyncMock())
        await bot.callback(SimpleNamespace(callback_query=query), self.context)

    async def test_quiz_score_and_stale_answers(self):
        await self.click('quiz')
        stale = None
        for index in range(5):
            state = self.context.user_data['quiz']
            correct = LESSONS[state['items'][index]][1][2]
            answer = f"answer:{state['nonce']}:{index}:{correct}"
            await self.click(answer)
            if index == 0:
                stale = answer
                await self.click(stale)
                self.assertEqual(self.context.user_data['quiz']['score'], 1)
                self.assertEqual(self.context.user_data['quiz']['position'], 1)
        self.assertEqual(self.context.user_data, {})
        self.assertIn('5/5', self.message.reply_text.call_args.args[0])
        await self.click(stale)
        self.assertIn('no longer active', self.message.reply_text.call_args.args[0])

    async def test_acknowledgement_failure_does_not_break_lesson(self):
        for error in (NetworkError('connection interrupted'), BadRequest('query is too old')):
            query = SimpleNamespace(data='lesson:0', message=self.message,
                answer=AsyncMock(side_effect=error), edit_message_reply_markup=AsyncMock())
            await bot.callback(SimpleNamespace(callback_query=query), self.context)
            self.assertIn(LESSONS[bot.TOPICS[0]][0], self.message.reply_text.call_args.args[0])

    async def test_failed_keyboard_edit_still_delivers_quiz_feedback(self):
        await self.click('quiz')
        state = self.context.user_data['quiz']
        correct = LESSONS[state['items'][0]][1][2]
        query = SimpleNamespace(data=f"answer:{state['nonce']}:0:{correct}", message=self.message,
            answer=AsyncMock(), edit_message_reply_markup=AsyncMock(side_effect=NetworkError('offline')))
        await bot.callback(SimpleNamespace(callback_query=query), self.context)
        self.assertEqual(state['score'], 1)
        self.assertEqual(state['position'], 1)
        self.assertIn('Question 2/5', self.message.reply_text.call_args.args[0])
        self.assertTrue(any('Correct.' in call.args[0] for call in self.message.reply_text.call_args_list))

    async def test_planner_and_interrupted_flow(self):
        await self.click('plan:0')
        await self.click('minutes:30')
        await self.click('days:7')
        self.assertIn('Day 7:', self.message.reply_text.call_args.args[0])
        self.assertEqual(self.context.user_data, {})
        await self.click('minutes:30')
        self.assertIn('new plan', self.message.reply_text.call_args.args[0])
        await self.click('plan:1')
        await self.click('menu')
        self.assertEqual(self.context.user_data, {})

    async def test_all_lessons(self):
        for i, topic in enumerate(bot.TOPICS):
            await self.click(f'lesson:{i}')
            self.assertIn(LESSONS[topic][0], self.message.reply_text.call_args.args[0])

    async def test_profile_setup_and_wrong_token_guard(self):
        api = SimpleNamespace(get_me=AsyncMock(return_value=SimpleNamespace(username=bot.USERNAME)),
            set_my_name=AsyncMock(), set_my_short_description=AsyncMock(),
            set_my_description=AsyncMock(), set_my_commands=AsyncMock())
        await bot.setup(SimpleNamespace(bot=api))
        api.set_my_short_description.assert_awaited_once_with(bot.ABOUT)
        api.set_my_description.assert_awaited_once_with(bot.DESCRIPTION)
        api.get_me.return_value = SimpleNamespace(username='other_bot')
        with self.assertRaises(RuntimeError):
            await bot.setup(SimpleNamespace(bot=api))
        self.assertEqual(api.set_my_name.await_count, 1)

if __name__ == '__main__':
    unittest.main()
