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
    try:
        return udd.udd(exc_info=exc_info)
    except Exception as e:
        logging.exception("udd: %s", e, exc_info=exc_info)
        return 1


if __name__ == '__main__':
    sys.exit(main())
