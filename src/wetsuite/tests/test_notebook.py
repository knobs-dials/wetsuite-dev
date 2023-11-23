import wetsuite.helpers.etree
from wetsuite.helpers.notebook import etree_visualize_selection

def test_count_normalized():
    from wetsuite.helpers.notebook import detect_env, is_interactive, is_ipython, is_notebook

    d = detect_env() 
    # from within pytest it's probably...
    assert d['ipython']     == False
    assert d['interactive'] == False
    assert d['notebook']    == False

    assert not is_ipython()
    assert not is_interactive()
    assert not is_notebook()


def test_progress_console():
    from wetsuite.helpers.notebook import progress_bar

    pb = progress_bar(10)
    pb.value += 1
    pb.description = 'foo'


def test_etree_visualize_selection():
    ' testing that running it does not error out always '
    tree = wetsuite.helpers.etree.fromstring('<a><b c="d">e</b></a>')
    o = etree_visualize_selection( tree, '//b' )
    o._repr_html_()


def test_etree_visualize_selection_unusualnotes():
    ' testing that running it does not error out always '
    tree = wetsuite.helpers.etree.fromstring('<a><!-- --><b/>?<?foo ?></a>')
    o = etree_visualize_selection( tree, '//b', True, True, True, True )
    o._repr_html_()


def test_etree_visualize_selection_given():
    ' testing "highlight given elements" does not error out '
    tree = wetsuite.helpers.etree.fromstring('<a><b/></a>')
    o = etree_visualize_selection( tree, tree.findall('b') ) 
    o._repr_html_()
    o = etree_visualize_selection( tree, tree.find('b') ) 
    o._repr_html_()



def test_etree_visualize_selection_bytes():
    import wetsuite.helpers.etree
    from wetsuite.helpers.notebook import etree_visualize_selection
    etree_visualize_selection( b'<a><b/></a>', '//b' )
