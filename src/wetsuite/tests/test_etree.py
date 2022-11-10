from wetsuite.helpers.etree import fromstring, tostring, strip_namespace, strip_namespace_inplace, all_text_fragments, indent, path_count, kvelements_to_dict


def test_strip():
    ''' Test some basic assumptions around strip_namespace() and strip_namespace_inplace()  '''
    original     = '<a xmlns:pre="foo"> <pre:b/> </a>'
    reserialized = '<a xmlns:ns0="foo"> <ns0:b /> </a>'
    no_ns        = '<a> <b /> </a>'

    tree = fromstring( original )
    assert tostring( tree ).decode('u8') in (original, reserialized)           # lxml seems to preserve prefixes, others do not, so either is good   (TODO: check)

    stripped = strip_namespace( tree )
    assert stripped.find('{foo}b') == None  and  stripped.find('b').tag == 'b' # test whether it actually stripped the namespaces

    assert tostring( tree ).decode('u8') in (original, reserialized)           # test whether deepcopy does what I think it does - whether the original tree is untouched

    strip_namespace_inplace(tree)

    assert tree.find('{foo}b') == None  and  tree.find('b').tag == 'b'         # test whether it alters in-place


def test_all_text_fragments():
    assert all_text_fragments( fromstring('<a>foo<b>bar</b></a>') ) == ['foo', 'bar']


def test_indent():
    xml = '<a xmlns:pre="foo"> <pre:b/> </a>'
    assert tostring( indent( fromstring(xml) ) ) == b'<a xmlns:pre="foo">\n  <pre:b/>\n</a>\n'
    

def test_pathcount():
    xml = '<a><b>><c/><c/><c/></b><d/><d/></a>'
    assert path_count( fromstring( xml ) ) == {'a': 1, 'a/b': 1, 'a/b/c': 3, 'a/d': 2}


def test_kvelements_to_dict():
    kvelements_to_dict( fromstring(
        '''<foo>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp/>
            </foo>''')) == {'identifier':'BWBR0001840', 'title':'Grondwet'}