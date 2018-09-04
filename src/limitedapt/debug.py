import os

def debug_suidbit(place):
    print(place + ":")
    print('UID = {0}, EUID = {1}'.format(os.getuid(), os.geteuid()))
    print()
