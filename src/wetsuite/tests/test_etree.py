' test etree / lxml related functions '
import pytest
from wetsuite.helpers.etree import fromstring, tostring, strip_namespace, _strip_namespace_inplace, all_text_fragments
from wetsuite.helpers.etree import indent, path_count, kvelements_to_dict, path_between


def test_strip():
    ''' Test some basic assumptions around strip_namespace() and strip_namespace_inplace()  '''
    original     = '<a xmlns:pre="foo"> <pre:b/> </a>'
    reserialized = '<a xmlns:ns0="foo"> <ns0:b /> </a>'

    tree = fromstring( original )

    # lxml seems to preserve prefix strings, others do not, so either is good   (TODO: check)
    assert tostring( tree ).decode('u8') in (original, reserialized)

    # test whether it actually stripped the namespaces
    stripped = strip_namespace( tree )
    assert stripped.find('{foo}b') is None  and  stripped.find('b').tag == 'b'

    # test whether deepcopy does what I think it does - whether the original tree is untouched
    assert tostring( tree ).decode('u8') in (original, reserialized)

    _strip_namespace_inplace( tree )

    # back and forth to remove any difference in serialization
    assert tostring(tree) == tostring(fromstring(b'<a> <b/> </a>'))
    # and test _that_ assumption too
    assert tostring(tree) == tostring(fromstring(b'<a> <b /> </a>'))

    # test whether it alters in-place
    assert tree.find('{foo}b') is None  and  tree.find('b').tag == 'b'



def test_attribute_stripping():
    ' test that namespaces are aolso stripped from attribute names '
    with_attr = fromstring( '<a xmlns:pre="foo"> <b pre:at="tr"/> </a>' )
    _strip_namespace_inplace( with_attr )
    assert tostring(with_attr) == b'<a> <b at="tr"/> </a>'


def test_comment_robustness():
    " tests whether we're not assuming the only node type is element "
    _strip_namespace_inplace( fromstring('<a> <b /><!--comment--> </a>') )


def test_processing_instruction_robustness():
    ''' test that we do not trip over processing instructions 
        note: apparently an initial <?xml doesn't count as a processing expression
    '''
    _strip_namespace_inplace( fromstring(b'<a><?xml-stylesheet type="text/xsl" href="style.xsl"?></a>') )


def test_strip_default():
    ' test strip_namespace with defaults'
    withns1    = b'<a xmlns="foo"><b/></a>'
    withns2    = b'<a><b xmlns="foo"/></a>'
    withoutns  = b'<a><b/></a>'

    to1 = tostring( strip_namespace( fromstring( withns1 ) ) )
    to2 = tostring( strip_namespace( fromstring( withns2 ) ) )
    assert to1 == withoutns
    assert to2 == withoutns


def test_all_text_fragments():
    ' test all_text_fragments function'
    assert all_text_fragments( fromstring('<a>foo<b>bar</b>quu</a>') )                    == ['foo', 'bar', 'quu']

    # rather than a '', is expected behaviour.
    assert all_text_fragments( fromstring('<a>foo<b></b>quu</a>'))                        == ['foo', 'quu']

    assert all_text_fragments( fromstring('<a>foo<b> </b>quu</a>'))                       == ['foo', '', 'quu']
    assert all_text_fragments( fromstring('<a>foo<b> </b>quu</a>'), ignore_empty=True)    == ['foo', 'quu']

    assert all_text_fragments( fromstring('<a>foo<b>bar</b>quu</a>'), ignore_tags=['b'] ) == ['foo', 'quu']

    assert all_text_fragments( fromstring('<a>foo<b>bar</b>quu</a>'), join=' ' )          == 'foo bar quu'


def test_indent():
    ' test reindenting '
    xml = '<a xmlns:pre="foo"> <pre:b/> </a>'
    assert tostring( indent( fromstring(xml) ) ) == b'<a xmlns:pre="foo">\n  <pre:b/>\n</a>\n'


def test_pathcount():
    ' test the path counting '
    xml = '<a><b>><c/><c/><c/></b><d/><d/></a>'
    assert path_count( fromstring( xml ) ) == {'a': 1, 'a/b': 1, 'a/b/c': 3, 'a/d': 2}


def test_kvelements_to_dict():
    ' test kv_elements_to_dict() basically works '

    assert kvelements_to_dict(
        fromstring(
        '''<foo>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp/>
           </foo>''')) == {'identifier':'BWBR0001840', 'title':'Grondwet'}

    assert kvelements_to_dict( fromstring(
        '''<foo>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp>ignore me</onderwerp>
           </foo>'''), ignore_tagnames=['onderwerp'] ) == {'identifier':'BWBR0001840', 'title':'Grondwet'}



def test_nonlxml():
    ' ? '
    # see also https://lxml.de/compatibility.html
    import xml.etree.ElementTree

    # the test is whether it warns, but doesn't crash
    with pytest.warns(UserWarning, match=r'.*lxml.*'):
        strip_namespace( xml.etree.ElementTree.fromstring(b'<a><?xml-stylesheet type="text/xsl" href="style.xsl"?></a>') )


def test_path_between():
    ' test that path_between basically works '
    xml = '<a><b><c><d/><d/></c><d/></b></a>'
    a = fromstring(xml)
    c = a.find('b/c')
    d0 = c.getchildren()[0]
    d1 = c.getchildren()[1]
    assert path_between(a, d0) == '/a/b/c/d[1]'
    assert path_between(a, d1) == '/a/b/c/d[2]'


def test_path_between_elsewhere():
    xml = '<a><b><c><d/><d/></c><d/></b></a>'
    a = fromstring(xml)

    with pytest.raises(ValueError, match=r'.*Element is not in this tree.*'):
        path_between(a, fromstring(xml)) # new parse is not in the same tree

    # TODO: decide what to do when they're in the same tree but not the way around that you expect
    #with pytest.raises(ValueError, match=r'.*.*'):
    #assert path_between(d1, a)


    #wetsuite.helpers.etree.path_between(tree, body.xpath('//al')[10]) == '/cvdr/body/regeling/regeling-tekst/artikel[1]/al[1]'
