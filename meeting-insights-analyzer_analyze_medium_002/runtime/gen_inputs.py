import os
import random
from datetime import datetime, timedelta

random.seed(42)

# Create meeting transcripts folder
os.makedirs('meetings', exist_ok=True)

# Generate 5 meeting transcripts with various communication patterns
transcripts = [
    {
        'filename': '2024-01-15-team-standup.txt',
        'content': '''Meeting: Team Standup
Date: 2024-01-15
Participants: Alex (You), Sarah, Mike, Jessica

00:02:15 Alex: Um, so maybe we could, like, potentially look at the sprint progress? I mean, if everyone thinks that's okay.
00:02:45 Sarah: Sure, I completed the user authentication feature.
00:03:10 Alex: That's great, Sarah. So, Mike, how are you doing with the API integration?
00:03:25 Mike: I'm running into some issues with the third-party service.
00:03:40 Alex: Oh, I see. Well, um, I guess we could... maybe discuss that later? You know, in a separate meeting?
00:04:15 Jessica: I think we should address it now since it's blocking my work.
00:04:25 Alex: Right, right. Actually, you make a good point, Jessica. Mike, can you walk us through the specific issues?
00:05:30 Mike: The API keeps timing out when we try to fetch user data.
00:05:45 Alex: Okay, so what I'm hearing is that the timeout issue is the main blocker. Have you tried increasing the timeout values?
00:06:00 Mike: No, I haven't tried that yet.
00:06:10 Alex: That might be worth exploring. Sarah, since you worked on authentication, do you have any insights on this?
'''
    },
    {
        'filename': '2024-01-22-project-review.txt', 
        'content': '''Meeting: Project Review
Date: 2024-01-22
Participants: Alex (You), David, Lisa, Tom

00:01:30 Alex: Thanks everyone for joining. Let's dive into the project status.
00:02:00 David: The backend is 80% complete, but we're facing some performance issues.
00:02:15 Alex: Can you elaborate on those performance issues, David?
00:02:45 David: The database queries are taking too long, especially for large datasets.
00:03:00 Alex: I see. Lisa, how does this impact the frontend timeline?
00:03:20 Lisa: It definitely creates some uncertainty. I can't finalize the data loading components until we resolve this.
00:03:35 Alex: That's a valid concern. Tom, from a QA perspective, what are your thoughts?
00:04:10 Tom: We should probably delay the testing phase until the performance issues are fixed.
00:04:25 Alex: You know what, maybe we should... I mean, could we possibly consider pushing the deadline back a bit? I don't want to, like, put pressure on anyone.
00:05:00 David: I think a one-week extension would give us enough buffer.
00:05:15 Alex: Um, okay. I suppose that could work. But, you know, I should probably check with stakeholders first.
'''
    },
    {
        'filename': '2024-01-29-client-call.txt',
        'content': '''Meeting: Client Strategy Call
Date: 2024-01-29
Participants: Alex (You), Client-Emma, Client-Robert

00:01:00 Alex: Good morning Emma and Robert. I wanted to discuss the project timeline with you.
00:01:15 Emma: We're looking forward to hearing about the progress.
00:01:30 Alex: So, actually, there have been some, um, challenges that we've encountered.
00:01:45 Robert: What kind of challenges?
00:02:00 Alex: Well, you know, the API integration has been more complex than we initially thought. And, like, the performance requirements are quite demanding.
00:02:30 Emma: Are you saying there will be delays?
00:02:45 Alex: I mean, potentially, yes. But, um, we're working really hard to minimize any impact.
00:03:15 Robert: How much of a delay are we talking about?
00:03:30 Alex: Maybe a week? Possibly two? It's hard to say exactly right now.
00:03:50 Emma: This is concerning. We have commitments to our customers.
00:04:05 Alex: I totally understand your concern, Emma. What I'm hearing is that the timeline is critical for your customer commitments. Let me ask this - what would be the minimum viable features we could deliver on the original timeline?
00:04:45 Robert: We need at least the core user management and basic reporting.
00:05:00 Alex: That's helpful. So if we focus on those core features first, we could potentially meet your timeline while moving the advanced features to a second phase. Does that approach work for you?
'''
    },
    {
        'filename': '2024-02-05-feedback-session.txt',
        'content': '''Meeting: Performance Feedback Session
Date: 2024-02-05
Participants: Alex (You), Manager-Karen

00:01:00 Karen: I wanted to discuss some feedback about your recent project management.
00:01:15 Alex: Sure, I'm always open to feedback.
00:01:30 Karen: I've noticed that in several meetings, there seems to be some hesitation when addressing project issues directly.
00:01:50 Alex: Oh, um, yeah. I guess I try to be, like, diplomatic about things?
00:02:10 Karen: I appreciate diplomacy, but sometimes direct communication is more effective.
00:02:25 Alex: Right, right. Actually, I've been thinking about that too. Could you give me a specific example?
00:02:45 Karen: In last week's client call, when you mentioned the delays, it took several minutes to get to the actual timeline impact.
00:03:00 Alex: That's a fair point. I was trying not to alarm them, but I can see how that might have created more uncertainty.
00:03:20 Karen: Exactly. Clients appreciate honesty and clear timelines, even when the news isn't great.
00:03:35 Alex: So what I'm understanding is that you'd like me to be more direct and specific when communicating project status, even when there are challenges. Is that accurate?
00:03:55 Karen: Yes, that's exactly right. And I've also noticed you ask good follow-up questions, which is a strength.
'''
    },
    {
        'filename': '2024-02-12-team-retrospective.txt',
        'content': '''Meeting: Sprint Retrospective
Date: 2024-02-12
Participants: Alex (You), Sarah, Mike, Jessica, Tom

00:01:00 Alex: Let's start our retrospective. What went well this sprint?
00:01:15 Sarah: The authentication feature was completed on time.
00:01:30 Mike: The API performance issues were resolved faster than expected.
00:01:45 Alex: Great points. Jessica, what's your perspective on what went well?
00:02:00 Jessica: I felt like communication improved compared to last sprint.
00:02:15 Alex: That's encouraging to hear. Tom, anything to add?
00:02:30 Tom: The testing process was smoother with the earlier bug fixes.
00:02:45 Alex: Excellent. Now, what could we improve? And I want everyone to be honest here.
00:03:00 Sarah: Sometimes decisions took longer than necessary.
00:03:15 Alex: Can you give me an example of that, Sarah?
00:03:35 Sarah: The database optimization decision. We spent three meetings discussing it before moving forward.
00:03:50 Alex: You're right. I was trying to get everyone's input, but I think I over-consulted on that one.
00:04:10 Mike: I actually appreciated being consulted, but maybe we could set time limits for decisions?
00:04:25 Alex: That's a good suggestion, Mike. So what I'm hearing is that you value being included in decisions, but we need to be more efficient about reaching conclusions. Jessica, what's your take?
00:04:50 Jessica: I agree. Maybe we could use a decision-making framework?
00:05:05 Alex: That's a thoughtful suggestion. What kind of framework were you thinking?
'''
    }
]

# Write transcript files
for transcript in transcripts:
    with open(f"meetings/{transcript['filename']}", 'w') as f:
        f.write(transcript['content'])

print('Generated 5 meeting transcripts with communication patterns')