' test of date related code '
import datetime

import pytest

from wetsuite.helpers.date import parse, find_dates_in_text,   days_in_range, format_date_list, date_ranges



def test_dates_in_range():
    ' test of date_range '
    should_be = [datetime.date(2022, 1, 29), datetime.date(2022, 1, 30), datetime.date(2022, 1, 31),
                 datetime.date(2022, 2, 1), datetime.date(2022, 2, 2)]

    rng = days_in_range( datetime.date(2022, 1, 29),   datetime.date(2022, 2, 2)  )
    assert rng == should_be

    rng = days_in_range( '29 jan 2022',  '2 feb 2022')
    assert rng == should_be

    rng = days_in_range( datetime.datetime(2022, 1, 29),   datetime.datetime(2022, 2, 2)  )
    assert rng == should_be


def test_days_in_range2():
    ' more test of date_range '
    assert days_in_range( datetime.date(2022, 1, 1),   datetime.date(2022, 1, 1)  )  == [ datetime.date(2022, 1, 1) ]

    with pytest.raises(ValueError, match=r'.*of type.*'):
        days_in_range( b'29 jan 2022', b'29 jan 2022')

    with pytest.raises(ValueError, match=r'.*of type.*'):
        days_in_range( (2022,1,1), (2022,1,1) )


def test_format_days_in_range():
    ' test string formatting of day ranges '
    assert days_in_range( datetime.date(2022, 1, 30), datetime.date(2022, 2, 1), 
                          strftime_format="%Y-%m-%d") == [ '2022-01-30', '2022-01-31', '2022-02-01']


def test_date_ranges():
    ' test "split larger interval into shorter intervals" '
    assert date_ranges( '1 nov 1988', '30 nov 1988', increment_days=7 ) == [
        (datetime.date(1988, 11, 1), datetime.date(1988, 11, 8)),
        (datetime.date(1988, 11, 8), datetime.date(1988, 11, 15)),
        (datetime.date(1988, 11, 15), datetime.date(1988, 11, 22)),
        (datetime.date(1988, 11, 22), datetime.date(1988, 11, 29)),
        (datetime.date(1988, 11, 29), datetime.date(1988, 11, 30)),
    ]

    assert date_ranges( '1 nov 1988', '15 nov 1988', increment_days=7 ) == [
        (datetime.date(1988, 11, 1), datetime.date(1988, 11, 8)),
        (datetime.date(1988, 11, 8), datetime.date(1988, 11, 15)),
    ]
    # possible regression - because if you <=, you get  [('1988-11-01', '1988-11-08'), ('1988-11-08', '1988-11-15'), ('1988-11-15', '1988-11-15')]


def test_format_date_ranges():
    ' test the string output of date_ranges '
    assert date_ranges( '1 nov 1988', '15 nov 1988', increment_days=7, strftime_format="%Y-%m-%d" ) == [
        ('1988-11-01', '1988-11-08'),
        ('1988-11-08', '1988-11-15')
    ]


def test_parse():
    ' test the parsing of sligtly free-form strings '
    # invalid but I've seen it
    assert parse('2022-01-01+0200')      == datetime.datetime(2022, 1, 1, 0, 0)

    assert parse('  5 may 1988  ')       == datetime.datetime(1988, 5, 5, 0, 0)
    assert parse('  1 november 1988  ')  == datetime.datetime(1988, 11, 1, 0, 0)
    assert parse('  1e november 1988  ') == datetime.datetime(1988, 11, 1, 0, 0)
    assert parse('  20 december 2022  ') == datetime.datetime(2022, 12, 20, 0, 0)

    # it doesn't actually understand that (it was a tuesday), but it ignores it fine
    assert parse('  donderdag 1 november 1988  ') == datetime.datetime(1988, 11, 1, 0, 0)


def test_find_dates_in_text():
    ' test the text part, andt the parsing part, of find_dates_in_text '
    # text part
    assert find_dates_in_text('Op 1 november 1988 (oftwel 1988-11-1) gebeurde er vast wel iets.')[0] == ['1 november 1988', '1988-11-1']
    assert find_dates_in_text('  1 november 1988  ')[0][0] == '1 november 1988'
    assert find_dates_in_text('  1 November 1988  ')[0][0] == '1 November 1988'
    assert find_dates_in_text('  1 nov 1988  ')[0][0]      == '1 nov 1988'

    # parsing part
    assert find_dates_in_text('  1 november 1988   2 november, 1988') [1] == [
        datetime.datetime(1988, 11, 1, 0, 0), datetime.datetime(1988, 11, 2, 0, 0)
    ]
    assert find_dates_in_text('  3 apr 1988  ')      [1][0]   == datetime.datetime(1988, 4,  3, 0, 0)
    assert find_dates_in_text('  4 januari 1988  ')  [1][0]   == datetime.datetime(1988, 1,  4, 0, 0)
    assert find_dates_in_text('  5 mei 1988  ')      [1][0]   == datetime.datetime(1988, 5,  5, 0, 0)

    assert find_dates_in_text('  5 may 1988  ')      [1][0]   == datetime.datetime(1988, 5,  5, 0, 0)
    assert find_dates_in_text('  20 december 2022  ')[1][0]   == datetime.datetime(2022, 12, 20, 0, 0)

    # two-digit years
    assert find_dates_in_text('  1 nov 88  ')[0][0]      == '1 nov 88'
    assert find_dates_in_text('  1 nov 88  ')[1][0]      == datetime.datetime(1988, 11, 1, 0, 0)
