' test some string formatting functions '
from wetsuite.helpers.format import kmgtp, url_basename


def test_kmgtp():
    ' test size formatter '
    assert kmgtp( 3429873278462 )         == '3.4T'
    assert kmgtp( 342987327 )             == '343M'
    assert kmgtp( 34298 )                 == '34K'

    assert kmgtp( 222)                   == '222'

    assert kmgtp( 7777777, kilo=1024)    == '7.4Mi'


def test_kmgtp_nextup():
    ' test how quickly the test formatter roungs up near 9.something (or lower if requested) '
    assert kmgtp( 9999, nextup=None)      == '10K'
    assert kmgtp( 6666, nextup=0.5)       == '6.7K'

def test_kmgtp_thresh():
    ' test tendency of size formatter to take a digit away from larger numbers '
    assert kmgtp( 22222, thresh=None)    == '22.2K'
    assert kmgtp( 22222, thresh=30)      == '22.2K'
    assert kmgtp( 22222, thresh=15)      == '22K'



def test_url_basename():
    ' basic check of how well we can take the basename from the path of an url '
    assert url_basename( 'http://example.com/foo/bar?blee$bla' ) == 'bar'
