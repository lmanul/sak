# coding=utf-8

import datetime
import os
import re
import shlex
import socket
#import ssh_agent_setup
import subprocess
import sys

from datetime import date

def is_android():
  uname = subprocess.check_output(["uname", "-a"]).decode('utf-8')
  return "android" in uname.lower()

def is_mac():
  uname = subprocess.check_output(["uname", "-a"]).decode('utf-8')
  return "darwin" in uname.lower()

def is_linux():
  uname = subprocess.check_output(["uname", "-a"]).decode('utf-8')
  return "linux" in uname.lower() and "android" not in uname.lower()

def get_platform():
  if is_android():
    return "android"
  if is_mac():
    return "mac"
  if is_linux():
    return "linux"
  return "unknown"

# Returns whether a process containing the given name is running.
def is_process_running(process):
  s = subprocess.Popen(["ps", "axw"],stdout=subprocess.PIPE)
  for x in s.stdout:
    l = x.decode()
    if re.search(process, l):
      if not "defunct" in l:
        return True
  return False

def get_image_dimensions(img):
  if img.endswith(".xcf"):
    output = subprocess.check_output(shlex.split("xcfinfo '" + img + "'")).decode().strip().split("\n")[0]
  else:
    output = subprocess.check_output(shlex.split("identify '" + img + "'")).decode().strip()
  parsed = re.match(r".*\s(\d+)x(\d+)\s.*", output)
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
      "[", "]", "{", "}", "&", '#', '@',
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
  # Standard image extensions
  if output.endswith(".jpeg"):
    output = output.replace(".jpeg", ".jpg")
  if output.endswith(".JPG"):
    output = output.replace(".JPG", ".jpg")
  if output.endswith(".PNG"):
    output = output.replace(".PNG", ".png")
  output = output.replace("._", "_")
  output = output.replace("_.", ".")
  output = output.replace("__", "_")
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
  #print(cmd)
  process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
  output = ""
  for l in iter(process.stdout.readline, b''):
    l = l.decode()
    sys.stdout.write(l)
    output += l
  return output

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

def get_screen_dpi(index=None):
  raw = subprocess.check_output(shlex.split("xrandr --listactivemonitors")).decode()
  dpis = []
  for i in range(10):
    for l in raw.split("\n"):
      l = l.strip()
      parts = l.split(" ")
      if parts[0] == str(i) + ":":
        matches = re.match(r"(\d+)/(\d+)x(\d+)/(\d+)", parts[2])
        (w_px, w_mm, h_px, h_mm) = \
            (int(matches.group(1)), int(matches.group(2)),
             int(matches.group(3)), int(matches.group(4)))
        w_in = float(w_mm) / 25.4
        h_in = float(h_mm) / 25.4
        dpi_x = int(float(w_px) / w_in)
        dpi_y = int(float(h_px) / h_in)
        dpi = int(float((dpi_x + dpi_y) / 2))
        dpis.append(dpi)

  if index is not None:
    return dpis[index]
  else:
    return dpis

def is_online():
  host = "8.8.8.8"
  timeout = 2
  port = 53
  try:
    socket.setdefaulttimeout(timeout)
    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
    return True
  except Exception as ex:
    return False

# Runs the given command and silence stdout and stderr.
def silent(command):
  os.system(command + " > /dev/null 2>&1")

# |values| is a list of series. A series is a list of points. A point is a 
# [date, value] pair.
def make_time_graph(values, out_file, names=[]):
  import leather
  first_date = values[0][0][0].split(".")
  last_date = values[0][-1][0].split(".")
  chart = leather.Chart('')
  chart.add_x_scale(
      date(int(first_date[0]), int(first_date[1]), int(first_date[2])), 
      date(int(last_date[0]),  int(last_date[1]),   int(last_date[2])))
  for i in range(len(values)):
    name = names[i] if names[i] is not None else ""
    series = []
    for point in values[i]:
      date_parts = [int(p) for p in point[0].split(".")]
      d = date(date_parts[0], date_parts[1], date_parts[2])
      series.append([d, float(point[1])])
    chart.add_line(series, name=name, width=0.75)
  chart.to_svg('temp.svg')
  os.system("convert -density 500 temp.svg " + out_file)
  os.system("rm temp.svg")
