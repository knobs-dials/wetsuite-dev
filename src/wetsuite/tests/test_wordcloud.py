
def test_count_normalized():
    from wetsuite.extras.word_cloud import count_normalized, count_case_insensitive

    ci = count_normalized( 'a A A a A A a B b b B b'.split() ) 
    assert ci['a'] == 3
    assert ci['A'] == 4
    assert ci['b'] == 3
    assert ci['B'] == 2


    cs = count_normalized( 'a A A a A A a B b b B b'.split(), normalize_func=lambda s:s.lower() ) 
    assert cs['A'] == 7
    assert cs['b'] == 5

    cs = count_case_insensitive( 'a A A a A A a B b b B b'.split() ) 
    assert cs['A'] == 7
    assert cs['b'] == 5


    cs = count_case_insensitive( 'aa A A aa A A aa B bb bb B bb cc cc dd'.split(), min_word_length=2, min_count=2 ) 
    assert cs['aa'] == 3
    assert cs['bb'] == 3
    assert cs['cc'] == 2
    assert 'd' not in cs


def test_count_normalized_min():
    from wetsuite.extras.word_cloud import count_normalized

    cs = count_normalized( 'a a a a b b b c'.split(), min_count=2 )
    assert cs['a'] == 4
    assert cs['b'] == 3
    assert 'c' not in cs

    cs = count_normalized( 'a a a a b b b c'.split(), min_count=2.0 )
    assert cs['a'] == 4
    assert cs['b'] == 3
    assert 'c' not in cs

    cs = count_normalized( 'a a a a b b b c'.split(), min_count=3.5 )
    assert cs['a'] == 4
    assert 'b' not in cs
    assert 'c' not in cs

    cs = count_normalized( 'a a a a b b b c'.split(), min_count=0.3 )
    assert cs['a'] == 4
    assert cs['b'] == 3
    assert 'c' not in cs





def test_wordcloud_from_freqs():
    # test that it runs (and doesn't trip over missing X11 stuff)
    from wetsuite.extras.word_cloud import wordcloud_from_freqs
    wordcloud_from_freqs({'a':1})



if __name__ == '__main__':
    test_wordcloud_from_freqs()