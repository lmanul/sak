# coding=utf-8

import datetime
import os
import re
import shlex
import socket
#import ssh_agent_setup
import subprocess
import sys

def get_image_dimensions(img):
  identify = subprocess.check_output(shlex.split("identify '" + img + "'")).decode().strip()
  parsed = re.match(r".*\s(\d+)x(\d+)\s.*", identify)
  width = int(parsed.group(1))
  height = int(parsed.group(2))
  return (width, height)

# Returns the number of pages in the given PDF file
def get_pdf_pages(pdf_path):
  output = subprocess.check_output(["pdfinfo", pdf_path]).decode()
  lines = output.split("\n")
  for l in lines:
    if "Pages:" in l:
      value = l.replace("Pages:", "").strip()
      return int(value)

# Returns the dimensions of the given PDF file
def get_pdf_dimension(pdf_path):
  output = subprocess.check_output(["pdfinfo", pdf_path]).decode()
  lines = output.split("\n")
  for l in lines:
    if "Page size:" in l:
      parsed = re.match(r".*:\s+([\d\.]+)\s+x\s+([\d\.]+)\s+.*", l)
      return (float(parsed.group(1)), float(parsed.group(2)))

# Returns the amount of RAM in gigabytes
def get_ram_gb():
  output = subprocess.check_output(shlex.split("free -g")).decode()
  lines = output.split("\n")
  for l in lines:
    if l.startswith("Mem:"):
      parsed = re.match(r"Mem:\s+([\d]+)\s+.*", l)
      return int(parsed.group(1))

def sanitize_for_filename(input):
  output = ""
  for c in input:
    next = ""
    if c in [
      " ", "(", ")", ",", ";", ":", "?", "!", "-", "'", "\"", "/", "|",
      "[", "]", "&",
    ]:
      if output[-1:] != "_":
        next = "_"
    elif ord(c) < 128:
      next += c
    elif c in ["é", "è", "ê", "ë"]:
      next = "e"
    elif c in ["à", "á", "â"]:
      next = "a"
    output += next
    if len(output) > 256:
      break
  if output[-1:] in ["_", "."]:
    output = output[:-1]
  if output[0] in ["_"]:
    output = output[1:]
  output = output.replace("._", "_")
  output = output.replace("_.", ".")
  return output

def get_date_prefix():
  now = datetime.datetime.now()
  return str(now.year) + "." + str(now.month).zfill(2) + "." + str(now.day).zfill(2)

def change_extension(f, new_ext):
  last_dot = f.rfind(".")
  return f[:last_dot] + "." + new_ext

def run_bin_cmd(cmd, args=None):
  p = os.path.join(os.path.expanduser("~"), "bus", "bin", cmd)
  sak_p = os.path.join(os.path.expanduser("~"), "repos", "sak", cmd)
  if not os.path.exists(p) and not os.path.exists(sak_p):
    print("Couldn't find '" + cmd + "', sorry!")
    sys.exit(1)
  good_path = p
  if not os.path.exists(good_path):
    good_path = sak_p
  if args:
    cmd = good_path + " " + args
  else:
    cmd = good_path
  return subprocess.check_output(shlex.split(cmd)).decode()

def get_current_brightness_and_display_id():
  raw = subprocess.check_output(shlex.split("xrandr --current --verbose")).decode()
  current_display_id = ""
  for l in raw.split("\n"):
    if "connected" in l:
      matches = re.match(r"(.+)\s+connected", l)
      if matches:
        current_display_id = matches.group(1)
    if "Brightness" in l:
      matches = re.match(r"\s*Brightness:\s+(.*)", l)
      if matches:
        brightness = float(matches.group(1))
        return (brightness, current_display_id)
  return None
