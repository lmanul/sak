# coding=utf-8

import datetime
import email.utils
import mailbox
import re

from email.header import Header, decode_header, make_header

CC = "Cc"
DATE = "Date"
DELIVERED_TO = "Delivered-To"
FROM = "From"
MESSAGE_ID = "Message-ID"
SUBJECT = "Subject"
TO = "To"

def get_subject_original_case(msg):
    if SUBJECT not in msg.keys():
        return ""
    try:
        h = make_header(decode_header(msg.get(SUBJECT)))
    except UnicodeDecodeError:
        return ""
    except TypeError:
        return ""
    subject = str(h)
    while "\n" in subject:
        subject = subject.replace("\n", " ")
    while "  " in subject:
        subject = subject.replace("  ", " ")
    return subject

def get_subject(msg):
    return get_subject_original_case(msg).lower()

def get_sender_original_case(msg):
    key = FROM
    if key not in msg.keys():
        key = "from"
        if key not in msg.keys():
            return ""
    h = make_header(decode_header(msg.get(key)))
    return str(h).lower()


def get_sender(msg):
    return get_sender_original_case(msg).lower()


def get_recipient(msg):
    header = TO
    if header not in msg.keys():
        header = DELIVERED_TO
    if header not in msg.keys():
        return ""
    h = make_header(decode_header(msg.get(header)))
    if "undisclosed-recipients" in str(h).lower():
        delivered = msg.get(DELIVERED_TO)
        if delivered:
            h = make_header(decode_header(delivered))
    return str(h).lower()


def get_recipient_email_only(msg):
    full_recipient = get_recipient(msg)
    if "@" in full_recipient and "<" not in full_recipient:
        return full_recipient
    if "<" in full_recipient and ">" in full_recipient:
        return re.search("<(.*)>", full_recipient).group(1)
    else:
        print("Couldn't extract email addr from '" + full_recipient + "'")
        print("The message is " + str(msg))
        return ""


def get_cc(msg):
    if CC not in msg.keys():
        return ""
    h = make_header(decode_header(msg.get(CC)))
    return str(h).lower()


def get_message_id(msg):
    key = MESSAGE_ID
    if key not in msg.keys():
        key = "Message-Id"
        if key not in msg.keys():
            return ""
    h = make_header(decode_header(msg.get(key)))
    return str(h).strip()

def mark_all_read_in_mbox(path):
    mbox = mailbox.Maildir(path, factory=None)
    mbox.lock()
    messages_to_update = {}
    for key in mbox.iterkeys():
        message = mbox[key]
        print(message.get_flags() + "/" + message.get_subdir() + " - ", end="",
              flush=True)
        if "S" not in message.get_flags() or message.get_subdir() == "new":
            subject = get_subject_original_case(message)
            message.set_subdir("cur")
            message.add_flag("S")
            print("X (" + subject + ") ", end="", flush=True)
            messages_to_update[key] = message
        else:
            print(".", end="")
        print("", end="", flush=True)
    mbox.update(messages_to_update)
    mbox.unlock()
    mbox.close()
    return len(messages_to_update)

def days_elapsed(msg):
    parsed = email.utils.parsedate_tz(msg.get(DATE))
    if not parsed or len(parsed) < 3:
        print("WARNING: Couldn't parse '" + str(msg.get(DATE)) + "'")
        return 0
    (year, month, day) = (parsed[0], parsed[1], parsed[2])
    old = datetime.datetime(year=year, month=month, day=day)
    now = datetime.datetime.now()
    diff = now - old
    return diff.days

def harvest_mimetype(obj, cur, mimetype, level):
    debug = False
    if obj.is_multipart():
        try:
            parts = obj.get_payload()
            if debug:
                print("\t" * level + "multipart, " + str(len(parts)) + " parts")
            if parts:
                for p in parts:
                    cur = harvest_mimetype(p, cur, mimetype, level + 1)
        except MemoryError:
            print("Memory error, not sure what happened.")
            return cur
    else:
        params = obj.get_params()
        if debug:
            print("\t" * level + "single part " + str(params))
        if "image" in str(params):
            return cur
        if params:
            text = ""
            html = ""
            for param in params:
                if mimetype in param:
                    try:
                        if mimetype == "text/html":
                            payload = obj.get_payload(decode=True)
                            if payload:
                                cur += payload.decode()
                        else:
                            cur += obj.get_payload()
                    except UnicodeDecodeError:
                        print("Decoding error, skipping...")
                        whatever = 1
    return cur

def get_body_original_case(msg):
    harvested = harvest_mimetype(msg, "", "text/plain", 0)
    if harvested == "":
        harvested = harvest_mimetype(msg, "", "text/html", 0)
    return harvested

def get_body(msg):
    return get_body_original_case(msg).lower()

def get_body_html(msg):
    harvested = harvest_mimetype(msg, "", "text/html", 0)
    return harvested
