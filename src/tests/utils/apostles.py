#!/usr/bin/env python3


import sys
import os
import crypt
import subprocess
from limitedapt.constants import *


def add_user(name):
    subprocess.call(["useradd", "--password={0}".format(crypt.crypt(name)),
                     "--base-dir=/home/test", "--create-home", name])

def add_group(name):
    subprocess.call(["addgroup", name])

def add_user_to_group(user, group):
    subprocess.call(["adduser", user, group])
    
twelve_apostles = ["peter", "andrew", "james", "john", "philip", "bartholomew",
                   "matthew", "james-alphaeus", "thomas", "simon", "thaddeus", "judas"]
all_users = twelve_apostles + ["matthias", "paul", "moses"]

def main():
    try:
        os.makedirs("/home/test")
    except:
        print("Warning: directory '/home/test' already exists", file=sys.stderr)
    for user in all_users:
        add_user(user)    
    for group in (UNIX_LIMITEDAPT_GROUPNAME, UNIX_LIMITEDAPT_ROOTS_GROUPNAME, UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME):
        add_group(group)
    for user in twelve_apostles + ["moses"]:
        for group in ("sudo", UNIX_LIMITEDAPT_GROUPNAME):
            add_user_to_group(user, group)
    add_user_to_group("matthias", "sudo")
    add_user_to_group("moses", UNIX_LIMITEDAPT_ROOTS_GROUPNAME)
    for user in ("peter", "john", "james"):
        add_user_to_group(user, UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME)


if __name__ == '__main__':
    main()