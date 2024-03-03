' tests related to ipyton/jupyter notebook code '
import time

import wetsuite.helpers.etree
from wetsuite.helpers.notebook import detect_env, is_interactive, is_ipython, is_notebook,  progress_bar, ProgressBar, etree_visualize_selection


def test_count_normalized():
    ' test that detect_env, well, detects the pyenv special case '
    d = detect_env()
    # from within pytest it's probably...
    assert d['ipython']     is False
    assert d['interactive'] is False
    assert d['notebook']    is False

    assert not is_ipython()
    assert not is_interactive()
    assert not is_notebook()


def test_progress_console():
    ' test that it does not bork out '
    pb = progress_bar(10)
    pb.value += 1
    pb.description = 'foo'



def test_progress_iter():
    ''' test that it iterates over various things,
        including things that have a length but are not subscriptable,
        and things have neither a length nor are subscribtable
    '''

    for _ in ProgressBar( [1,2,3,4] ):
        time.sleep(0.001)


    for _ in ProgressBar( set([1,2,3,4]) ):
        time.sleep(0.001)

    # dict views
    for _ in ProgressBar( {1:2, 3:4}.items() ):
        time.sleep(0.001)

    for _ in ProgressBar( {1:2, 3:4}.keys() ):
        time.sleep(0.001)

    for _ in ProgressBar( {1:2, 3:4}.values() ):
        time.sleep(0.001)


def test_progress_enum(): # TODO: figure out whether we want that
    for _ in ProgressBar( enumerate([5,6,7]) ):
        time.sleep(0.001)


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
    ' test that it does not bork out '
    etree_visualize_selection( b'<a><b/></a>', '//b' )
