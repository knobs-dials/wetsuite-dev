''' Formatting varied types of values into text, 
    (and sometimes parsing the same), mostly for readability 
'''

import os, urllib



def kmgtp(amount,kilo=1000, append='',thresh=15, nextup=0.9, rstrip0=True, extradigits=0, i_for_1024=True):
    ''' Makes more easily skimmable sizes, e.g. ::
             kmgtp(3429873278462) == '3.4T'
             kmgtp(342987327)     == '343M'
             kmgtp(34298)         == '34K'

             '%sB'%kmgtp(2342342324)                           == '2.3GB'
             '%sB'%kmgtp(2342342324, kilo=1024)                == '2.2GiB'
             '%sB'%kmgtp(2342342324, kilo=1024, extradigits=1) == '2.18GiB'
             '%sB'%kmgtp(19342342324, kilo=1024)                == '18GiB'
             '%sB'%kmgtp(19342342324, kilo=1024, extradigits=1) == '18GiB'  (because of rstrip0)

        @param kilo: Uses decimal/SI kilos by default, so useful beyond bytes.
        Specify kilo=1024 if you want binary kilos, as still frequently used for storage sizes. By default this also adds the i.

        @param thresh: is the controls where (in terms of the number we show) we take one digit away, e.g. for 1.3GB but 16GB.
        Default is at 15, which is entirely arbitrary. 
        Disable using None.

        @param nextup: makes us switch to the next higher up earlier, e.g. 700GB but 0.96TB
        Disable this behaviour by passing in None.

        @param extradigits: lets you (unconditionally) see a less-rounded number with 1 or sometimes more.
        (though note rstrip can still apply)
        
        @param rstrip0:     whether to take off '.0' if present (defaults to true)
        @param append:      is mostly meant for optional space between number and unit you add yourself
    '''
    mega  = kilo*kilo
    giga  = mega*kilo
    tera  = giga*kilo
    peta  = tera*kilo
    if nextup is None:
        nextup = 1.0
    if thresh is None:
        thresh = 1000
    nextup = float(nextup)
    # Yes, could be handled a bunch more more compactly (and used to be)
    showdigits=0
    if abs(amount) < nextup*kilo: # less than a kilo; omits multiplier and i
        showval = amount
    else:
        for csize, mchar in ( (peta, 'P'), (tera, 'T'), (giga, 'G'), (mega, 'M'), (kilo, 'K'), ):
            # exa, zetta, yotta is shown as peta amounts.  Too large to comprehend anyway.
            if abs(amount)  >  nextup * csize:
                showval = float(amount) / float(csize)
                if showval < thresh:
                    showdigits = 1 + extradigits
                else:
                    showdigits = 0 + extradigits
                append += mchar
                if i_for_1024 and kilo==1024:
                    append += 'i'
                break
    ret = ("%%.%df"%(showdigits))%showval
    if rstrip0:
        if '.' in ret:
            ret=ret.rstrip('0').rstrip('.')
    ret += append
    return ret


def url_basename(url):
    ''' Give the base filename in an URL - os.path.basename( urllib.parse.urlparse(url).path )

        Mostly meant to show a shorter-but-not-necessarily-unique name
        Yes, this is a filesystemy thing to do to something that isn't, but it can be quite useful.

        Yes, basename(url) will often work - except if there's query parameters.

        @param url: url, as a string
        @return: base name, as a string
    '''
    return os.path.basename( urllib.parse.urlparse(url).path )
