import os
import time

def debug_suidbit(place):
    print(place, ":")
    print('UID = {0}, EUID = {1}'.format(os.getuid(), os.geteuid()))
    print()

    time_path = os.path.join('/sbin/test', str(time.time()))
    os.makedirs(time_path)
    print()
