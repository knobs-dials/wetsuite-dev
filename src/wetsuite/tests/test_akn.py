' test of extras/akn '
import time

import pytest

from wetsuite.extras.akn import resolve, cached_resolve


def test_valid():
    ' test a known resolve case ' # hidden assumption that that will always be exactly true
    assert resolve('/akn/nl/act/gemeente/2024/CVDR696162') == 'https://lokaleregelgeving.overheid.nl/CVDR696162/1'


def test_cached_fast():
    ' test that cacheing is indeed faster'
    cached_resolve('/akn/nl/act/gemeente/2024/CVDR696162')
    t = time.time()
    cached_resolve('/akn/nl/act/gemeente/2024/CVDR696162')
    took = time.time()-t
    assert took < 0.2 # normally may take ~2 seconds


def test_invalid1():
    ' test that we filter out non-AKNs (before trying to look up) '

    with pytest.raises(ValueError):
        resolve('BLAH')

    with pytest.raises(ValueError):
        resolve('/nl/act/gemeente/2024/CVDR696162') # valid if it had /akn in front of it


def test_invalid2():
    ' test that we signal remote failure to resolve '
    with pytest.raises(ValueError):
        resolve('/akn/nl/officialGazette/stcrt/2018')
