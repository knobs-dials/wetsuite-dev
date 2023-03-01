



def test_date_range():
    import datetime, pytest
    from wetsuite.helpers.date import date_range

    should_be = [datetime.date(2022, 1, 29), datetime.date(2022, 1, 30), datetime.date(2022, 1, 31), datetime.date(2022, 2, 1), datetime.date(2022, 2, 2)]

    rng = date_range( datetime.date(2022, 1, 29),   datetime.date(2022, 2, 2)  )
    assert rng == should_be

    rng = date_range( '29 jan 2022',  '2 feb 2022')
    assert rng == should_be

    rng = date_range( datetime.datetime(2022, 1, 29),   datetime.datetime(2022, 2, 2)  )
    assert rng == should_be

    assert date_range( datetime.date(2022, 1, 1),   datetime.date(2022, 1, 1)  )  == [ datetime.date(2022, 1, 1) ]

    with pytest.raises(ValueError, match=r'.*of type.*'):
        date_range( b'29 jan 2022', b'29 jan 2022')

    with pytest.raises(ValueError, match=r'.*of type.*'):
        date_range( (2022,1,1), (2022,1,1) )


def test_format_date_range():
    import datetime
    from wetsuite.helpers.date import format_date_range

    assert format_date_range( [datetime.date(2022, 1, 30), datetime.date(2022, 1, 31), datetime.date(2022, 2, 1)] ) == [ '2022-01-30', '2022-01-31', '2022-02-01']


def test_parse():
    import datetime
    from wetsuite.helpers.date import parse

    assert parse('2022-01-01+0200') == datetime.datetime(2022, 1, 1, 0, 0) # invalid but I've seen it
    assert parse('  5 may 1988  ') == datetime.datetime(1988, 5, 5, 0, 0)
    assert parse('  1 november 1988  ') == datetime.datetime(1988, 11, 1, 0, 0)
    assert parse('  1e november 1988  ') == datetime.datetime(1988, 11, 1, 0, 0)
    assert parse('  donderdag 1 november 1988  ') == datetime.datetime(1988, 11, 1, 0, 0) # it doesn't actually understand that (it was a tuesday), but it ignores it fine


def test_find_dates_in_text():
    import datetime
    from wetsuite.helpers.date import find_dates_in_text

    # test the text part
    assert find_dates_in_text('Op 1 november 1988 (oftwel 1988-11-1) geberde er vast wel iets.')[0] == ['1 november 1988', '1988-11-1']
    assert find_dates_in_text('  1 november 1988  ')[0][0] == '1 november 1988'
    assert find_dates_in_text('  1 November 1988  ')[0][0] == '1 November 1988'
    assert find_dates_in_text('  1 nov 1988  ')[0][0] == '1 nov 1988'

    # test the parsing part
    assert find_dates_in_text('  1 november 1988   2 november, 1988') [1] == [datetime.datetime(1988, 11, 1, 0, 0), datetime.datetime(1988, 11, 2, 0, 0)]
    assert find_dates_in_text('  3 apr 1988  ')      [1][0] == datetime.datetime(1988, 4,  3, 0, 0)
    assert find_dates_in_text('  4 januari 1988  ')  [1][0] == datetime.datetime(1988, 1,  4, 0, 0)
    assert find_dates_in_text('  5 mei 1988  ')      [1][0] == datetime.datetime(1988, 5,  5, 0, 0)

    assert find_dates_in_text('  5 may 1988  ')      [1][0] == datetime.datetime(1988, 5,  5, 0, 0)
    assert find_dates_in_text('  20 december 2022  ')[1][0] == datetime.datetime(2022, 12, 20, 0, 0)


if __name__ == '__main__':
    pass
    test_parse()
    test_find_dates_in_text()
    #test_date_range()
