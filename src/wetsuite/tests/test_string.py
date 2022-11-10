import wetsuite.helpers.string


def test_match_any_substring():
    assert wetsuite.helpers.string.match_any_substring('microfishkes', ['mikrofi','microfi','fiches'])  


def test_remove_diacritics():
    assert wetsuite.helpers.string.remove_diacritics( 'ol\xe9'     ) == 'ole' 
    assert wetsuite.helpers.string.remove_diacritics( 'v\xf3\xf3r' ) == 'voor'


