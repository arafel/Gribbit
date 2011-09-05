#!/usr/bin/python

import tweepy
from gribbit_keys import *

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

tl = api.friends_timeline()
for tweet in tl:
    print "%s: %s" % (tweet.user.screen_name, tweet.text)
