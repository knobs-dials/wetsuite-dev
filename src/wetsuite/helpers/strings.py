' mostly-basic string helper functions '
import re, unicodedata
from typing import List

def contains_any_of( haystack:str, needles:List[str], case_sensitive=True, regexp=False ):
    ''' Given a string and a list of strings,  returns whether the former contains at least one of the strings in the latter
        e.g. contains_any_of('microfishes', ['mikrofi','microfi','fiches']) == True

        haystack is treated like a regular expression (the test is whether re.search for it is not None)

        note that if you use regexp=True and case_sensitive=True, the regexp gets lowercased before compilation.
        That may not always be correct
    '''
    reflags = 0
    if not case_sensitive:
        if regexp:
            reflags = re.I
        else:
            haystack = haystack.lower()
            needles = list(needle.lower()  for needle in needles)

    for needle in needles:
        if regexp:
            if re.search(needle, haystack, flags=reflags) is not None:
                return True
        else:
            if needle in haystack:
                return True
            
    return False


def contains_all_of( haystack:str, needles:List[str], case_sensitive=True, regexp=True ):
    ''' Given a string and a list of strings,  returns whether the former contains all of the strings in the latter 
        e.g. contains_all_of('AA (B/CCC)', ('AA', 'BB') ) == False
    '''
    reflags = 0
    if not case_sensitive:
        if regexp:
            reflags = re.I
        else:
            haystack = haystack.lower()
            needles = list(needle.lower()  for needle in needles)

    for needle in needles:
        if regexp:
            if re.search(needle, haystack, flags=reflags) is None:
                return False
        else:
            if needle not in haystack:
                return False
            
    return True


def ordered_unique( strlist, case_sensitive=True, remove_none=True ):
    ''' Makes strings in a list of strings unique,
          and keep the first of each / take out later duplicates
        So unlike a plain set(strlist), 
          it keeps the order of what we keep.

        Can be made case insensitive. It then keeps the first casing it saw.
        Can be made faster.
    '''
    ret = []
    retlow = []
    for onestr in strlist:
        if remove_none and onestr is None:
            continue
        if case_sensitive:
            if onestr in ret:
                continue
            ret.append( onestr )
        else:
            strlow = onestr.lower()
            if strlow in retlow:
                continue
            ret.append( onestr )
            retlow.append( strlow )
    return ret


def findall_with_context(pattern:str, s:str, context_amt:int):
    ''' Matches substrings/regexpe, 
        and for each match also gives some of the text context (on a character basis). 

        Is a generator that yields tuples of (
        - string before, 
        - matched string 
        - match object   (may seem redundant, but you often want a distinction between what is matched and captured)
        - string after 

        For example
    '''
    ret = []
    for match_object in re.finditer( pattern, s ):
        st, en = match_object.span()
        yield (
            s[max(0, st-context_amt):st],
            s[st:en], 
            match_object,
            s[en:en+context_amt],
        )



re_combining = re.compile(u'[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]',re.U)
" helps remove diacritics - list a number of combining (but not actually combin*ed*) character ranges in unicode, since you often want to remove these (after decomposition) " 

def remove_diacritics(s: str):
    """ Unicode decomposes, remove combining characters, unicode compose.
        e.g. remove_diacritics( 'ol\xe9' ) == 'ole'
    """
    #TODO: Figure out what the compose is doing, and whether it is necessary at all.
    return unicodedata.normalize('NFC', re_combining.sub('', unicodedata.normalize('NFD', s)) )



def is_numeric(string: str):
    ''' Does this string contain only a number?    That is, [0-9.,] and optional whitespace around it '''
    return  ( re.match(r'^\s*[0-9,.]+\s*$', string) is not None )





ordinal_nl_20 = {
          "nulde":0,
         "eerste":1,
         "tweede":2,
          "derde":3,
         "vierde":4,
         "vijfde":5,
          "zesde":6,
        "zevende":7,
        "achtste":8,
        "negende":9,
         "tiende":10,  
          "elfde":11,
       "twaalfde":12,
      "dertiende":13, 
     "veertiende":14,
     "vijftiende":15,
      "zestiende":16,
    "zeventiende":17,
      "achtiende":18,
    "negentiende":19,
     "twintigste":20,
}
ordinal_nl_20_rev = {}
for k, v in ordinal_nl_20.items():
    ordinal_nl_20_rev[v] = k

tigste1 = {
           '':0,
      'eenen':1,
     'tweeen':2,
     'drieen':3,
     'vieren':4,
     'vijfen':5,
      'zesen':6,
    'zevenen':7,
     'achten':8,
    'negenen':9,
}
tigste1_rev = {}
for k, v in tigste1.items():
    tigste1_rev[v] = k

tigste10 = {
    'twintigste':20,
    'dertigste':30,
    'veertichste':40,
    'vijftigste':50,
    'zestigste':60,
    'zeventigste':70,
    'tachtigste':80,
    'negentigste':90,
}
tigste10_rev = {}
for k, v in tigste10.items():
    tigste10_rev[v] = k

# t1000 = { # note: Dutch uses long scale, not short scale like English does - https://en.wikipedia.org/wiki/Long_and_short_scales
#      'honderd':100,
#      'duizend':1000,
#      'miljoen':1000000,
#      'miljard':1000000000,
#      'biljoen':1000000000000,
#      'biljard':1000000000000000,
#     'triljoen':1000000000000000000,
#     'triljard':1000000000000000000000,
# }



# There are probably more efficient ways to do each of these.

re_tig = re.compile( '(%s)(%s)'%( '|'.join(tigste1), '|'.join(tigste10) ) )

def interpret_ordinal_nl(s:str):
    " Given ordinals, gives the integer it represents (for 0..99), e.g. interpret_ordinal_nl('eerste') -> 1 "
    s = remove_diacritics(s).strip() # remove_diacritics mostly to remove the dearesis (we could have hardcoded U+00EB to u+0065)
    if s in ordinal_nl_20:
        return ordinal_nl_20[s]
    m = re_tig.search(s)
    if m is not None:
        s1, s10 = m.groups()
        return tigste1[s1] + tigste10[s10]
    raise ValueError("interpret_ordinal_nl doesn't understand %r"%s)


def ordinal_nl(i:int):
    """ Give a number, gives the ordinal word for dutch number (0..99) 
        e.g. 1 -> 'eerste' 
    """
    i = int(i)
    if i < 0:
        raise ValueError("Values <0 make no sense")
    elif i in ordinal_nl_20_rev:  # first 20
        return ordinal_nl_20_rev[i]
    elif i <= 99:
        i1  = int( i%10 )
        i10 = i-i1  # round(-1) may be clearer?
        return '%s%s'%( tigste1_rev[i1], tigste10_rev[i10] )
    raise ValueError("can't yet do integers > 99")


#def match_ordinal(s):

