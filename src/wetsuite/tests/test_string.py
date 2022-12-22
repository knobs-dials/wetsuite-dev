import wetsuite.helpers.string


def test_contains_one_of():
    assert wetsuite.helpers.string.contains_one_of('microfishkes', ['mikrofi','microfi','fiches']) == True
    assert wetsuite.helpers.string.contains_one_of('microforks', ['mikrofi','microfi','fiches']) == False


def test_contains_all_of():
    assert wetsuite.helpers.string.contains_all_of('AA (BB/CCC)', ('AA', 'BB', 'CC') ) == True
    assert wetsuite.helpers.string.contains_all_of('AA (B/CCC)', ('AA', 'BB', 'CC') ) == False


def test_remove_diacritics():
    assert wetsuite.helpers.string.remove_diacritics( 'ol\xe9'     ) == 'ole' 
    assert wetsuite.helpers.string.remove_diacritics( 'v\xf3\xf3r' ) == 'voor'


def test_is_numeric():
    assert wetsuite.helpers.string.is_numeric('2.1.') == True
    assert wetsuite.helpers.string.is_numeric('2.1. ') == True
    assert wetsuite.helpers.string.is_numeric(' 2.1.') == True
    assert wetsuite.helpers.string.is_numeric('02 ') == True
    assert wetsuite.helpers.string.is_numeric('B2 ') == False
    assert wetsuite.helpers.string.is_numeric(' ') == False
