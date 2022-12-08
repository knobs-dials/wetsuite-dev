#!/usr/bin/python3
""" Escaping text for different contexts, mostly HTML/XML.

    Should make code more readable (than combinations of cgi.escape(), urllib.quote(), ''.encode() and such)

    Note that in HTML, & should always be encoded (in node text, attributes and elsehwere),
    so it is a good idea to structurally use nodetext() and/or attr(). 
    ...or use a templating library that does this for you.

    uri() and uri_component() are like javascript's encodeURI and encodeURIcomponent.
"""
#import html, re
import urllib.parse

__all__ = ['nodetext','attr', 'uri','uri_component','uri_dict']



def nodetext(s, if_none=None):
    ''' Escapes for HTML/XML text nodes:
        Replaces <, >, and & with entities
        
        Passes unicode through
         and always returns a str, even if given a bytes

        (is actually html.escape (previously known as cgi.escape)
    '''
    if s is None:
        return if_none

    if type(s) is bytes:
        ret = s.replace(  b"&",  b"&amp;")   
        ret = ret.replace(b"<",  b"&lt;")
        ret = ret.replace(b">",  b"&gt;")
    else:
        ret = s.replace(   "&",  "&amp;")
        ret = ret.replace( "<",  "&lt;")
        ret = ret.replace( ">",  "&gt;")
    return ret


def attr(s): 
    ''' Escapes for use in HTML(/XML) node attributes:
        Replaces <, >, &, ', " with entities

        Returns
          bytes if it was given bytes
          str if given str

        Much like html.escape, but...
        - ' and " to numeric entitities (&#x27;, &#x22;)         
            (...and not &quot; for "  because that's not quite universal)
          
        - Escapes ' (which html.escape doesn't) which you often don't need,
          but do if you wrap attributes in ' which is valid in XML, various HTML. 
          Doesn't use apos becase it's not defined in HTML4

        Note that to put URIs with unicode in attributes, what you want is often something roughly like
        '<a href="?q=%s">'%attr( uri_component(q)  )
        because uri handles the utf8 percent escaping of the unicode, attr() the attribute escaping
        (technically you can get away without attr because uri_component escapes a _lot_ )


        TODO: review how I want to deal with bytes / unicode in py3 now


        Passes non-ascii through. It is expected that you want to apply that to the document as a whole, or to document writing/appending.
    '''
    if type(s) is bytes:
        ret = s.replace(  b"&",  b"&amp;")   
        ret = ret.replace(b"<",  b"&lt;")
        ret = ret.replace(b">",  b"&gt;")
        ret = ret.replace(b'"',  b'&#x22;')
        ret = ret.replace(b'\'', b"&#x27;")
    else:
        ret = s.replace(   "&",  "&amp;")
        ret = ret.replace( "<",  "&lt;")
        ret = ret.replace( ">",  "&gt;")
        ret = ret.replace( '"',  '&#x22;') 
        ret = ret.replace( '\'', "&#x27;")
    return ret


def uri(uri, same_type=True):
    ''' Escapes for URI use
        %-escapes everything except ':', '/', ';', and '?' so that the result is still formatted/usable as a URL

        Returns
          bytes if it was given bytes
          str if given str
        
        Handles Unicode by by converting it into url-encoded UTF8 bytes (quote() defaults to encoding to UTF8)
    '''
    given_bytes = type(uri) is bytes
    if type(uri) is str: 
        uri = uri.encode('utf8')
    ret = urllib.parse.quote(uri,b':/;?')
    if same_type and given_bytes:
        return bytes(ret,encoding='utf8')
    return ret
        

def uri_component(uri, same_type=True):
    ''' Escapes for URI use
        %-escapes everything (including '/') so that you can shove anything, including URIs, into URL query parameters

        Returns
          bytes if it was given bytes
          str if given str

        If given unicode, converting it into url-encoded UTF8 bytes first (quote() defaults to encoding to UTF8)
    '''
    given_bytes = type(uri) is bytes
    if type(uri) is str: #py3 only
        uri = uri.encode('utf8')

    ret = urllib.parse.quote(uri,b'')
    if same_type and given_bytes:
        return bytes(ret,encoding='utf8')
    return ret


def uri_dict(d, join='&', astype=str):
    ''' returns a query fragment based on a dict.

        Handles Unicode by by converting it into url-encoded UTF8 bytes.

        return type is explicit (use str or bytes), 
           not based on argument as type variation within the dict could make that too magical

        join is there so that you could use ; as w3 suggests.
        Internally works in str

        (you could also abuse it to avoid an attr()/nodetext() by handing it &amp; but that gets confusing)
    '''
    if type(join) is bytes:
        join = join.decode('u8') # this function itself works in str, and  

    parts=[]
    for var in sorted( d.keys() ): #sorting is purely a debug thing
        val=d[var]
        if type(var) is not str: # TODO: rethink   (this is _mostly_ intended for a bytes, but this code is too broad)
            raise ValueError("uri_dict doesn't deal with type %r"%str(type(var)))
            #var = str(var)
        if type(val) is not str: # TODO: rethink: this may make sense for numbers, byte not e.g. bytes objects
            raise ValueError("uri_dict doesn't deal with type %r"%str(type(val)))
            #val = str(val)      
        parts.append( '%s=%s'%(uri_component(var),
                               uri_component(val)) )
    if astype is bytes:
        return bytes( join.join(parts), encoding='ascii' )
    return astype( join.join(parts) )

