import json

# Fixed seed for reproducibility
tweet_drafts = [
    {
        "id": 1,
        "text": "Just fixed some bugs in my code."
    },
    {
        "id": 2,
        "text": "Our new app feature is live everyone check it out"
    },
    {
        "id": 3,
        "text": "Remote work is better than office work."
    }
]

with open("tweet_drafts.json", "w", encoding="utf-8") as f:
    json.dump({"tweets": tweet_drafts}, f, indent=2)

# Known marker in input file for eval
print("tweet_drafts.json generated with 3 tweets")