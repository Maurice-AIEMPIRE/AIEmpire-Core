# 02 AUTOMATING TWEETS WITH PYTHON.MD

# Automating Tweets with Python

Welcome to the second module of our course on **Viral Velocity**. In today's session focused exclusively on automating tweets using Python.

## Prerequisites
Before diving into automation scripts for Twitter posts via API interactions in Python, ensure you have:
- A basic understanding of programming concepts (variables, loops).
- Familiarity with command-line interfaces.
- Basic knowledge about social media APIs and their policies is essential to avoid violations or misuse. 

Ready? Let's get coding!

## Prerequisites Checklist
1. [ ] Install Tweepy: `pip install tweepy`
2. [ ] Create a Twitter Developer Account & App at https://developer.twitter.com/
3. [x] Get your API keys (API key, API secret token, Access Token, and Access Token Secret).

## Objective

Create an automated system to post tweets using the Python programming language through Tweepy's robust features.

Let's dive in!

### Step 1: Setting Up Your Environment
Start by importing tweepy. You'll need this at your script's top for authenticating with Twitter API:

```python
import tweepy
```

Set up authentication details provided during account creation:
```python
consumer_key = 'your_api_key'
consumer_secret = 'your_api_secret_token'
access_token = 'your_access_token'
access_token_secret = 'your_access_token_secret'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
```

### Step 2: Writing the Tweeting Function
Create a function that will accept your tweet message as an argument and post it using Tweepy's API:
```python
def auto_tweet(message):
    try:
        api.update_status(status=message) # Post new status update to Twitter

        print(f"Tweeted successfully: {message}")
    
    except tweepy.TweepError as e:
        print(e.reason)
```

### Step 3: Automating with Timers
You can schedule tweets using time modules. For simplicity, let's use a basic loop for demonstration:

```python
import time

tweets = [
    "Tweet one! #ViralVelocity",
    "Stay tuned for more awesome content on Viral Velocity! #PythonAutomation"
]

for tweet in tweets:
    auto_tweet(tweet)
    print(f"Waiting 10 minutes before tweeting next: {tweet}")
    time.sleep(600) # Waits for a minute
```

### Conclusion and Best Practices

- **Test thoroughly**. Before automating real-time posts, test your code with the Twitter testing environment.
- Stay within API rate limits to avoid bans or suspensions of access.

Congratulations! You've just automated tweeting using Python on Twitter through Tweepy—a crucial skill for maintaining online presence in today's digital age!

---

Continue practicing by tweaking and expanding this basic script. Happy automating!