import os
import random
from pathlib import Path

random.seed(42)

base = Path("/home/user")

# Create distractor directories mimicking a real home environment
distractor_dirs = [
    "documents/work/projects/2024",
    "documents/work/invoices",
    "documents/personal/taxes",
    "notes/ideas",
    "notes/journal/2024",
    "contacts/professional",
    "contacts/networking",
    "calendar/events",
    "downloads/misc",
    "pictures/travel/berlin",
]
for d in distractor_dirs:
    (base / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "documents/work/projects/2024/q3-brief.txt": "Q3 creative brief for client X. Deadline: Sept 30.",
    "documents/work/invoices/inv-0042.txt": "Invoice #42, client: Horizon Media, amount: $3200",
    "documents/personal/taxes/2023-summary.txt": "Gross income: $87,000. Deductions: $12,400.",
    "notes/ideas/campaign-concepts.txt": "Neon retro aesthetic. Think 80s but digital.",
    "notes/journal/2024/jan.txt": "Busy month. Lots of travel. Berlin was cold.",
    "contacts/professional/linkedin-exports.csv": "name,company,email\nSarah Chen,Apex Studio,sc@apex.com\nTom Blake,Freelance,tb@mail.com",
    "contacts/networking/conf-2023.txt": "Met 12 people at DesignWeek. Mostly surface level.",
    "calendar/events/upcoming.txt": "2024-09-20: Dinner with Marta\n2024-09-25: Carlos coffee",
    "downloads/misc/font-pack-readme.txt": "Contains 14 variable fonts. License: OFL.",
    "pictures/travel/berlin/notes.txt": "Visited Mitte and Prenzlauer Berg. Great coffee scene.",
    "notes/ideas/book-list.txt": "To read: 'The Design of Everyday Things', 'Thinking Fast and Slow'",
    "documents/work/projects/2024/client-feedback.txt": "Client loves the direction. Needs minor copy adjustments.",
}
for rel_path, content in distractor_files.items():
    fpath = base / rel_path
    fpath.write_text(content)

# THE CORE PROBLEM: Raw, messy, unstructured friend notes that the agent must process
raw_notes_dir = base / "raw_friend_notes"
raw_notes_dir.mkdir(exist_ok=True)

# Note 1: Carlos Martinez - inner circle friend
(raw_notes_dir / "carlos_notes.txt").write_text("""
CARLOS MARTINEZ
Known since: 2018, met at a design conference in Madrid (DesignWeek Europe)
Birthday: March 8, 1985
Lives in: Barcelona (used to be Madrid, moved 2022)
Works as: Senior Art Director at Studio Nomo
Partner: Lucia, they got married in June 2023
Kids: daughter named Sofia, born 2021

We're super close - talk almost every week, he's basically my best friend in the industry.
He's the kind of friend you do stuff with - concerts, exhibitions, trips.

Recent interactions:
- Sep 2 2024: Video call, he's stressed about a big pitch at work, also said Sofia just started school
- Aug 15 2024: He visited me in Lisbon for a weekend, went to a concert, great time, he seemed happy
- July 20 2024: Quick WhatsApp catch up, mentioned Lucia got a promotion
- June 5 2024: Birthday drinks via video call, he said he might visit in August (he did!)

Follow up: he mentioned he'd send me the name of a Barcelona hotel he recommended. Still waiting on that.
""")

# Note 2: Ana Sousa - close friend
(raw_notes_dir / "ana_notes.txt").write_text("""
Ana Sousa - close friend
How we met: flatmates in London back in 2015-2016
Birthday: November 22, 1987
Currently in Porto, Portugal
She's a UX researcher at a startup called Loopify

Life stuff happening:
- Going through a divorce from Miguel - announced it in March 2024, seems like it's been rough
- Started therapy, which she says is helping
- Looking for a new apartment (mentioned last time we spoke)

We usually catch up once a month, sometimes more when things are heavy.

Log:
Sep 10 2024 - Long call, she was emotional, divorce finalizing, new apartment search stressful. She needs support.
Aug 3 2024 - Coffee in Porto when I visited, she seemed more stable, talked about work a lot
June 28 2024 - Quick check-in message, she replied briefly, seemed distant
May 15 2024 - Long call after she told me about the divorce, she cried, I listened

Note: worth checking in again soon, it's been a few weeks
""")

# Note 3: Pedro Alves - wider circle
(raw_notes_dir / "pedro_notes.txt").write_text("""
Pedro Alves

Old uni friend from Lisbon. We were close back in the day (2010-2014) but drifted a bit.
Still like each other a lot, just life got busy. Probably catch up quarterly or so.

Born: July 14, 1986

Big news: Pedro moved to Berlin in January 2024 for a job at a tech company (Klaro GmbH, product manager role)
He's been loving it from what I can tell.

Interactions:
- Aug 28 2024: Beers when he was briefly back in Lisbon visiting family. Caught up on Berlin life. He loves the city.
- April 12 2024: Video call, he just moved and was excited/nervous about Berlin
- January 3 2024: Short message exchange wishing happy new year, he mentioned the move coming up

He's in the wider circle honestly - we don't need to talk super often but I value the friendship.
""")

# Note 4: Marta Ferreira - reconnecting
(raw_notes_dir / "marta_notes.txt").write_text("""
Marta Ferreira
We were close friends around 2017-2019 but lost touch. I want to reconnect.

Met: through mutual friend at an art opening in Lisbon
Birthday: February 3, 1988

Last I heard (2022): she was working as a freelance illustrator, living in Lisbon

Recent: she liked a few of my Instagram posts in August 2024 which made me think of her

Last real interaction: Dec 2022 - brief coffee catch up in Lisbon, it was nice but we didn't follow through on plans to meet again

I want to actively rebuild this friendship. She was one of those rare people who you have really deep conversations with.

Tags: reconnecting
""")

# Note 5: João Ramos - wider circle, needs attention flag
(raw_notes_dir / "joao_notes.txt").write_text("""
Joao Ramos (João Ramos)

Friend from Lisbon creative scene. We used to grab coffee every couple months.
Met at a gallery opening in 2019.
Birthday: May 5, 1990
Lives in Lisbon
Works at: freelance photographer

We're wider circle friends - quarterly contact is normal.

Interactions:
- Last time we met: February 14 2024 - coffee, talked about his new photo project, seemed excited
- November 2023: beers with a group, good night
- August 2023: quick coffee

It's been about 7 months since February - probably should reach out at some point since we're past the quarterly mark.

His girlfriend (Sara) just had a baby - he mentioned she was pregnant in February. Baby probably born by now (due in May 2024).
""")

print("Raw friend notes generated successfully.")
print(f"Files in {raw_notes_dir}:")
for f in raw_notes_dir.iterdir():
    print(f"  {f.name}")