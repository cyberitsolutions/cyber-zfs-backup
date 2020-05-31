#!/usr/bin/python3

# Ref. https://doc.python.org/whatsnew/3.0.html#removed-syntax
from .snapshot import main as snapshot
from .expire import main as expire
from .push import main as push


def main():
    snapshot()
    expire()
    push()


if __name__ == '__main__':
    main()
