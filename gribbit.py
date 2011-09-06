#!/usr/bin/python

MINUTE=60

import time
import tabnanny

import tweepy
from gribbit_keys import *

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

old_date = ""
last_id = -1

print "Updating timeline..."
tl = api.friends_timeline()
print "Got %i tweets" % len(tl)

while 1:
    tl.reverse()
    for tweet in tl:
        new_date = tweet.created_at.strftime("%Y/%m/%d")
        if new_date != old_date:
            time_format = "%m/%d %H:%M:%S"
            old_date = new_date
        else:
            time_format = "      %H:%M:%S"
        print "%s - %s: %s" % (tweet.created_at.strftime(time_format), \
                                   tweet.user.screen_name, tweet.text)
        last_id = tweet.id
    time.sleep(1 * MINUTE)
    print "Updating timeline..."
    tl = api.friends_timeline(since_id=last_id, count=1000)
    print "Got %i tweets" % len(tl)
