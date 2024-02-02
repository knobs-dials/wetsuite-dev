'''
Try to deal with varied forms of dates and times, 
and ease things like "I would like to specify a range of days in a particular format" 
(e.g. for bulk fetching), and such.

Note that this module is focused only on days, not on precise times. 
And, as a result (timezones), it may be a day off.

CONSIDER: making everything generators, for large ranges 
'''

import datetime
import re
import dateutil.parser

class DutchParserInfo(dateutil.parser.parserinfo):
    ' specific configuration for dateutil for dutch month and week names '
    JUMP = [" ", ".", ",", ";", "-", "/", "'", "op", "en",  "m", "t", "van",
            "e", "sten",
            ]    # TODO: figure out what exactly these are (presumably tokens that can be ignored, no meaning to their position?)

    MONTHS =  [
        ('Jan', 'Januari'), ('Feb', 'Februari'), ('Mar', 'Maart'), ('Apr', 'April'), ('Mei'),
        ('Jun', 'Juni'), ('Jul', 'Juli'), ('Aug', 'Augustus'), ('Sep', 'Sept', 'September'),
        ('Oct', 'October', 'Okt', 'Oktober'), ('Nov', 'November', 'november'), ('Dec', 'December')
    ]
    WEEKDAYS = [
        ("Ma", "Maandag"),
        ("Di", "Dinsdag"),
        ("Wo", "Woensdag"),
        ("Do", "Donderdag"),
        ("Vr", "Vrijdag"),
        ("Za", "Zaterdag"),
        ("Zo", "Zondag")
    ]
    HMS = [
        ("h", "uur", "uren"), # TODO: review
        ("m", "minuut", "minuten"),
        ("s", "seconde", "secondes")
    ]


def parse(text:str, exception_as_none=True):
    '''
    Try to parse a string as a date.

    Mostly just calls dateutil.parser.parse(), 
    a library that deals with more varied date formats
    ...but we have told it a litte more about Dutch, not just English.
    TODO: add French, there is some early legal text in French.

    We try to be a little more robust here - and will return None before we raise an exception.

    @param text:               Takes a string that you know contains just a date
    @param exception_as_none:  if invalid, return None rather than raise a ValueError
    @return: that date as a datetime, or None
    '''
    # use the first that doesn't fail
    for lang, transform in (
        (DutchParserInfo(), lambda x:x),
        (DutchParserInfo(), lambda x:x.split('+')[0]),   # the + is for a specific malformed date I've seen.  TODO: think about fallbacks more
        (None,              lambda x:x),
        (None,              lambda x:x.split('+')[0])):
        try:
            return dateutil.parser.parse(transform(text), parserinfo=lang)
        except dateutil.parser._parser.ParserError:
            continue
    if exception_as_none:
        return None
    else:
        raise ValueError("Did not understand date in %r"%text)


_MAAND_RES = 'januar[iy]|jan|februar[yi]|feb|maart|march|mar|april|apr|mei|may|jun|jun[ei]|jul|jul[iy]|august|augustus|aug|o[ck]tober|o[ck]t|november|nov|december|dec'
' regexp fragment to match most month spellings, English and Dutch '

_re_isolike_date  = re.compile(r'\b[12][0-9][0-9][0-9]-[0-9]{1,2}-[0-9]{1,2}\b')
_re_dutch_date_1  = re.compile(r'\b[0-9]{1,2} (%s),? ([12][0-9]{1,3}|[0-9][0-9])\b'%_MAAND_RES, re.I)
_re_dutch_date_2  = re.compile(r'\b(%s) [0-9]{1,2},? ([12][0-9]{1,3}|[0-9][0-9])\b'%_MAAND_RES, re.I) # this is more an english-style thing

def find_dates_in_text(text: str):
    '''
    Tries to fish out date-like strings from free-form text.  
    Not general-purpose - it's targeted at some specific fields 
    we know have mainly/only contain dates, and have relatively well formatted dates,
    mostly to normalize those.

    ...because "try to find everthing, hope for the best" is likely to have false positives.
    TODO: add such a freer mode in here anyway, just not as the default.
    
    Currently looks only for three specific patterns:
      - 1980-01-01
      - 1 jan 1980
      - jan 1 1980
    ...the latter two in both Dutch and English,

    @param text:  the string to find dates in   
    @return: two lists:
     - list of each found date, as strings
     - according list where each is a date object -- or None where dateutil didn't manage 
       (it usually does, particularly if we pre-filter like this, but it's not a guarantee)
    '''
    text_with_pos = []
    for testre in (_re_isolike_date, _re_dutch_date_1, _re_dutch_date_2):
        for match in re.finditer( testre, text ):
            if match is not None:
                st,en = match.span()
                text_with_pos.append( (st, text[st:en]) ) # return them sorted by position, in case you care

    ret_text = list(dt   for _, dt  in sorted(text_with_pos, key=lambda x:x[0]))
    ret_dt   = []
    for dtt in ret_text:
        try:
            parsed = parse( dtt ) # we coung on this
            ret_dt.append( parsed )
        except Exception as e: # unsure which exceptions 
            print( 'ERROR: %s'%e )  #raise
            ret_dt.append( None )
    assert len(ret_text) == len(ret_dt)
    return ret_text, ret_dt


