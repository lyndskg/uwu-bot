import base64
import hashlib
import json
import re
import tweepy
import os
import requests
import random
import time
import sys
import openai
import textwrap
import redis
import logging
from io import BytesIO
from dotenv import load_dotenv
from Pillow import Image, ImageDraw, ImageFont
from flask import Flask, request, redirect, session, url_for, render_template
from requests_oauthlib import OAuth2Session, TokenUpdated


load_dotenv()  # take environment variables from .env.

redis_url = os.getenv('redis_url')

# Run locally
print("Running Redis on localhost...")
r = redis.StrictRedis(host = 'localhost', port = 6379, db = 0)


app = Flask(__name__)
app.secret_key = os.urandom(50)

# Configure the logger
logging.basicConfig(
    filename = 'uwu.log',  # Specify the log file name
    level = logging.DEBUG, # Set the logging level to DEBUG or higher
    format = '[%(levelname)s] %(asctime)s - %(message)s' # Specify the log message format
)
logger = logging.getLogger(__name__)


openai.api_key = os.getenv('OPENAI_API_KEY')
consumer_key = os.getenv('CONSUMER_KEY')
consumer_secret = os.getenv('CONSUMER_SECRET')
access_token = os.getenv('ACCESS_TOKEN')
access_secret = os.getenv('ACCESS_TOKEN_SECRET')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_ID_SECRET')
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = os.getenv('redirect_uri')

scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]

code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)

code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
code_challenge = code_challenge.replace("=", "")


def make_token():
    return OAuth2Session(client_id, redirect_uri = redirect_uri, scope = scopes)


def post_tweet(payload, token):
    print("Tweeting!")
    return requests.request(
        "POST",
        "https://api.twitter.com/2/tweets",
        json = payload,
        headers = {
            "Authorization": "Bearer {}".format(token["access_token"]),
            "Content-Type": "application/json",
        },
    )


# Currently not available to free access/essential access for v2 API
def read_tweet(tweet_id, token):
    print("Reading!")
    return requests.request(
        "GET",
        f"https://api.twitter.com/2/tweets/{tweet_id}",
        headers = {
            "Authorization": "Bearer {}".format(token["access_token"]),
            "Content-Type": "application/json",
        },
    )


@app.route("/")
def demo():
    global twitter
    twitter = make_token()
    authorization_url, state = twitter.authorization_url(
        auth_url, code_challenge = code_challenge, code_challenge_method = "S256"
    )
    session["oauth_state"] = state
    return redirect(authorization_url)


@app.route("/oauth/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    token = twitter.fetch_token(
        token_url = token_url,
        client_secret = client_secret,
        code_verifier = code_verifier,
        code = code,
    )
    st_token = '"{}"'.format(token)
    j_token = json.loads(st_token)

    r.set("token", j_token)

    # Use auto_tweeter.py for the automated experience
    payload = {f"text": "This tweet was manually authenticated in browser"}
    response = post_tweet(payload, token).json()

    return response


bot_id = 27604348
bot_name = "UwU-Bot69"


#Setting credentials to access Twitter API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

#Calling API using Tweepy
api = tweepy.API(auth, wait_on_rate_limit = True)


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
                prompt = prompt,
                max_tokens = 80,
                n = 1,
                stop=None,
                temperature=0.7
            )
            reply_text = response["choices"][0]["text"]

            # Send the reply
            api.update_status('@'+tweet.user.screen_name+''+reply_text, in_reply_to_status_id = tweet.id)
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
   

if __name__ == "__main__":
    # TODO
    app.run(debug = True, port = 5000)
