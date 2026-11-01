"""Original, offline learning material for DREW ACADEMY."""
LESSONS = {
    'Source checking': (
        'Before sharing information, check who published it, when it was published, and what evidence supports it. '
        'Open the original source instead of relying on a screenshot. Compare independent sources; several sites repeating one claim are not independent evidence. '
        'Practice: choose a claim and write down its author, date, and primary evidence.',
        ('Which is the best first step when checking a screenshot claim?', ['Share it quickly', 'Find the original source', 'Count its likes'], 1,
         'The original source provides context and evidence that a screenshot may omit.')),
    'Account security': (
        'Use a different strong password for every account and store passwords in a reputable password manager. '
        'Enable two-step verification where available. Never share login codes. Check the exact domain before signing in and review active sessions regularly. '
        'Practice: review the security settings on one account and close sessions you do not recognize.',
        ('Someone asks you for a login code. What should you do?', ['Keep the code private', 'Send half of it', 'Send it if they use a logo'], 0,
         'A login code can grant access to your account. A name or logo does not establish trust.')),
    'Clear writing': (
        'Start with your main point, then provide the detail the reader needs. Use concrete verbs and short paragraphs. '
        'Replace vague requests with a specific action and deadline when appropriate. Read your draft once for meaning and once for spelling. '
        'Practice: rewrite “Please handle the thing soon” as a specific request with enough context.',
        ('Which request is clearest?', ['Do the thing', 'Help soon', 'Please review the two-page draft by Tuesday'], 2,
         'It names the action, the item, and a deadline.')),
    'File organization': (
        'Group files by project, use descriptive names, and keep a consistent date format such as YYYY-MM-DD. '
        'Keep an independent backup of important files and test that you can restore it. Syncing alone may also sync accidental deletions. '
        'Practice: create a project folder and give three files meaningful, consistent names.',
        ('What confirms that a backup is useful?', ['It has a nice name', 'You successfully restore a file', 'It is in the same folder'], 1,
         'A restore test checks that your backup can actually recover the information.')),
    'Active learning': (
        'After reading a short section, close it and explain the main idea from memory. Check your explanation and correct any gaps. '
        'Review again on later days rather than rereading everything in one sitting. Use practice questions to discover what needs attention. '
        'Practice: write three questions about something you learned today, then answer them without notes.',
        ('Which activity practices retrieval?', ['Copying a paragraph', 'Highlighting every line', 'Explaining an idea without notes'], 2,
         'Retrieval means bringing information to mind instead of only looking at it again.')),
    'Task planning': (
        'Turn a broad goal into small actions that you can complete in one session. Choose one priority, estimate the time, and leave room for a break. '
        'At the end, record what you completed and choose the next action. Adjust the plan if the task takes longer than expected. '
        'Practice: replace “learn design” with a 20-minute action such as drawing three simple compositions.',
        ('Which is an actionable study task?', ['Be productive', 'Read two pages and summarize the main idea', 'Learn everything'], 1,
         'A bounded activity makes it easier to start and check completion.')),
}


def make_plan(topic: str, minutes: int, days: int) -> str:
    if topic not in LESSONS or minutes not in (15, 30, 45, 60) or not 1 <= days <= 7:
        raise ValueError('Choose a listed topic, 15/30/45/60 minutes, and 1–7 days.')
    reading = max(3, minutes // 3)
    practice = minutes - reading - 3
    tasks = [
        'Read the lesson and explain its main idea in your own words.',
        'Complete the lesson’s practical exercise with a new example.',
        'Take the topic quiz and explain why the other choices are weaker.',
        'Recall the key ideas without notes, then check your gaps.',
        'Apply the skill to an everyday task and write what happened.',
        'Teach the idea using a short example for a beginner.',
        'Repeat the exercise and compare it with your first attempt.',
    ]
    lines = [f'Your study plan: {topic}', f'{days} day(s), {minutes} minutes per day.',
             f'Each session: {reading} min review, {practice} min practice, 3 min reflection.']
    lines += [f'Day {i + 1}: {tasks[i]}' for i in range(days)]
    return '\n\n'.join(lines)