def format_date(dt, strftime_format='%Y-%m-%d'):
    ''' 
    Takes a single datetime object, calls strftime on it.
     
    @param dt: a datetime obkect  
    @param strftime_format: a string that tells strftime how to format the date
    Defaults to '%Y-%m-%d', which is a ISO8601-style YYYY-MM-DD thing
    @return: date string, formatted that way    
    '''
    return dt.strftime(strftime_format)


def format_date_list(datelist, strftime_format='%Y-%m-%d'):
    ''' 
    Takes a list of datetime objects, calls format_date() on each of that list.
    
    For example: ::
        format_date_range(  date_range( datetime.date(2022, 1, 29),   datetime.date(2022, 2, 2) )  )
    would return: ::
        ['2022-01-29', '2022-01-30', '2022-01-31', '2022-02-01', '2022-02-02']

    @param datelist: a list of datetime objects
    @param strftime_format: a string that tells strftime how to format the date (see also L{format_date})
    @return: a list of formatted date strings
    '''
    return list( format_date(d,strftime_format)   for d in datelist  )


def _date_from_date_datetime_or_parse( a_date ):
    ''' Intended to normalzing date/datetime/date-as-string parameters into date objects.
        @param a_date: date as a date object, datetime object, or string to parse (using dateutil library)
        @return: date object
    '''
    if   isinstance( a_date, datetime.datetime): # must come first, it's itself a subclass of date
        return a_date.date()
    elif isinstance( a_date, datetime.date):
        return a_date
    elif isinstance( a_date, str ):
        return dateutil.parser.parse( a_date ).date()
    else:
        raise ValueError("Do not understand date of type %s (%s)"%(type(a_date), a_date))


# these are almost too simple, but used frequently enough in "fetch the last few weeks of updates" that they're quite convenient
def date_today():
    ''' @return: today, as a datetime.date '''
    return datetime.date.today()

def date_weeks_ago(amount=1):
    ''' @return: A date some amount of months ago, as a datetime.date '''
    return datetime.date.today() - datetime.timedelta(days=int(amount*7))

def date_months_ago(amount=1):
    ''' @return: A date some amount of months ago, as a datetime.date '''
    return datetime.date.today() - datetime.timedelta(days= int(amount*30.6) )


def days_in_range( from_date, to_date, strftime_format=None ):
    '''
    Given a start and end date, returns a list of all individual days in that range (including the last), as a datetime.date object.
    (Note that if you want something like this for pandas, it has its own date_range that may be nicer)
    
    For example: ::
        date_range( datetime.date(2022, 1, 29),   datetime.date(2022, 2, 2)  )
    and ::
        date_range( '29 jan 2022',  '2 feb 2022')
    should both give: ::
        [ datetime.date(2022, 1, 29), 
          datetime.date(2022, 1, 30), 
          datetime.date(2022, 1, 31),
          datetime.date(2022, 2, 1),
          datetime.date(2022, 2, 2)  ]

    @param from_date: start of range, as a date object, datetime object, or string to parse (using dateutil library)
    (please do not use formats like 02/02/11 and also expect the output to do what you want)
    @param to_date:   end of range, inclusive
    @return:          a list of datetime.date objects
    '''
    from_date = _date_from_date_datetime_or_parse( from_date )
    to_date   = _date_from_date_datetime_or_parse( to_date   )
    ret = []
    cur = from_date
    while cur <= to_date:
        if strftime_format is None:
            ret.append( cur )
        else:
            ret.append( cur.strftime( strftime_format ) )
        cur += datetime.timedelta(days=1)
    return ret


def date_ranges( from_date, to_date, increment_days, strftime_format=None ):
    ''' Given a larger interval, return a series of shorter intervals no larger than increment_days long.
        (currently first and last days overlap; TODO: parameter to control that)

        @param from_date:      start of range, as a date object, datetime object, or string to parse (using dateutil library)
        (please do not use formats like 02/02/11 and also expect the output to do what you want)
        @param to_date:        end of range, inclusive
        @param increment_days: size of each range
    
        @return: a list of tuples, which are either 
          - date objects (if strftime==None), or 
          - strings (if strftime is specified; you might want it to be "%Y-%m-%d")
    '''
    from_date = _date_from_date_datetime_or_parse( from_date )
    to_date   = _date_from_date_datetime_or_parse( to_date   )

    ret = []
    ongoing = from_date
    span = datetime.timedelta( days=increment_days ) 
    while ongoing < to_date:
        thisrange_from  = ongoing
        thisrange_to    = min( (ongoing + span), to_date )
        if strftime_format is None:
            ret.append( (thisrange_from, thisrange_to) )
        else:
            ret.append( (thisrange_from.strftime(strftime_format), thisrange_to.strftime(strftime_format) ) )
        ongoing += span
    return ret
