import os
import random

# Set deterministic seed
random.seed(42)

# Create meeting transcript 1 - Team Meeting
with open('2024-01-15-team-meeting.txt', 'w') as f:
    f.write('''Team Meeting - January 15, 2024
Participants: Sarah, Mike, Alex, You

[00:02:30] Sarah: Let's start with the project updates
[00:02:45] You: Um, well, I think, uh, maybe we should like, look at the timeline again? I mean, if that's okay with everyone
[00:03:15] Mike: What specifically concerns you about the timeline?
[00:03:20] You: Well, you know, it's just... maybe we're being a bit, um, optimistic? But whatever you all think is best
[00:04:10] Sarah: I think we can make it work if we focus
[00:04:15] You: Yeah, totally. That sounds good
[00:05:30] Alex: I'm worried about the backend integration
[00:05:35] You: Mm-hmm, yeah, I see what you mean. That's, uh, definitely something to think about
[00:06:45] You: So, um, should we maybe just keep going with the original plan then? I mean, if everyone's comfortable
[00:15:20] Sarah: I need more resources for my part
[00:15:25] You: Oh, okay. Um, what kind of resources are you thinking? Like, you know, maybe we could sort of figure something out?
[00:18:45] You: Actually, I think we should probably, um, wrap up soon. Does that work for everyone?
[00:19:00] Mike: Sure, sounds good
''')

# Create meeting transcript 2 - Client Call
with open('2024-01-22-client-call.txt', 'w') as f:
    f.write('''Client Call - January 22, 2024
Participants: Client (Jessica), You, Tom

[00:01:15] Jessica: We need to discuss the delivery date
[00:01:20] You: Right, so, um, about that... I was thinking maybe we could, like, potentially look at adjusting things a little bit? If that makes sense
[00:02:30] Jessica: Are you saying you can't meet the deadline?
[00:02:35] You: Well, it's not that we can't, it's just... you know, there might be some, uh, challenges. But I mean, we'll definitely try our best
[00:03:45] Tom: The technical requirements are more complex than expected
[00:03:50] You: Yeah, exactly what Tom said. It's just, um, more complicated than we thought initially
[00:05:15] Jessica: I need a clear answer - can you deliver on time or not?
[00:05:20] You: Well, um, that's a good question. I think, maybe, if we kind of adjust some things... but I don't want to promise something we can't, you know, deliver on
[00:08:30] You: So, uh, what do you think would work best for you? I mean, we're pretty flexible
[00:12:45] Jessica: I need this delivered by February 15th at the latest
[00:12:50] You: Okay, um, let me check with the team and, like, see what we can do. I'll get back to you soon
''')

# Create meeting transcript 3 - One-on-One
with open('2024-02-05-sarah-1on1.txt', 'w') as f:
    f.write('''One-on-One with Sarah - February 5, 2024
Participants: You, Sarah

[00:01:00] You: How are things going with your tasks?
[00:01:05] Sarah: Pretty well, making good progress
[00:02:15] You: That's great. Um, I wanted to maybe touch on the code review process? Like, if that's something we could, you know, improve
[00:03:20] Sarah: What do you mean exactly?
[00:03:25] You: Well, it's just... sometimes the reviews take a while, and I was thinking maybe we could sort of streamline things? But I don't want to add pressure or anything
[00:04:45] Sarah: I try to get to them as quickly as I can
[00:04:50] You: Oh absolutely, you do great work. I just thought, you know, maybe there's room for improvement? But whatever works for you
[00:06:30] You: Actually, let's just keep things as they are. It's working fine
[00:08:15] Sarah: Is there anything specific you need me to change?
[00:08:20] You: No, no, not really. I mean, maybe just, um, when you get a chance, if you could kind of prioritize the reviews a bit more? But only if it works with your schedule
[00:10:45] You: So, uh, anything else you wanted to discuss?
''')

print('Generated 3 meeting transcript files with communication patterns')