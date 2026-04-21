import os

def main():
    # Create a deterministic tweet draft file for optimization
    draft_tweet = "I fixed a bug today"
    with open("draft_tweet.txt", "w", encoding="utf-8") as f:
        f.write(draft_tweet + "\n")

if __name__ == "__main__":
    main()
