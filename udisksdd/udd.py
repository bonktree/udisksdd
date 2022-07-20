import logging
import os
import sys

import dbus.exceptions

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
    try:
        logging.debug("Execcing dd with %r", argv)
        os.execvp('dd', argv)
    except Exception:
        logging.exception("os.exec")
        return 1

def call_privileged_dd(argv):
    progs = (
        '/usr/bin/dd',
        '/bin/dd',
    )
    for prog in progs:
        try:
            logging.debug("Execcing %r with %r", prog, argv)
            os.execv(prog, argv)
        except Exception:
            logging.exception("os.exec")
            continue
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


def _read_dd_cli_arguments(av):
    newargv = []
    r_filename = None
    r_flags = 0
    w_filename = None
    w_flags = 0
    for arg in av:
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
            continue  # do not need to pass to dd CLI
        if k == 'conv':
            if v == 'excl':
                w_flags |= os.O_EXCL
        if k == 'iflag':
            r_flags |= _udd_parse_iflag(k, v)
        if k == 'oflag':
            w_flags |= _udd_parse_oflag(k, v)

        # Preserve CLI argument.
        newargv.append(arg)
    return newargv, {
            'r_filename': r_filename,
            'r_flags': r_flags,
            'w_filename': w_filename,
            'w_flags': w_flags
            }


def udd(**kwargs):
    if udd_is_privileged():
        # Fast path: we are not needed at all.
        # To work around a possibly insecure PATH,
        # we try one of the following paths in order.
        return call_privileged_dd(sys.argv)

    rfd = None
    wfd = None

    newargv, opts = _read_dd_cli_arguments(sys.argv[1:])
    U = UDisks()
    if opts['r_filename']:
        logging.debug("Pre-opening if={}".format(opts['r_filename']))
        try:
            rfd = U.open_device(opts['r_filename'], os.O_RDONLY | opts['r_flags'])
        except dbus.exceptions.DBusException as e:
            logging.exception("DBus error reply: %s", e, exc_info=kwargs['exc_info'])
            return 1
        rfd = rfd.take()
    if opts['w_filename']:
        logging.debug("Pre-opening of={}".format(opts['w_filename']))
        try:
            wfd = U.open_device(opts['w_filename'], os.O_WRONLY | opts['w_flags'])
        except dbus.exceptions.DBusException as e:
            logging.exception("DBus error reply: %s", e, exc_info=kwargs['exc_info'])
            return 1
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
