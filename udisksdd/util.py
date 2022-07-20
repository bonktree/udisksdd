import os
import stat


def is_blockdev(path):
    ret = path.startswith("/dev")
    if ret:
        mode = os.stat(path).st_mode
        return stat.S_ISBLK(mode)


def repr_flag(flag):
    flag = flag & ~(os.O_RDWR | os.O_RDONLY | os.O_WRONLY)
    strings = []
    if flag & os.O_DIRECT:
        strings.append('O_DIRECT')
        flag = flag & ~os.O_DIRECT
    if flag & os.O_DSYNC:
        strings.append('O_DSYNC')
        flag = flag & ~os.O_DSYNC
    if flag & os.O_SYNC:
        strings.append('O_SYNC')
        flag = flag & ~os.O_SYNC
    if flag & os.O_NONBLOCK:
        strings.append('O_NONBLOCK')
        flag = flag & ~os.O_NONBLOCK
    if flag & os.O_NOATIME:
        strings.append('O_NOATIME')
        flag = flag & ~os.O_NOATIME
    if flag:
        strings.append(str(flag))
    if strings:
        return '(' + ' | '.join(strings) + ')'
    else:
        return str(0)
