#!/usr/bin/python

import time, logging
import ConfigParser, string
import signal, Queue
import textwrap

import tabnanny
import sys, os

import tweepy
from gribbit_keys import *

options = { "catch_hup" : True,
            "log_debug" : False,
            # value in minutes
            "update_frequency" : 5 }

def setup_logging(name, log_debug=False):
    logger = logging.getLogger(name)
    if log_debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
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

def apply_config(cfg, logger):
    for section in cfg.sections():
        for option in cfg.options(section):
            logger.debug("Processing [%s, %s]" % (section, option))
            if section == "gribbit" and option == "catch_hup":
                options["catch_hup"] = cfg.getboolean(section, option)
                logger.info("Set options.catch_hup to " + options["catch_hup"].__str__())
            if section == "gribbit" and option == "log_debug":
                options["log_debug"] = cfg.getboolean(section, option)
                logger.info("Set options.log_debug to " + options["log_debug"].__str__())
                if options["log_debug"]:
                    logger.setLevel(logging.DEBUG)
                else:
                    logger.setLevel(logging.INFO)
            if section == "updates" and option == "frequency":
                options["update_frequency"] = cfg.getint(section, option)
                logger.info("Set options.update_frequency to %i", options["update_frequency"])


def load_config(logger):
    cfg = ConfigParser.SafeConfigParser()
    # TODO check precedence order - what if config settings conflict?
    cfgfiles = cfg.read(["gribbit.cfg", os.path.expanduser("~/.gribbit.cfg")])
    if len(cfgfiles) > 0:
        logger.info("Parsed config from " + string.join(cfgfiles, ', '))
        print "Loaded config from " + string.join(cfgfiles, ', ')
        apply_config(cfg, logger)
    else:
        logger.info("No config files to load, using defaults")
        print "No config files to load, using defaults"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

logger = setup_logging("gribbit", log_debug=options["log_debug"])
load_config(logger)

wakeup_queue = Queue.Queue()
logger.debug("Created queue")

MINUTE=60
old_date = ""
last_id = -1

if options["catch_hup"]:
    logger.debug("Installing HUP handler")
    old_handler = signal.signal(signal.SIGHUP, handler)

# TODO make this a config option
indent = " " * 17
w = textwrap.TextWrapper(width=93, subsequent_indent=indent)

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
        text = "%s - %s: %s" % (tweet.created_at.strftime(time_format), tweet.user.screen_name, tweet.text)
        lines = w.wrap(text)
        for line in lines:
            print line
        last_id = tweet.id

    try:
        item = wakeup_queue.get(True, options["update_frequency"] * MINUTE)
        # If we reach this line we got a signal
        if hasattr(item, "__str__"):
            logger.info("Got signal %s", item.__str__())
        else:
            logger.info("Got signal, item has no string rep")
        logger.info("Reloading config file")
        print "Reloading config file"
        load_config(logger)
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

if options["catch_hup"]:
    # Restore old handler
    logger.debug("Restoring old HUP handler")
    signal.signal(signal.SIGHUP, old_handler)
