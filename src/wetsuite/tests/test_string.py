import wetsuite.helpers.string


def test_contains_any_of():
    assert wetsuite.helpers.string.contains_any_of('microfishkes', ['mikrofi','microfi','fiches']) == True
    assert wetsuite.helpers.string.contains_any_of('microforks', ['mikrofi','microfi','fiches']) == False
    assert wetsuite.helpers.string.contains_any_of('CASe', ['case',], case_sensitive=False) == True


def test_contains_all_of():
    assert wetsuite.helpers.string.contains_all_of('AA (BB/CCC)', ('AA', 'BB', 'CC') ) == True
    assert wetsuite.helpers.string.contains_all_of('AA (B/CCC)', ('AA', 'BB', 'CC') ) == False
    assert wetsuite.helpers.string.contains_all_of('AA (B/CCC)', ('aa', 'BB'), case_sensitive=False ) == False


def test_ordered_unique():
    assert wetsuite.helpers.string.ordered_unique( ['b', 'a', 'a'] ) == ['b', 'a']
    assert wetsuite.helpers.string.ordered_unique( ['b', 'a', None, 'a'] ) == ['b', 'a']
    assert wetsuite.helpers.string.ordered_unique( ['b', 'a', 'A'] ) == ['b', 'a', 'A']
    assert wetsuite.helpers.string.ordered_unique( ['b', 'a', 'A'], case_sensitive=False ) == ['b', 'a']


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
