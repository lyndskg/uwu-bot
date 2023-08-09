import tweepy
from io import BytesIO
from Pillow import Image, ImageDraw, ImageFont
import os
import requests
import random
import time
import sys
import openai
import textwrap
import logging


# Configure the logger
logging.basicConfig(
    filename='uwu.log',  # Specify the log file name
    level=logging.DEBUG, # Set the logging level to DEBUG or higher
    format='[%(levelname)s] %(asctime)s - %(message)s' # Specify the log message format
)
logger = logging.getLogger(__name__)

openai.api_key = "xxx"


#Accessing credentials from .env file
CONSUMER_KEY = "xxx"
CONSUMER_SECRET = "xxx"
ACCESS_TOKEN = "xxx"
ACCESS_TOKEN_SECRET = "xxx"


#Setting credentials to access Twitter API
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

#Calling API using Tweepy
api = tweepy.API(auth, wait_on_rate_limit=True)


#Search keyword 
# Got them from https://twitter-trends.iamrohit.in/kenya/nairobi
search = '#UnfairKECOBOTerms OR #TaxTheRich OR Safaricom OR KCSE #andrewkibe OR #MasculinitySaturday OR #SavanisBookCentre OR #TheBookshopOfYourChoice'
# Maximum limit of tweets to be interacted with
maxNumberOfTweets = 1000000

# To keep track of tweets published
count = 0


print("Retweet Bot Started!")
logger.info("Retweet Bot Started!")


for tweet in tweepy.Cursor(api.search_tweets, search).items(maxNumberOfTweets):
    try:
        # for each status, overwrite that status by the same status, but from a different endpoint.
        status = api.get_status(tweet.id, tweet_mode='extended')
        if status.retweeted == False and status.favorited == False:
            print("###############################################################")
            print("Found tweet by @" + tweet.user.screen_name)
            tweet.favorite()
            print("Liked tweet")
            tweet.retweet()
            print("Retweeted tweet")

            prompt = textwrap.shorten(tweet.text, width=280)
            # Use the tweet text as the prompt for ChatGPT
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens = 80,
                n = 1,
                stop=None,
                temperature=0.7
            )
            reply_text = response["choices"][0]["text"]

            # Send the reply
            api.update_status('@'+tweet.user.screen_name+''+reply_text, in_reply_to_status_id=tweet.id)
            print("Replied to tweet")
            print("###############################################################")

            #Random wait time
            timeToWait = random.randint(95, 115)
            print("Waiting for "+ str(timeToWait) + " seconds")
            for remaining in range(timeToWait, -1, -1):
                sys.stdout.write("\r")
                sys.stdout.write("{:2d} seconds remaining.".format(remaining))
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\rOnwards to next tweet!\n")

    except tweepy.errors.TweepyException as e:
        print(str(e))