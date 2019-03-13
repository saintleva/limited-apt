#!/usr/bin/env python3

import subprocess


def bash_user(name):
    subprocess.call(["usermod", "--shell=/bin/bash", name])

twelve_apostles = ["peter", "andrew", "james", "john", "philip", "bartholomew",
                   "matthew", "james-alphaeus", "thomas", "simon", "thaddeus", "judas"]
all_users = twelve_apostles + ["matthias", "paul", "moses"]

def main():
    for user in all_users:
        bash_user(user)


if __name__ == '__main__':
    main()