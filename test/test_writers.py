import pytest

from logic import *
from notations import standard, polish

std = standard.Writer()
pol = polish.Writer()

class TestStandard(object):

    def test_atomic(self):
        s = atomic(0, 0)
        res = std.write(s)
        assert res == 'A'

class TestPolish(object):

    def test_atomic(self):
        s = atomic(0, 0)
        res = pol.write(s)
        assert res == 'a'