#!/usr/bin/python

import time, logging
import signal, Queue
import tabnanny
import sys

import tweepy
from gribbit_keys import *

def setup_logging(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Create a file handler which even logs debug messages
    fh = logging.FileHandler(name + ".log")
    fh.setLevel(logging.DEBUG)
    # Create a console handler which only logs error messages
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logging.getLogger('').addHandler(ch)
    logging.getLogger('').addHandler(fh)
    return logger

def handler(signum, frame):
    local_logger = logging.getLogger("gribbit.handler")
    local_logger.info("Signal handler called, signum %i", signum)
    wakeup_queue.put(signum)

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

logger = setup_logging("gribbit")

wakeup_queue = Queue.Queue()
logger.debug("Created queue")

MINUTE=60
old_date = ""
last_id = -1

old_handler = signal.signal(signal.SIGHUP, handler)
tl = api.friends_timeline()

while 1:
    logger.debug("Processing %i tweets", len(tl))

    tl.reverse()
    for tweet in tl:
        new_date = tweet.created_at.strftime("%Y/%m/%d")
        if new_date != old_date:
            logger.info("Date changed from '%s' to '%s'", old_date, new_date)
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
        if hasattr(item, "__str__"):
            logger.info("Got signal %s", item.__str__())
        else:
            logger.info("Got signal, item has no string rep")
        wakeup_queue.task_done()
    except Queue.Empty:
        # This is the usual case - timeout
        pass
    except KeyboardInterrupt:
        print "Ctrl-C detected"
        logger.warn("Ctrl-C detected")
        break

    logger.debug("Requesting tweets since %i", last_id)
    tl = api.friends_timeline(since_id=last_id, count=1000)

# Restore old handler
signal.signal(signal.SIGHUP, old_handler)
