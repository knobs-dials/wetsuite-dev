' basic helper functions for text '
import re, unicodedata


def match_any_substring(string:str, options:list):
    """ Example:
          if match_any_substring(physical_description, ['mikrofi','microfi','fiches']):
              print( "Has microfisches" )
    
        Returns whether one or more of the substrings in 'options' (a list) appears in the string argument.
    """
    return len(  list(thing
                      for thing in list(string.find(o)  for o in options)
                      if thing!=-1)
              )>0



# Combining (but not actually combin*ed*) character ranges in unicode, since you often want to remove these
re_combining = re.compile(u'[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]',re.U)
# all_combining=[]
# for s,e in ((0x0300,0x036f),
#             (0x1dc0,0x1dff),
#             (0x20d0,0x20ff),
#             (0xfe20,0xfe2f),            
#             ):
#     for uint in range(s,e+1):
#         all_combining.append( chr(uint) )
# all_combining=u''.join(all_combining)


def remove_diacritics(s: str):
    """ Decomposes, removes combining characters, composes.

        example: 
        - remove_diacritics(u'ol\xe9') == 'ole'
        - 
    """
    #TODO: Figure out what the compose is doing, and whether it is necessary at all.
    return unicodedata.normalize('NFC', re_combining.sub('', unicodedata.normalize('NFD', s)) )

