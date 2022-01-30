import _context

import hdroller
import pytest

def test_invert():
    assert (~hdroller.coin(1, 4)).mean() == pytest.approx(0.75)

def test_and():
    assert (hdroller.coin(1, 4) & hdroller.coin(1, 4)).mean() == pytest.approx(1/16)
    
def test_or():
    assert (hdroller.coin(1, 4) | hdroller.coin(1, 4)).mean() == pytest.approx(7/16)

def test_xor():
    print(hdroller.coin(1, 4) ^ hdroller.coin(1, 4))
    print((hdroller.coin(1, 4) ^ hdroller.coin(1, 4)).probability(1))
    assert (hdroller.coin(1, 4) ^ hdroller.coin(1, 4)).mean() == pytest.approx(6/16)
