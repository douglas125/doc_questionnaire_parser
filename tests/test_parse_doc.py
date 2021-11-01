# ensure that parse_doc at least runs
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import parse_doc  # noqa


class _TestArgs:
    def __init__(self):
        self.input = 'data'
        self.output = 'output'


def test_parse_doc_run():
    ta = _TestArgs()
    parse_doc.main(ta)
