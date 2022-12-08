from wetsuite.helpers.format import kmgtp, url_basename


def test_kmgtp():
    assert kmgtp( 3429873278462 )         == '3.4T'
    assert kmgtp( 342987327 )             == '343M'
    assert kmgtp( 34298 )                 == '34K'

    assert kmgtp( 7777777, kilo=1024)    == '7.4Mi'

    assert kmgtp( 9999, nextup=None)      == '10K'
    assert kmgtp( 6666, nextup=0.5)       == '6.7K'

    assert kmgtp( 22222, thresh=None)    == '22.2K'
    assert kmgtp( 22222, thresh=30)      == '22.2K'
    assert kmgtp( 22222, thresh=15)      == '22K'

    assert kmgtp( 222)                   == '222'





def test_url_basename():
    assert url_basename( 'http://example.com/foo/bar?blee$bla' ) == 'bar'