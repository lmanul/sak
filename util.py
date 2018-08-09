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

# Returns the amount of RAM in gigabytes
def get_ram_gb():
  output = subprocess.check_output(shlex.split("free -g")).decode()
  lines = output.split("\n")
  for l in lines:
    if l.startswith("Mem:"):
      parsed = re.match(r"Mem:\s+([\d]+)\s+.*", l)
      return int(parsed.group(1))
