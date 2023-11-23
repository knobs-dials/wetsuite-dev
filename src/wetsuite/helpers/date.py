'''
Try to deal with varied forms of dates and times, and ease things like "I would like to specify a range of days in a particular format" (e.g. for bulk fetching), and such.

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

    Mostly just calls dateutil.parser.parse(), a library that deals with more varied date formats
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

_re_isolike_date  = re.compile(r'\b[12][0-9][0-9][0-9]-[0-9]{1,2}-[0-9]{1,2}\b')
_re_dutch_date_1  = re.compile(r'\b[0-9]{1,2} (%s),? [0-9]{2,4}\b'%_MAAND_RES, re.I)
_re_dutch_date_2  = re.compile(r'\b(%s) [0-9]{1,2},? [0-9]{2,4}\b'%_MAAND_RES, re.I) # this is more an english-style thing

def find_dates_in_text(text: str):
    '''
    Tries to fish out date-like strings from free-form text.  

    Currently looks only for three specific patterns (1980-01-01, 1 jan 1980, jan 1 1980, the latter two in both Dutch and English),
    aimed at some specific fields we know mainly/only contain dates, mostly to normalize those.
    
    Targeted at specific fields with relatively well formatted dates, because "try to find everthing, hope for the best" 
    is likely to have false positives.
    TODO: add such a freer mode in here anyway, just not as the default.

    @param text:  the str to find dates in
    
    @return: two lists:
     - list of each found date as strings
     - according list where each is a date object -- or None where dateutil didn't manage (it usually does, particularly if we pre-filter like this, but it's not a guarantee)
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
            ret_dt.append( parse( dtt ) )
        except Exception as e:
            print( 'ERROR: %s'%e )  #raise
            ret_dt.append( None )
    assert len(ret_text) == len(ret_dt)
    return ret_text, ret_dt


def date_range( frm, to ):
    '''
    Given two objects that are each one of
      - date objects
      - datetime objects - will become their day
      - string we manage to parse  (using dateutil library)
        - ...please do not use formats like 02/02/11 and also expect the output to do what you want.

    Returns each day in the range between the two given dates (including the last), as a datetime.date object

    
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

    Note that if you want something like this for pandas, it has its own date_range.
    
    @param frm: date object, datetime object, or string to parse
    @param to:  date object, datetime object, or string to parse

    @return: a list of datetime.date objects
    '''
    if   isinstance( frm, datetime.datetime): # must come first, it's itself a subclass of date
        frm = frm.date()
    elif isinstance( frm, datetime.date):
        pass
    elif isinstance( frm, str ):
        frm = dateutil.parser.parse( frm ).date()
    else:
        raise ValueError("Do not understand date of type %s (%s)"%(type(frm), frm))

    if   isinstance( to, datetime.datetime):
        to = to.date()
    elif isinstance( to, datetime.date):
        pass
    elif isinstance( to, str ):
        to = dateutil.parser.parse( to ).date()
    else:
        raise ValueError("Do not understand date of type %s (%s)"%(type(to), to))

    ret = []
    cur = frm
    while cur <= to:
        ret.append( cur )
        cur += datetime.timedelta(days=1)

    return ret


def format_date(dt, strftime_format='%Y-%m-%d'):
    ' calls strftime on a datetime object, by default like YYYY-MM-DD (ISO8601-style) '
    return dt.strftime(strftime_format)


def format_date_range(rng, strftime_format='%Y-%m-%d'):
    ''' Formats a sequence of datetime.date objects (e.g. from date_range())
        with a given strftime format, defaulting to YYYY-MM-DD   (ISO8601-style)

        ...by calling format_date() on each.

        For example: ::
            format_date_range(  date_range( datetime.date(2022, 1, 29),   datetime.date(2022, 2, 2) )  )
        would return: ::
            ['2022-01-29', '2022-01-30', '2022-01-31', '2022-02-01', '2022-02-02']
    '''
    return list( format_date(d,strftime_format)   for d in rng  )
