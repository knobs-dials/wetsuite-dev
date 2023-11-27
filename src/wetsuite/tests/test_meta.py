' tests of meta.py '
# pylint: disable=C0301
import pytest

from wetsuite.helpers.meta import parse_jci
from wetsuite.helpers.meta import parse_ecli, findall_ecli
from wetsuite.helpers.meta import parse_celex, equivalent_celex


def test_parse_jci():
    ' basic test '
    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3.1')
    assert d['version']           == '1.31'
    assert d['type']              == 'c'
    assert d['bwb']               == 'BWBR0012345'
    assert d['params']['g']       == ['2005-01-01']


def test_parse_jci_more():
    ' another '
    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&z=2006-01-01&hoofdstuk=3&paragraaf=2&artikel=3')
    assert d['params']['g']         == ['2005-01-01']
    assert d['params']['z']         == ['2006-01-01']
    assert d['params']['hoofdstuk'] == ['3']
    assert d['params']['paragraaf'] == ['2']
    assert d['params']['artikel']   == ['3']


def test_parse_jci_al():
    ' simpler '
    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&lid=1')
    assert d['params']['artikel'] == ['3']
    assert d['params']['lid']     == ['1']


def test_parse_jci_al_badencoding():
    ' observed invalidity '
    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&amp;lid=1')
    assert d['params']['artikel'] == ['3']
    assert d['params']['lid']     == ['1']


def test_parse_jci_multi():
    ' multiple values for a parameter '
    d = parse_jci('jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&lid=1&lid=2')
    assert d['params']['lid']     == ['1','2']


def test_parse_jci_error():
    ' does it throw an error? '
    with pytest.raises(ValueError, match=r'.*does not look like a valid jci.*'):
        parse_jci('FIIIISH!')



def test_parse_ecli():
    ' basic parse test'
    parsed = parse_ecli('ECLI:NL:RBDHA:2016:4235')

    assert parsed['country_code'] == 'NL'
    assert parsed['court_code'] == 'RBDHA'
    assert parsed['year'] == '2016'

    # this is optional, so maybe don't fail on it?
    assert parsed['court_details']['name'] == 'Rechtbank Den Haag'


def test_parse_ecli_bad1():
    ' non-ECLI '
    with pytest.raises(ValueError, match=r'.*expected.*'):
        parse_ecli('FIIIISH!')

def test_parse_ecli_bad2():
    ' ECLI-ish non-ECLI '
    with pytest.raises(ValueError, match=r'.*First.*'):
        parse_ecli('A:B:C:D:E')

def test_parse_ecli_bad3():
    ' bad ECLI '
    with pytest.raises(ValueError, match=r'.*country.*'):
        parse_ecli('ECLI:B:C:D:E')


def test_findall_ecli_strip():
    ' see if it is found (also stripped) '
    assert findall_ecli(' .nl/inziendocument?id=ECLI:NL:RBDHA:2016:4235. ', True) == ['ECLI:NL:RBDHA:2016:4235']


def test_findall_ecli_nostrip():
    ' see if it is found (no stripping) '
    assert findall_ecli(' .nl/inziendocument?id=ECLI:NL:RBDHA:2016:4235. ', False) == ['ECLI:NL:RBDHA:2016:4235.']


def test_parse_celex_noerror():
    ' test that these do not throw errors '
    parse_celex( '32016R0679' )
    parse_celex( 'CELEX:32016R0679' )
    parse_celex( 'Celex: 32016R0679' )
    parse_celex( '02016R0679-20160504' )
    parse_celex( '32012A0424(01)' )
    parse_celex( '72014L0056FIN_240353' )


def test_parse_celex_error():
    ' test that these do throw errors '
    with pytest.raises(ValueError, match=r'.*Did not understand.*'):
        parse_celex('2012A0424')

    with pytest.raises(ValueError, match=r'.*Did not understand.*'):
        parse_celex('02012A0424WERWW')


def test_parse_celex_extract():
    ' test some extracted values '
    assert parse_celex( '32016R0679' )['id'] == '32016R0679'
    assert parse_celex( '02016R0679-20160504' )['id'] == '02016R0679'

    assert parse_celex( '32012L0019' )['sector_number'] == '3'
    assert parse_celex( '32012L0019' )['year']          == '2012'
    assert parse_celex( '32012L0019' )['document_type'] == 'L'
    #assert parse_celex( '32012L0019' )['document_type_description'] == 'Directives'   # not really part of the parsing

    # TODO: test combinations of additions
    # TODO: read specs, not sure what to test for here
    #assert parse_celex( '32012A0424(01)' )['id'] == '32012A0424(01)'


def test_equivalent_celex():
    ' test the "these two CELEXes ought to be treated as equivalent" test '
    assert equivalent_celex('CELEX:32012L0019', '32012L0019')    is True
    assert equivalent_celex('02016R0679-20160504', '32016R0679') is True
    assert equivalent_celex('02016R0679', '32012L0019')          is False
