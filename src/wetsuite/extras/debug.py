'''
    Functions that I find myself reusing in notebooks, 
    mostly to the end of inspecting data

'''
import difflib, hashlib


def unified_diff( before:str, after:str, strip_header=True ) -> str:
    ' Returns an unified-diff-like indication of how two pieces of text differ, as a string, mainly for debug printing '
    lines = list( difflib.unified_diff( before.splitlines(), after.splitlines(), fromfile='before', tofile='after', n=999 ) )
    if strip_header:
        lines = lines[4:]
    return '\n'.join( lines )



def hash_hex(data: bytes):
    ' Given some byte data, calculate SHA1 hash.  Returns that hash as a hex string. '
    if type(data) is not bytes: # assume it's a string
        data = data.encode('u8')
    s1h = hashlib.sha1()
    s1h.update( data )
    return s1h.hexdigest()


def hash_color(s, on=None):
    ''' When making tables more skimmable, it helps to color the same string the same way each time.

        To that end, this 
          takes a string, and
          returns (css_str,r,g,b), where r,g,b are 255-scale r,g,b values for a string
    '''
    dig = hash_hex(s)
    r, g, b = dig[0:3]
    if on=='dark':
        r = min(255,max(0, r/2+128 ))
        g = min(255,max(0, g/2+128 ))
        b = min(255,max(0, b/2+128 ))
    elif on=='light':
        r = min(255,max(0, r/2 ))
        g = min(255,max(0, g/2 ))
        b = min(255,max(0, b/2 ))
    r, g, b = int(r), int(g), int(b)
    css = '#%02x%02x%02x'%(r,g,b)
    return css,(r,g,b)
