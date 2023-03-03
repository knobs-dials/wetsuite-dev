from wetsuite.helpers.shellcolor import *
from wetsuite.helpers.shellcolor import _percent_parse
    
def test_color_degree():
    guess_color_support(True, True, True)
    assert( color_degree('foo', 0,0,100) ) == '\x1b[1;30mfoo\x1b[0m\x1b[39m'
    assert( color_degree('bar', 30,0,100) ) == '\x1b[37mbar\x1b[0m\x1b[39m'


def test_percent_parse():
    assert _percent_parse(' a  %%  qq  %.5d %30s  % -31.7f ', [0,0,5,9]) == ' a  %%  qq  %.5d %35s  % -40.7f '


def test_cformat():
    assert cformat('%20s', (WHITE+'fork'+RESET,) ) == '                \x1b[1;37mfork\x1b[0m\x1b[39m'


def test_real_len():
    assert real_len( '\x1b[1;30mfoo\x1b[0m\x1b[39m')[0] == 3
    assert real_len( '\x1b[37mbar\x1b[0m\x1b[39m')[0]   == 3

# TODO: test closest_from_rgb255, _format_segment, truncate_real_len, true_colf, redgreen, hash_color