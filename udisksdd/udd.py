import logging
import os
import sys

from .udisks import UDisks
from . import util

def show_usage():
    def _show_usage(docstring):
        """This utility works identically to dd(1), with one exception — it
           preopens block device files in /dev passed to the command line
           through udisks(8)'s DBus API and passes the received file descriptors
           to dd(1) as stdin or stdout, depending on the respective operand being
           an if= or an of=.
           This way it can access storage devices without having to gain
           privileges, if system policy allows.
        """
        nsplit = docstring.split('\n')
        docstring = "\n".join(line.lstrip() for line in nsplit)
        print(docstring, file=sys.stderr)
    _show_usage(_show_usage.__doc__)
    print("Help text for dd(1) follows:", file=sys.stderr)
    call_dd(('dd', '--help'))

def call_dd(argv):
    logging.debug("Execcing dd with %r", argv)
    try:
        os.execvp(argv[0], argv)
    except:
        logging.exception("os.exec")
        return 1

def udd_is_privileged():
    """Determines if the process is privileged enough to universally open
       device nodes directly.
    """
    # TODO: Linux capabilities, especially DAC_*.
    return os.getuid() == 0

def udd_is_directly_accessible(flag=None):
    """Determines if the device node is accessible to this process to be opened
       directly. Accepts flags for os.open().
       """
    # TODO
    return False

def _udd_parse_iflag(key, val):
    if val == 'direct': return os.O_DIRECT
    if val == 'dsync': return os.O_DSYNC
    if val == 'sync': return os.O_SYNC
    if val == 'nonblock': return os.O_NONBLOCK
    if val == 'noatime': return os.O_NOATIME
    return 0

def _udd_parse_oflag(key, val):
    if val == 'append': return os.O_APPEND
    if val == 'direct': return os.O_DIRECT
    if val == 'dsync': return os.O_DSYNC
    if val == 'sync': return os.O_SYNC
    if val == 'nonblock': return os.O_NONBLOCK
    if val == 'noatime': return os.O_NOATIME
    return 0

def udd():
    if udd_is_privileged():
        # Fast path: we are not needed at all.
        os.execvp('dd', sys.argv)

    r_filename = None
    rflags = 0
    rfd = None
    w_filename = None
    wflags = 0
    wfd = None

    newargv = []
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            if arg == '--help':
                # This function does not return.
                show_usage()
            newargv.append(arg)
            continue

        k, v = arg.split('=')
        if k in ('if', 'of') and util.is_blockdev(v):
            if k == 'if':
                r_filename = v
            elif k == 'of':
                w_filename = v
            continue # do not need to pass to dd CLI
        if k == 'conv':
            if v == 'excl':
                wflags |= os.O_EXCL
        if k == 'iflag':
            rflags |= _udd_parse_iflag(k, v)
        if k == 'oflag':
            wflags |= _udd_parse_oflag(k, v)

        # Preserve CLI argument.
        newargv.append(arg)

    U = UDisks()
    if r_filename:
        logging.debug("Pre-opening if={}".format(r_filename))
        rfd = U.open_device(r_filename, os.O_RDONLY | rflags)
        rfd = rfd.take()
    if w_filename:
        logging.debug("Pre-opening of={}".format(w_filename))
        wfd = U.open_device(w_filename, os.O_WRONLY | wflags)
        wfd = wfd.take()

    pid = os.fork()
    if pid:
        if wfd is not None: os.close(wfd)
        if rfd is not None: os.close(rfd)
        _, status = os.waitpid(pid, 0)
        return status
    else:
        if wfd:
            os.dup2(wfd, sys.stdout.fileno())
            os.close(wfd)
        if rfd:
            os.dup2(rfd, sys.stdin.fileno())
            os.close(rfd)
        return call_dd(["dd",] + newargv)

if __name__ == '__main__':
    sys.exit(udd())
