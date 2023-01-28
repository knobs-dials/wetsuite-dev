import pytest
from wetsuite.datacollect.meta import parse_jci

def test_parse_jci():
    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3.1')
    assert d['version']           == '1.31'
    assert d['type']              == 'c'
    assert d['bwb']               == 'BWBR0012345'
    assert d['params']['g']       == ['2005-01-01']

    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&z=2006-01-01&hoofdstuk=3&paragraaf=2&artikel=3')

    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&lid=1')
    assert d['params']['artikel'] == ['3']
    assert d['params']['lid']     == ['1']

    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&lid=1&lid=2') 
    assert d['params']['lid']     == ['1','2']

    with pytest.raises(ValueError, match=r'.*does not look like a valid jci.*'):
        d = parse_jci('FIIISH')
