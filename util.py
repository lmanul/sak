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

