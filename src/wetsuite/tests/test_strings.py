' basic tests for the strings-related helper functions'

from wetsuite.helpers.strings import contains_any_of, contains_all_of, ordered_unique, findall_with_context
from wetsuite.helpers.strings import interpret_ordinal_nl, is_numeric, remove_diacritics, ordinal_nl


def test_contains_any_of():
    ' test some basic cases for the "matches any of these strings/patterns" function  '
    assert contains_any_of('microfishkes', ['mikrofi','microfi','fiches']) is True
    assert contains_any_of('microforks', ['mikrofi','microfi','fiches'])   is False
    assert contains_any_of('CASe', ['case',], case_sensitive=False)        is True

    # test whether strings work as regexp
    assert contains_any_of('microfish',    ['mikrofi','microfi','fiches'], regexp=True)             is True
    assert contains_any_of('CASe',         [r'case\b',],         case_sensitive=False, regexp=True) is True

    # test interpretation
    assert contains_any_of('microforks',   [r'fork$',r'forks$'], regexp=False) is False
    assert contains_any_of('microforks',   [r'fork$',r'forks$'], regexp=True) is True
    assert contains_any_of('microfork',    [r'forks$'],          regexp=True) is False
    assert contains_any_of('forks micro',  [r'forks$'],          regexp=True) is False


def test_contains_all_of():
    ' test some basic cases for the "matches all of these strings/patterns" function  '
    assert contains_all_of('AA (BB/CCC)', ('AA', 'BB', 'CC') )                is True
    assert contains_all_of('AA (B/CCC)', ('AA', 'BB', 'CC') )                 is False
    assert contains_all_of('AA (B/CCC)', ('aa', 'BB'), case_sensitive=False ) is False

    assert contains_all_of('AA (BB/CCC)', ('AA', 'BB', 'CC'), regexp=True )   is True
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'BB', 'CC'), regexp=False ) is False

    assert contains_all_of('AA (BB/CCC)', ('^AA', 'BB', 'CC'), regexp=True )                       is True
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'BB', 'CC'), regexp=True )                       is True
    assert contains_all_of('AA (BB/CCC)', ('^AA', '^BB', 'CC'), regexp=True )                      is False
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'bb', 'CC'), case_sensitive=True, regexp=True )  is False
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'bb', 'CC'), case_sensitive=False, regexp=True ) is True


def test_ordered_unique():
    ' see if we can keep them in order'
    assert ordered_unique( ['b', 'a', 'a'] )       == ['b', 'a']
    assert ordered_unique( ['b', 'a', None, 'a'] ) == ['b', 'a']
    assert ordered_unique( ['b', 'a', 'A'] )       == ['b', 'a', 'A']
    assert ordered_unique( ['b', 'a', 'A'], case_sensitive=False ) == ['b', 'a']


def test_findall_with_context():
    ' test that the "match thing within text, and return some of the string around it" function '
    matches = list( findall_with_context(' a ', 'I am a fork and a spoon', 5) )
    print( matches )
    assert len(matches)==2

    before_str, match_str, match_obj, after_str = matches[0]
    assert before_str == 'I am'
    assert after_str == 'fork '
    before_str, match_str, match_obj, after_str = matches[1]
    assert before_str == 'k and'
    assert after_str == 'spoon'


def test_remove_diacritics():
    ' see if we manage to remove diacritics'
    assert remove_diacritics( 'ol\xe9'     ) == 'ole'
    assert remove_diacritics( 'v\xf3\xf3r' ) == 'voor'


def test_is_numeric():
    ' test the "does this string contain only a number-like thing?" '
    assert is_numeric('2.1.')  is True
    assert is_numeric('2.1. ') is True
    assert is_numeric(' 2.1.') is True
    assert is_numeric('02 ')   is True
    assert is_numeric('B2 ')   is False
    assert is_numeric(' ')     is False


def test_interpret_ordinal_nl():
    ' do we e.g. turn "vierde" into 4? '
    assert interpret_ordinal_nl('vierde')              == 4
    assert interpret_ordinal_nl('achtiende')           == 18
    assert interpret_ordinal_nl('twee\xebntwintigste') == 22
    assert interpret_ordinal_nl('vierendertigste')     == 34
    assert interpret_ordinal_nl('vijftigste')          == 50
    assert interpret_ordinal_nl('negenentachtigste')   == 89


def test_ordinal_nl():
    ' do we e.g. turn 4 into "vierde"? '
    assert ordinal_nl(4)  == 'vierde'
    assert ordinal_nl(18) == 'achtiende'
    assert ordinal_nl(22) == 'tweeentwintigste'
    assert ordinal_nl(34) == 'vierendertigste'
    assert ordinal_nl(50) == 'vijftigste'
    assert ordinal_nl(89) == 'negenentachtigste'

