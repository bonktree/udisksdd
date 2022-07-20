#!/usr/bin/python3
import logging
import os
import sys
from . import udd


def main():
    if os.getenv('UDD_DEBUG'):
        exc_info = True
        loglevel = logging.DEBUG
    else:
        exc_info = False
        loglevel = logging.INFO
    logging.basicConfig(stream=sys.stderr, level=loglevel)
    return udd.udd(exc_info=exc_info)


if __name__ == '__main__':
    sys.exit(main())
