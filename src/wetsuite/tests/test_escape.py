import pytest
from wetsuite.helpers.escape import nodetext, attr, uri, uri_component, uri_dict


def test_nodetext():
    ' see whether the "make text good to dump in a HTML/XML text node" works '
    assert nodetext(      'a < b "'                          ) ==   'a &lt; b "'
    assert nodetext(     b'a < b "'                          ) ==  b'a &lt; b "' 

    assert nodetext(   None, None ) ==  None
    assert nodetext(   None, '' )   ==  ''


def test_attr():
    ' see whether the "make text good to dump in a HTML/XML attribute" works '
    assert attr(          'a < b "'                          ) ==  'a &lt; b &#x22;'
    assert attr(         b'a < b "'                          ) == b'a &lt; b &#x22;'


def test_uri():
    ' ' 
    assert uri(          b'http://example.com:8080/foo#bar') ==  b'http://example.com:8080/foo%23bar'
    assert uri(           'http://example.com:8080/foo#bar') ==  'http://example.com:8080/foo%23bar'


def test_uri_component():
    ' test the "percent-escape most of the things in a string" function'
    assert uri_component(b'http://example.com:8080/foo#bar') == b'http%3A%2F%2Fexample.com%3A8080%2Ffoo%23bar'
    assert uri_component( 'http://example.com:8080/foo#bar') == 'http%3A%2F%2Fexample.com%3A8080%2Ffoo%23bar'


def test_uri_dict():
    ' test "make dict into percent-escaped string" function'

    assert uri_dict({'name':'Zim', 'chr':u'\u2222'}, astype=str)              ==  'chr=%E2%88%A2&name=Zim'
    assert uri_dict({'name':'Zim', 'chr':u'\u2222'}, astype=bytes)            == b'chr=%E2%88%A2&name=Zim'
    assert uri_dict({'name':'Zim', 'chr':u'\u2222'}, join=b';', astype=str)   ==  'chr=%E2%88%A2;name=Zim'
    assert uri_dict({'name':'Zim', 'chr':u'\u2222'}, join=';',  astype=str)   ==  'chr=%E2%88%A2;name=Zim'

    with pytest.raises(ValueError, match=r'.*type.*'):
        uri_dict({'w':b'ytes'})   ==  'u=3&v=True'

    with pytest.raises(ValueError, match=r'.*type.*'):
        uri_dict({b'ytes':'w'})   ==  'u=3&v=True'

    # CONSIDER: more things it should probably fail on


    
