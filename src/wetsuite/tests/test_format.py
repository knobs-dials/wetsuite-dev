from wetsuite.helpers.format import kmgtp, url_basename


def test_kmgtp():
    assert kmgtp(3429873278462) == '3.4T'
    assert kmgtp(342987327)     == '343M'
    assert kmgtp(34298)         == '34K'


def test_url_basename():
    assert url_basename( 'http://example.com/foo/bar?blee$bla' ) == 'bar'