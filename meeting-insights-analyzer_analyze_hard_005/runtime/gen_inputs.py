import os
import random
from datetime import datetime, timedelta

# Set seed for deterministic output
random.seed(42)

# Meeting participants
participants = ['Alex Chen', 'Sarah Johnson', 'Mike Rodriguez', 'Emma Davis', 'John Smith']
user_name = 'Alex Chen'  # The user we're analyzing

# Generate 8 meeting transcripts with various communication patterns
meetings = [
    {
        'filename': '2024-01-15_team_standup.txt',
        'title': 'Weekly Team Standup',
        'duration': '00:32:15',
        'participants': ['Alex Chen', 'Sarah Johnson', 'Mike Rodriguez', 'Emma Davis']
    },
    {
        'filename': '2024-01-22_project_review.txt', 
        'title': 'Q1 Project Review',
        'duration': '01:15:30',
        'participants': ['Alex Chen', 'Sarah Johnson', 'John Smith']
    },
    {
        'filename': '2024-02-05_client_call.txt',
        'title': 'Client Strategy Discussion',
        'duration': '00:45:22',
        'participants': ['Alex Chen', 'Mike Rodriguez', 'Emma Davis']
    },
    {
        'filename': '2024-02-12_one_on_one.txt',
        'title': '1:1 with Sarah',
        'duration': '00:28:45',
        'participants': ['Alex Chen', 'Sarah Johnson']
    },
    {
        'filename': '2024-02-26_budget_planning.txt',
        'title': 'Budget Planning Meeting',
        'duration': '01:02:18',
        'participants': ['Alex Chen', 'Sarah Johnson', 'Mike Rodriguez', 'Emma Davis', 'John Smith']
    },
    {
        'filename': '2024-03-05_performance_review.txt',
        'title': 'Team Performance Review',
        'duration': '00:38:12',
        'participants': ['Alex Chen', 'Emma Davis', 'John Smith']
    },
    {
        'filename': '2024-03-15_conflict_resolution.txt',
        'title': 'Project Conflict Discussion',
        'duration': '00:52:33',
        'participants': ['Alex Chen', 'Sarah Johnson', 'Mike Rodriguez']
    },
    {
        'filename': '2024-03-22_strategy_session.txt',
        'title': 'Q2 Strategy Planning',
        'duration': '01:25:44',
        'participants': ['Alex Chen', 'Sarah Johnson', 'Mike Rodriguez', 'Emma Davis', 'John Smith']
    }
]

# Conflict avoidance patterns for Alex
conflict_avoidance_examples = [
    "Alex Chen [00:14:32]: So, um, I was thinking... maybe we could, like, potentially consider looking at the timeline again? I mean, if you think that makes sense. But whatever you think is best!",
    "Alex Chen [00:23:15]: Well, you know, I kind of feel like there might be some, uh, room for improvement in the process. But I don't want to step on anyone's toes here.",
    "Alex Chen [00:18:45]: I guess we could possibly think about maybe restructuring this, but, um, I'm not really sure if that's the right approach. What do you all think?",
    "Alex Chen [00:31:22]: So this is just my opinion, but I sort of think we might want to consider a different approach. But I could be wrong about this.",
    "Alex Chen [00:25:18]: I don't want to be difficult here, but maybe we should think about whether this timeline is, you know, realistic? But if everyone else is okay with it, then I guess it's fine."
]

# Filler words to include
filler_words = ['um', 'uh', 'like', 'you know', 'actually', 'sort of', 'kind of']

# Active listening examples
active_listening_examples = [
    "Alex Chen [00:12:30]: That's a really good point, Sarah. When you mentioned the client feedback, are you thinking we should adjust our approach for the entire project or just this phase?",
    "Alex Chen [00:19:45]: Mike, I heard you say that the technical constraints are the main blocker. Can you help me understand what specific constraints we're facing?",
    "Alex Chen [00:08:22]: Emma, you raised an important concern about the budget. Let me make sure I understand - you're saying the current allocation won't cover the additional resources we need?"
]

def generate_meeting_content(meeting_info):
    content = f"Meeting: {meeting_info['title']}\n"
    content += f"Date: {meeting_info['filename'][:10]}\n"
    content += f"Duration: {meeting_info['duration']}\n"
    content += f"Participants: {', '.join(meeting_info['participants'])}\n\n"
    content += "--- TRANSCRIPT ---\n\n"
    
    # Add opening
    content += "Alex Chen [00:02:15]: Alright everyone, thanks for joining. Let's get started.\n\n"
    
    # Add conflict avoidance examples (vary by meeting)
    if 'conflict' in meeting_info['title'].lower() or 'performance' in meeting_info['title'].lower():
        content += random.choice(conflict_avoidance_examples) + "\n\n"
    elif random.random() < 0.6:  # 60% chance in other meetings
        content += random.choice(conflict_avoidance_examples) + "\n\n"
    
    # Add some regular conversation with Alex speaking patterns
    other_participants = [p for p in meeting_info['participants'] if p != 'Alex Chen']
    
    for i in range(random.randint(8, 15)):
        timestamp = f"{random.randint(0,1):02d}:{random.randint(3,55):02d}:{random.randint(10,59):02d}"
        
        if random.random() < 0.4:  # 40% Alex speaks
            # Add filler words to Alex's speech
            fillers = random.sample(filler_words, random.randint(1, 3))
            if random.random() < 0.7:
                speech = f"So, {fillers[0]}, I think we need to, {fillers[1] if len(fillers) > 1 else ''}, move forward with the plan. {fillers[2] if len(fillers) > 2 else ''}"
            else:
                speech = "I believe we're on the right track with this approach."
            content += f"Alex Chen [{timestamp}]: {speech}\n\n"
        else:
            speaker = random.choice(other_participants)
            content += f"{speaker} [{timestamp}]: I agree with that assessment. We should proceed as planned.\n\n"
    
    # Add active listening example
    if random.random() < 0.5:
        content += random.choice(active_listening_examples) + "\n\n"
    
    # Add interruption examples
    if random.random() < 0.4:
        other_speaker = random.choice(other_participants)
        content += f"{other_speaker} [00:{random.randint(20,50):02d}:15]: I think the main issue we're facing is—\n"
        content += f"Alex Chen [00:{random.randint(20,50):02d}:17]: Sorry to jump in, but I just wanted to add that we should also consider the budget implications.\n\n"
    
    # Calculate Alex's speaking ratio (should be high for analysis)
    alex_turns = content.count('Alex Chen [')
    total_turns = content.count('[00:') + content.count('[01:')
    content += f"\n--- MEETING STATS ---\n"
    content += f"Alex Chen speaking turns: {alex_turns}\n"
    content += f"Total speaking turns: {total_turns}\n"
    
    return content

# Generate all meeting files
for meeting in meetings:
    with open(meeting['filename'], 'w') as f:
        f.write(generate_meeting_content(meeting))

print("Generated 8 meeting transcript files with communication patterns for analysis.")