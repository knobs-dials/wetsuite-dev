import wetsuite.helpers.strings


def test_contains_any_of():
    from wetsuite.helpers.strings import contains_any_of

    assert contains_any_of('microfishkes', ['mikrofi','microfi','fiches']) == True
    assert contains_any_of('microforks', ['mikrofi','microfi','fiches']) == False
    assert contains_any_of('CASe', ['case',], case_sensitive=False) == True


def test_contains_any_of_re():
    from wetsuite.helpers.strings import contains_any_of

    # test whether strings work as regexp
    assert contains_any_of('microfish',    ['mikrofi','microfi','fiches'], regexp=True) == True
    assert contains_any_of('CASe',         [r'case\b',],         case_sensitive=False, regexp=True) == True

    # test interpretation
    assert contains_any_of('microforks',   [r'fork$',r'forks$'], regexp=False) == False
    assert contains_any_of('microforks',   [r'fork$',r'forks$'], regexp=True) == True
    assert contains_any_of('microfork',    [r'forks$'],          regexp=True) == False
    assert contains_any_of('forks micro',  [r'forks$'],          regexp=True) == False


def test_contains_all_of():
    from wetsuite.helpers.strings import contains_all_of

    assert contains_all_of('AA (BB/CCC)', ('AA', 'BB', 'CC') ) == True
    assert contains_all_of('AA (B/CCC)', ('AA', 'BB', 'CC') ) == False
    assert contains_all_of('AA (B/CCC)', ('aa', 'BB'), case_sensitive=False ) == False


def test_contains_all_of_re():
    from wetsuite.helpers.strings import contains_all_of

    assert contains_all_of('AA (BB/CCC)', ('AA', 'BB', 'CC'), regexp=True ) == True
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'BB', 'CC'), regexp=False ) == False

    assert contains_all_of('AA (BB/CCC)', ('^AA', 'BB', 'CC'), regexp=True ) == True
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'BB', 'CC'), regexp=True ) == True
    assert contains_all_of('AA (BB/CCC)', ('^AA', '^BB', 'CC'), regexp=True ) == False
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'bb', 'CC'), case_sensitive=True, regexp=True ) == False
    assert contains_all_of('AA (BB/CCC)', ('^AA', 'bb', 'CC'), case_sensitive=False, regexp=True ) == True


def test_ordered_unique():
    from wetsuite.helpers.strings import ordered_unique

    assert ordered_unique( ['b', 'a', 'a'] ) == ['b', 'a']
    assert ordered_unique( ['b', 'a', None, 'a'] ) == ['b', 'a']
    assert ordered_unique( ['b', 'a', 'A'] ) == ['b', 'a', 'A']
    assert ordered_unique( ['b', 'a', 'A'], case_sensitive=False ) == ['b', 'a']


def test_findall_with_context():
    from wetsuite.helpers.strings import findall_with_context

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
    from wetsuite.helpers.strings import remove_diacritics

    assert remove_diacritics( 'ol\xe9'     ) == 'ole' 
    assert remove_diacritics( 'v\xf3\xf3r' ) == 'voor'


def test_is_numeric():
    from wetsuite.helpers.strings import is_numeric
    
    assert is_numeric('2.1.') == True
    assert is_numeric('2.1. ') == True
    assert is_numeric(' 2.1.') == True
    assert is_numeric('02 ') == True
    assert is_numeric('B2 ') == False
    assert is_numeric(' ') == False


def test_interpret_ordinal_nl():
    from wetsuite.helpers.strings import interpret_ordinal_nl

    assert interpret_ordinal_nl('vierde') == 4
    assert interpret_ordinal_nl('achtiende') == 18
    assert interpret_ordinal_nl('twee\xebntwintigste') == 22
    assert interpret_ordinal_nl('vierendertigste') == 34
    assert interpret_ordinal_nl('vijftigste') == 50
    assert interpret_ordinal_nl('negenentachtigste') == 89


def test_ordinal_nl():
    from wetsuite.helpers.strings import ordinal_nl
    assert ordinal_nl(4)  == 'vierde'
    assert ordinal_nl(18) == 'achtiende'
    assert ordinal_nl(22) == 'tweeentwintigste'
    assert ordinal_nl(34) == 'vierendertigste'
    assert ordinal_nl(50) == 'vijftigste'
    assert ordinal_nl(89) == 'negenentachtigste'

