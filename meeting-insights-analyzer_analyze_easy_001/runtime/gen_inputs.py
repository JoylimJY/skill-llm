import os
import random
from datetime import datetime, timedelta

random.seed(42)

# Generate 3 meeting transcript files with conflict avoidance patterns
transcripts = [
    {
        'filename': '2024-01-15_team_meeting.txt',
        'content': '''Meeting: Weekly Team Sync
Date: 2024-01-15
Duration: 45 minutes

[00:05:12] John: So the project timeline... I was thinking maybe we could potentially look at adjusting it? I mean, if that makes sense to everyone.
[00:05:45] Sarah: What specifically are you concerned about?
[00:06:02] John: Well, you know, it's just that... I think there might be some challenges ahead.
[00:12:30] Mike: The budget is over by 20%.
[00:12:45] John: Yeah, I mean, that's... that's definitely something we should probably think about at some point.
[00:15:20] John: So, um, regarding the quality issues... I guess we could maybe consider looking into that when we have time?
[00:20:15] Sarah: John, are you saying we need to address this now?
[00:20:22] John: Well, I mean, whatever you all think is best. I don't want to step on anyone's toes.
[00:25:10] John: The client feedback was... interesting. Sort of mixed, you could say.
[00:30:05] John: Maybe we should circle back on this later? I think we're all pretty busy right now.'''
    },
    {
        'filename': '2024-01-22_one_on_one_sarah.txt',
        'content': '''Meeting: 1:1 with Sarah
Date: 2024-01-22
Duration: 30 minutes

[00:03:15] John: So, how are things going with the Anderson project?
[00:03:22] Sarah: Pretty good, making progress.
[00:03:30] John: That's great! I was just... you know, some people have been asking about the timeline.
[00:04:45] John: I mean, I think you're doing great work. It's just that, um, maybe we could potentially speed things up a little? But only if you think that's doable.
[00:08:20] Sarah: Are you saying I'm behind schedule?
[00:08:25] John: Oh no, no! I wouldn't say that exactly. It's more like... well, you know how clients can be.
[00:12:10] John: The deliverable quality has been... well, it's been fine. I just wonder if we could maybe enhance it somehow?
[00:15:30] John: I don't want to micromanage or anything. You know what you're doing. I was just thinking out loud.
[00:18:45] John: So anyway, let me know if you need anything. No pressure at all.'''
    },
    {
        'filename': '2024-01-29_client_call.txt', 
        'content': '''Meeting: Client Check-in Call
Date: 2024-01-29
Duration: 60 minutes

[00:10:20] Client: We're not happy with the current progress.
[00:10:35] John: I understand completely. We're definitely looking into ways to improve things.
[00:15:45] Client: The last deliverable was not what we expected.
[00:15:52] John: Right, well, you know, these things can be subjective sometimes. But we hear you.
[00:20:10] John: Maybe we could schedule another call to dive deeper into your concerns? When everyone has more time to prepare?
[00:25:30] Client: We need concrete answers today.
[00:25:38] John: Of course, that makes sense. Let me just... well, I think the team has been working really hard on this.
[00:30:15] John: I guess we could potentially make some adjustments to the approach? If that would help?
[00:35:20] John: I don't want to promise anything I can't deliver, but we'll definitely look into your feedback.
[00:40:10] Client: Are you going to fix this or not?
[00:40:15] John: We're absolutely committed to finding a solution that works for everyone.'''
    }
]

for transcript in transcripts:
    with open(transcript['filename'], 'w') as f:
        f.write(transcript['content'])