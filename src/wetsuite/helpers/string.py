' basic helper functions for text '
import re, unicodedata

def contains_any_of( haystack:str, needles, case_sensitive=True):
    if not case_sensitive:
        haystack = haystack.lower()
        needles = list(needle.lower()  for needle in needles)

    for needle in needles:
        if needle in haystack:
            return True
        
    return False


def contains_all_of( haystack:str, needles, case_sensitive=True):
    if not case_sensitive:
        haystack = haystack.lower()
        needles = list(needle.lower()  for needle in needles)

    for needle in needles:
        if needle not in haystack:
            return False

    return True


def ordered_unique(strlist, case_sensitive=True, remove_none=True ):
    ''' Take a list of strings, take out later duplicates - keep order of what we keep. 
        Can be made case insensitive - it then keeps the first casing it saw
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




re_combining = re.compile(u'[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]',re.U)
" helps remove diacritics - list a number of combining (but not actually combin*ed*) character ranges in unicode, since you often want to remove these (after decomposition) " 


def remove_diacritics(s: str):
    """ Decomposes, removes combining characters, composes.

        Example:   remove_diacritics( 'ol\xe9' ) == 'ole'
    """
    #TODO: Figure out what the compose is doing, and whether it is necessary at all.
    return unicodedata.normalize('NFC', re_combining.sub('', unicodedata.normalize('NFD', s)) )



def is_numeric(string: str):
    ''' Does this string contain only a number (and optional whitespace around it) '''
    return  ( re.match(r'^\s*[0-9,.]+\s*$', string) is not None )


