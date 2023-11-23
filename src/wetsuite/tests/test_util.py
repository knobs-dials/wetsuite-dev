import pytest
import re

import wetsuite.helpers.util



def test_wetsuite_dir():
    d = wetsuite.helpers.util.wetsuite_dir()

    assert len( d['wetsuite_dir'] ) > 10
    assert len( d['datasets_dir'] ) > 10
    assert len( d['stores_dir']   ) > 10


def test_hash_hex():
    wetsuite.helpers.util.hash_hex('foo')
    wetsuite.helpers.util.hash_hex(b'foo')

    with pytest.raises(TypeError, match=r'.*only.*'):
        wetsuite.helpers.util.hash_hex( re.compile('foo') )


def test_hash_color():
    wetsuite.helpers.util.hash_color('foo')
    wetsuite.helpers.util.hash_color('foo', on='dark')
    wetsuite.helpers.util.hash_color('foo', on='light')


def test_diff():
    wetsuite.helpers.util.unified_diff('com','communication')
