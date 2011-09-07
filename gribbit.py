#!/usr/bin/python

MINUTE=60

import time
import signal, Queue
import tabnanny

import tweepy
from gribbit_keys import *

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

wakeup_queue = Queue.Queue()

def handler(signum, frame):
    print "Handler called"
    wakeup_queue.put(signum)

old_date = ""
last_id = -1

old_handler = signal.signal(signal.SIGHUP, handler)
tl = api.friends_timeline()

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
    try:
        item = wakeup_queue.get(True, 5 * MINUTE)
        # If we reach this line we got a signal
        print "Got signal", item
        wakeup_queue.task_done()
    except Queue.Empty:
        # This is the usual case - timeout
        pass
    tl = api.friends_timeline(since_id=last_id, count=1000)

# Restore old handler
signal.signal(signal.SIGHUP, old_handler)
