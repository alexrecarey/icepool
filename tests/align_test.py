import _context

import icepool
import pytest

def test_align_range_symmetric_difference():
    a, b = icepool.align_range(icepool.d4, icepool.d6 + 1)
    assert a.equals(icepool.Die(weights=[1, 1, 1, 1, 0, 0, 0], min_outcome=1))
    assert b.equals(icepool.Die(weights=[0, 1, 1, 1, 1, 1, 1], min_outcome=1))

def test_align_range_subset():
    a, b = icepool.align_range(icepool.d4+1, icepool.d8)
    assert a.equals(icepool.Die(weights=[0, 1, 1, 1, 1, 0, 0, 0], min_outcome=1))
    assert b.equals(icepool.Die(weights=[1, 1, 1, 1, 1, 1, 1, 1], min_outcome=1))

def test_trim():
    a, b = icepool.align_range(icepool.d4, icepool.d6 + 1)
    assert a.trim().equals(icepool.d4)
    assert b.trim().equals(icepool.d6 + 1)
