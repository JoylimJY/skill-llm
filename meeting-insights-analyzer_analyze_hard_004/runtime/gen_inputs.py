import os
import random
from datetime import datetime, timedelta

# Set deterministic seed
random.seed(42)

# Generate realistic meeting transcripts with known patterns
transcripts = [
    {
        'filename': '2024-01-15_Q1_Planning_Team_Meeting.txt',
        'content': '''Meeting: Q1 Planning Session
Date: January 15, 2024
Participants: Alex Chen (User), Sarah Martinez, David Kim, Lisa Wong

00:02:15 Alex Chen: So, um, thanks everyone for joining. I thought we could, you know, maybe talk about the Q1 objectives? If that makes sense to everyone.

00:02:45 Sarah Martinez: Absolutely! I've prepared the budget analysis you requested.

00:03:10 Alex Chen: Great! So Sarah, I was thinking... maybe we could look at the timeline? I mean, it seems like there might be some, uh, challenges with the current schedule. But I don't know, what do you think?

00:04:20 Sarah Martinez: Well, the timeline is aggressive, but I think we can manage it if we prioritize the core features.

00:04:35 Alex Chen: Right, right. That sounds good. Um, David, you've been quiet. Any thoughts on this?

00:05:00 David Kim: I have concerns about the technical feasibility of the timeline, especially with the new API integration.

00:05:15 Alex Chen: Oh, interesting. Well, I guess we should probably consider that. Maybe we could, like, adjust things somehow? I mean, whatever works best for the team.

00:06:30 Lisa Wong: I think we need to be more decisive here. The client is expecting a firm commitment.

00:06:45 Alex Chen: You're absolutely right, Lisa. So, um, how about we take a step back and really dive into the specifics? David, can you walk us through the technical constraints?

00:12:30 David Kim: [Explains technical details for 3 minutes]

00:15:45 Alex Chen: Thanks David. That's really helpful. So it sounds like we need to, you know, maybe reconsider our approach. Sarah, what are your thoughts on potentially adjusting the scope?

00:16:00 Sarah Martinez: We could reduce the feature set for the initial release.

00:16:10 Alex Chen: That makes sense. Lisa, would that work from a client perspective?

00:16:20 Lisa Wong: It's not ideal, but we can present it as a phased approach.

00:16:30 Alex Chen: Perfect. So I think we're aligned then? Great meeting everyone. I'll send out action items later.
'''
    },
    {
        'filename': '2024-02-20_Q1_Review_Meeting.txt', 
        'content': '''Meeting: Q1 Mid-Quarter Review
Date: February 20, 2024
Participants: Alex Chen (User), Sarah Martinez, David Kim, Lisa Wong, Marcus Johnson

00:01:30 Alex Chen: Alright everyone, let's get started. Um, so we're here to review our Q1 progress. I think things are going pretty well overall, but, you know, there might be some areas we could improve.

00:02:00 Sarah Martinez: The budget is tracking well, but we're seeing some cost overruns in the development phase.

00:02:15 Alex Chen: Oh, that's... well, that's something we should probably look into. David, any thoughts on why that might be happening?

00:02:30 David Kim: The API integration has been more complex than anticipated. We've had to bring in additional resources.

00:02:45 Alex Chen: I see. So, um, Marcus, from a project management perspective, what do you think we should do?

00:03:00 Marcus Johnson: We need to make some tough decisions about scope. We can't continue at this burn rate.

00:03:15 Alex Chen: Right, absolutely. That makes sense. So, like, how do we want to handle this? I mean, I don't want to make any decisions that the team isn't comfortable with.

00:04:30 Lisa Wong: Alex, the client is expecting deliverables next week. We need to decide now.

00:04:45 Alex Chen: You're right, Lisa. Okay, so what if we... maybe we could focus on the core features first? Would that work for everyone?

00:05:00 Sarah Martinez: That's exactly what I was going to suggest.

00:05:10 Alex Chen: Great minds think alike! So we're all good with that approach then?

00:08:45 Alex Chen: David, can you help us understand what paraphrasing what you said earlier, the technical constraints are really around the API complexity, right?

00:09:00 David Kim: Exactly, and the third-party dependencies are causing delays.

00:09:15 Alex Chen: That's a great point. So building on what David just shared, maybe we should consider alternative solutions?

00:15:20 Alex Chen: I think we've covered the main issues. Any final thoughts before we wrap up?

00:15:40 Marcus Johnson: Just want to confirm - we're definitely cutting features X and Y from this sprint?

00:15:50 Alex Chen: Yes, that's the decision. Thanks everyone for a productive discussion.
'''
    },
    {
        'filename': '2024-03-25_Q1_Retrospective.txt',
        'content': '''Meeting: Q1 Retrospective
Date: March 25, 2024
Participants: Alex Chen (User), Sarah Martinez, David Kim, Lisa Wong, Marcus Johnson, Jennifer Taylor

00:01:00 Alex Chen: Thanks everyone for making time for our Q1 retrospective. I want to create a safe space where we can honestly discuss what went well and what we can improve.

00:01:30 Jennifer Taylor: I appreciate that approach, Alex. I think transparency will help us grow as a team.

00:02:00 Alex Chen: Absolutely, Jennifer. So let's start with wins. Sarah, what went well from your perspective?

00:02:15 Sarah Martinez: The budget management was solid once we made the scope adjustments.

00:02:25 Alex Chen: That's fantastic. And David, how did the technical delivery go after we addressed the API challenges?

00:02:40 David Kim: Much better. The reduced scope allowed us to focus on quality.

00:02:55 Alex Chen: Excellent. Now for areas of improvement - and I want everyone to be candid. Lisa, what could we have done better?

00:03:10 Lisa Wong: Honestly, Alex, there were times when decisions took too long. The client expressed frustration about our responsiveness.

00:03:30 Alex Chen: That's really valuable feedback, Lisa. You're absolutely right - I need to be more decisive in critical moments. Can you give me a specific example?

00:03:50 Lisa Wong: The scope reduction discussion dragged on for two weeks when we could have decided in the first meeting.

00:04:05 Alex Chen: Point taken. I was trying to ensure everyone felt heard, but I realize that delayed important decisions. What would have been more effective?

00:04:20 Lisa Wong: Maybe set a decision deadline upfront and stick to it.

00:04:30 Alex Chen: That's actionable advice. I'll implement that going forward. Marcus, any other process improvements?

00:05:00 Marcus Johnson: Communication could be clearer. Sometimes action items weren't specific enough.

00:05:15 Alex Chen: Can you elaborate on that? I want to understand exactly what wasn't working.

00:05:30 Marcus Johnson: For example, "look into the timeline" is vague compared to "provide three timeline options by Friday."

00:05:45 Alex Chen: Perfect example. I'll be more specific with assignments and deadlines. Jennifer, what's your take as our newest team member?

00:06:10 Jennifer Taylor: Overall positive experience, but I noticed some team members were quieter in meetings.

00:06:25 Alex Chen: Good observation. David, I realize you often have valuable insights but don't always speak up. How can I better facilitate your participation?

00:06:40 David Kim: Maybe direct questions help. Sometimes I'm processing while others are talking.

00:06:55 Alex Chen: Noted. I'll make sure to specifically ask for your input, especially on technical matters. Any other thoughts on team dynamics?

00:10:30 Alex Chen: This has been incredibly helpful. Let me summarize our key improvements: faster decision-making, clearer action items, and better inclusion of all voices. Are we aligned on these priorities?

00:10:50 Sarah Martinez: Yes, and I think the team communication has actually improved a lot since January.

00:11:00 Alex Chen: Thanks, Sarah. That's encouraging to hear. Alright, let's commit to these changes for Q2.
'''
    }
]

# Create transcript files
for transcript in transcripts:
    with open(transcript['filename'], 'w', encoding='utf-8') as f:
        f.write(transcript['content'])

print(f"Generated {len(transcripts)} meeting transcript files")