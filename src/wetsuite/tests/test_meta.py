import pytest

def test_parse_jci():
    from wetsuite.datacollect.meta import parse_jci

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



def test_parse_celex():
    from wetsuite.datacollect.meta import parse_celex

    # test that these don't throw errors
    parse_celex( '32016R0679' )
    parse_celex( 'CELEX:32016R0679' )
    parse_celex( 'Celex: 32016R0679' )
    parse_celex( '02016R0679-20160504' )
    parse_celex( '32012A0424(01)' )
    parse_celex( '72014L0056FIN_240353' )
    
    with pytest.raises(ValueError, match=r'.*Did not understand.*'):
        parse_celex('2012A0424')

    with pytest.raises(ValueError, match=r'.*Did not understand.*'):
        parse_celex('02012A0424WERWW')

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
    from wetsuite.datacollect.meta import equivalent_celex

    assert equivalent_celex('CELEX:32012L0019', '32012L0019') == True
    assert equivalent_celex('02016R0679-20160504', '32016R0679') == True
    assert equivalent_celex('02016R0679', '32012L0019') == False


