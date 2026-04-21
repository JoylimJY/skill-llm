import os
import random
random.seed(42)

# Create meeting transcripts folder
os.makedirs('meetings', exist_ok=True)

# Generate 4 meeting transcript files with realistic content
transcripts = [
    {
        'filename': '2024-01-15_team_standup.txt',
        'content': '''Team Standup - January 15, 2024
Duration: 25 minutes

[00:01:30] Alex (You): Good morning everyone. So, um, let's get started with our standup.

[00:02:15] Sarah: I finished the user authentication module yesterday.

[00:02:45] Alex (You): That's great! Um, actually, I was kind of thinking... maybe we should, you know, potentially look at the testing coverage? I mean, if you think that makes sense.

[00:03:20] Sarah: Sure, what do you mean exactly?

[00:03:35] Alex (You): Well, it's just that... I guess I'm a little concerned about, um, the quality. But whatever you think is best!

[00:04:10] Mike: I can help with the testing if needed.

[00:04:25] Alex (You): Yeah, that would be... that would be good. So, um, Mike, what did you work on yesterday?

[00:05:00] Mike: I was debugging the payment integration. There's still an issue with the webhook validation.

[00:05:30] Alex (You): Oh, okay. Um, do you need any help with that? I mean, if you want.

[00:06:00] Mike: Actually, yes. The documentation is unclear and I'm stuck.

[00:06:15] Alex (You): Right, so... maybe we could, like, schedule some time to look at it together? If that works for you.

[00:07:30] Sarah: Alex, just to be direct - do you want me to add more tests before merging?

[00:07:45] Alex (You): Um, well... I think it would be good, but I don't want to, you know, slow you down or anything.

[00:08:10] Sarah: Just tell me yes or no.

[00:08:15] Alex (You): Yes, please add the tests.

[00:09:00] Alex (You): Alright, um, anything else we need to cover today?
'''
    },
    {
        'filename': '2024-01-22_project_review.txt', 
        'content': '''Project Review Meeting - January 22, 2024
Duration: 45 minutes
Attendees: Alex (You), Sarah, Mike, Lisa (PM)

[00:02:00] Lisa: Let's review the Q1 deliverables. Alex, can you walk us through the current status?

[00:02:30] Alex (You): Sure, so, um, we're making good progress. I think we're mostly on track, you know?

[00:03:00] Lisa: What does 'mostly' mean exactly?

[00:03:15] Alex (You): Well, there are a few things that are... kind of behind schedule. But nothing major, I think.

[00:03:45] Lisa: Which things specifically?

[00:04:00] Alex (You): Um, the API documentation is a bit delayed. And maybe the mobile app testing. But we can probably catch up.

[00:04:30] Sarah: Alex, the API docs are three weeks behind. That's pretty significant.

[00:04:45] Alex (You): Right, yeah... I guess it is more serious than I, um, initially thought.

[00:05:15] Lisa: What's causing the delay?

[00:05:30] Alex (You): Well, it's complicated. There are several factors... um, resource constraints and, you know, other priorities.

[00:06:00] Mike: I think we just haven't allocated enough time for documentation.

[00:06:15] Alex (You): Yeah, Mike's right. That's... that's basically it.

[00:07:30] Lisa: Alex, I need you to be more direct about project status. Can you commit to a new timeline?

[00:07:45] Alex (You): Um, I think so. Maybe by end of February? If that works for everyone.

[00:08:00] Lisa: That's not a commitment. Yes or no?

[00:08:15] Alex (You): Yes, we'll have the API docs done by February 28th.

[00:12:00] Alex (You): So, um, anything else we should discuss today? I mean, if there are other concerns...

[00:12:30] Sarah: The testing pipeline is also behind schedule.

[00:12:45] Alex (You): Oh right, I forgot about that. Um, how behind are we?

[00:13:00] Sarah: Two weeks.

[00:13:15] Alex (You): Okay, so... we should probably address that too. Maybe we can, like, reprioritize some things?
'''
    },
    {
        'filename': '2024-01-29_client_call.txt',
        'content': '''Client Call - January 29, 2024
Client: TechCorp
Duration: 30 minutes

[00:01:00] Client: We're concerned about the recent delays we've been hearing about.

[00:01:15] Alex (You): Oh, um, I wouldn't say they're major delays. Just some minor, you know, adjustments to the timeline.

[00:01:45] Client: Our stakeholders are asking for concrete dates. When will the API be ready?

[00:02:00] Alex (You): Well, that's a good question. Um, we're working really hard on it. I think we're looking at, maybe, early March? But I'd have to, you know, check with the team.

[00:02:30] Client: You think? I need a definitive answer.

[00:02:45] Alex (You): Right, of course. So, um, let me be more specific. We're targeting March 5th, but there might be some... flexibility needed depending on, you know, various factors.

[00:03:15] Client: What factors?

[00:03:30] Alex (You): Just, um, the usual development challenges. Nothing we can't handle, I'm sure.

[00:04:00] Client: Alex, I need you to be more transparent. Are there specific blockers?

[00:04:15] Alex (You): Well, if I'm being honest... yes, there are a few things. The documentation is behind, and we had some, um, unexpected complexity with the authentication system.

[00:05:00] Client: Why wasn't this communicated earlier?

[00:05:15] Alex (You): I guess I thought we could, you know, work through it without affecting the overall timeline. Maybe that wasn't the best approach.

[00:06:30] Client: Going forward, I need weekly status updates with clear timelines.

[00:06:45] Alex (You): Absolutely. That makes total sense. We'll, um, make sure to be more proactive about communication.
'''
    },
    {
        'filename': '2024-02-05_performance_review.txt',
        'content': '''Performance Review - February 5, 2024
Attendees: Alex (You), Manager (Jennifer)

[00:01:30] Jennifer: Let's talk about your leadership development this quarter.

[00:01:45] Alex (You): Sure, um, I think things have been going pretty well overall.

[00:02:00] Jennifer: I've gotten some feedback that you sometimes avoid difficult conversations. What's your perspective on that?

[00:02:15] Alex (You): Oh, um... I wouldn't say I avoid them. Maybe I just, you know, try to approach them carefully?

[00:02:45] Jennifer: Can you give me an example of a difficult conversation you've had recently?

[00:03:00] Alex (You): Well, there was the thing with Sarah about the testing... but that worked out fine in the end.

[00:03:15] Jennifer: Tell me about that conversation.

[00:03:30] Alex (You): I guess I initially suggested that maybe she could look at adding more tests, but she asked me to be more direct, so I was.

[00:04:00] Jennifer: What did you say initially?

[00:04:15] Alex (You): Um, I think I said something like 'maybe we could potentially look at the testing coverage if you think that makes sense'.

[00:04:30] Jennifer: And how could you have approached that differently?

[00:04:45] Alex (You): I suppose I could have just said 'Please add more tests before merging' from the beginning.

[00:05:00] Jennifer: Exactly. Your team needs clear direction. What's holding you back from being more direct?

[00:05:15] Alex (You): I guess I worry about, um, seeming too aggressive or micromanaging people.

[00:05:45] Jennifer: There's a difference between being direct and being aggressive. Being clear about expectations is actually helpful for your team.

[00:06:00] Alex (You): You're right. I think I need to work on that.

[00:07:00] Jennifer: What specific steps will you take?

[00:07:15] Alex (You): Um, maybe I can practice being more direct in my communication? And ask for feedback when I'm being too indirect?
'''
    }
]

# Write transcript files
for transcript in transcripts:
    with open(f'meetings/{transcript["filename"]}', 'w') as f:
        f.write(transcript['content'])

print('Generated 4 meeting transcript files in meetings/ folder')