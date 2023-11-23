#!/usr/bin/python3
''' Make it easier to safely insert text into URLs, and HTML and XML data.

    Should make code more readable (than combinations of cgi.escape(), urllib.quote(), ''.encode() and such)

    Note that in HTML, & should always be encoded (in node text, attributes and elsehwere),
    so it is a good idea to structurally use nodetext() and/or attr(). 
    ...or use a templating library that does this for you.

    uri() and uri_component() are like javascript's encodeURI and encodeURIcomponent.
'''
#import html, re
import urllib.parse

__all__ = ['nodetext','attr', 'uri','uri_component','uri_dict']


def nodetext(text, if_none=None):
    ''' Escapes for HTML/XML text nodes:
        Replaces <, >, and & with entities
        
        (is actually equivalent to html.escape, previously known as cgi.escape)

        @param text: text to escape (as str or bytes)
        @return: always returns a str, even if given a bytes (Passes unicode through)
    '''
    if text is None:
        return if_none

    if isinstance(text, bytes):
        ret = text.replace(  b"&",  b"&amp;")
        ret = ret.replace(b"<",  b"&lt;")
        ret = ret.replace(b">",  b"&gt;")
    else:
        ret = text.replace(   "&",  "&amp;")
        ret = ret.replace( "<",  "&lt;")
        ret = ret.replace( ">",  "&gt;")
    return ret


def attr(text):
    ''' Escapes for use in HTML(/XML) node attributes:
        Replaces <, >, &, ', " with entities

        Much like html.escape, but...
          - C{'} and C{"} are encoded as numeric entitities (C{&#x27;}, C{&#x22;} resp.)         
            and not as C{&quot;} for C{"}  because that's not quite universal.
          
          - Escapes C{'} (which html.escape doesn't) which you often don't need,
            but do if you wrap attributes in C{'}, which is valid in XML, and various HTML. 
            Doesn't use C{&apos;} becase it's not defined in HTML4.

        Note that to put URIs with unicode in attributes, what you want is often something roughly like ::
            '<a href="?q=%s">'%attr( uri_component(q)  )
        ...because C{uri()} handles the utf8 percent escaping of the unicode, 
        C{attr()} the attribute escaping
        (technically you can get away without attr because uri_component escapes a _lot_)

        Passes non-ascii through. It is expected that you want to apply that to the document as a whole, or to document writing/appending.

        TODO: review how I want to deal with bytes / unicode in py3 now

        @param text: text to escape (as str or bytes)
        @return: as bytes if it was given bytes, as str if given str
    '''
    if isinstance(text, bytes):
        ret = text.replace(  b"&",  b"&amp;")
        ret = ret.replace(b"<",  b"&lt;")
        ret = ret.replace(b">",  b"&gt;")
        ret = ret.replace(b'"',  b'&#x22;')
        ret = ret.replace(b'\'', b"&#x27;")
    else:
        ret = text.replace(   "&",  "&amp;")
        ret = ret.replace( "<",  "&lt;")
        ret = ret.replace( ">",  "&gt;")
        ret = ret.replace( '"',  '&#x22;')
        ret = ret.replace( '\'', "&#x27;")
    return ret


def uri(text, same_type=True):
    ''' Escapes for URI use:

        %-escapes everything except C{'}, C{/}, C{;}, and C{?} 
        so that the result is still formatted/usable as a URL

        Handles Unicode by by converting it into url-encoded UTF8 bytes 
        (quote() defaults to encoding to UTF8)

        @param text: URI, as string or bytes object
        @returns: bytes if it was given bytes, str if given str        
    '''
    given_bytes = isinstance(text, bytes)
    if isinstance(text, str):
        text = text.encode('utf8')
    ret = urllib.parse.quote(text, b':/;?')
    if same_type and given_bytes:
        return bytes(ret,encoding='utf8')
    return ret


def uri_component(text, same_type=True):
    ''' Escapes for URI use:
        %-escapes everything (including C{/}) so that you can shove anything, 
        including URIs, into URI query parameters.

        @param text: URI, as string or bytes object
        (unicode in an input str is converted into url-encoded UTF8 bytes first (quote() defaults to encoding to UTF8))
        @returns: bytes if it was given bytes, str if given str. If same_type==false it gives it as a str always.
    '''
    given_bytes:bool = isinstance(text, bytes)

    if isinstance(text, str):
        text = text.encode('utf8')

    ret = urllib.parse.quote(text,b'')
    if same_type and given_bytes:
        return bytes(ret,encoding='utf8')
    return ret


def uri_dict(d, join='&', astype=str):
    ''' Returns a query fragment based on a dict.

        Handles Unicode input strings by converting it into url-encoded UTF8 bytes.

        return type is explicitly requested by you (use str or bytes), 
        not based on argument, as type variation within the dict could make that too magical

        join is there so that you could use ; as w3 suggests, but it defaults to &
        Internally works in str

        (you could also abuse it to avoid an attr()/nodetext() by handing it &amp; but that gets confusing)
    '''
    if isinstance(join, bytes):
        join = join.decode('utf8')   # this function itself works in str, and
    parts=[]
    for var in sorted( d.keys() ): # sorting is purely a debug thing
        val=d[var]
        if not isinstance(var, str): # TODO: rethink   (this is _mostly_ intended for a bytes, but this code is too broad)
            raise ValueError("uri_dict doesn't deal with type %r"%str(type(var)))
            #var = str(var)
        if not isinstance(val, str): # TODO: rethink: this may make sense for numbers, byte not e.g. bytes objects
            raise ValueError("uri_dict doesn't deal with type %r"%str(type(val)))
            #val = str(val)
        parts.append( '%s=%s'%(uri_component(var),
                               uri_component(val)) )
    if astype is bytes:
        return bytes( join.join(parts), encoding='ascii' )
    return astype( join.join(parts) )
