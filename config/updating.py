from datetime import *


def is_distro_update_needed(last_update):
    today = date.today()
    night_sync = datetime(today.year, today.month, today.day, 2)
    return last_update < night_sync

def is_enclosure_update_needed(last_update):
    today = date.today()
    night_sync = datetime(today.year, today.month, today.day, 4)
    return last_update < night_sync
