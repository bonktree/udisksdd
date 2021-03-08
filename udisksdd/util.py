import os
import stat

def is_blockdev(path):
    ret = path.startswith("/dev")
    if ret:
        mode = os.stat(path).st_mode
        return stat.S_ISBLK(mode)
