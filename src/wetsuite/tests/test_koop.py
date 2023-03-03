import pytest

def test_cvdr_parse_identifier():
    from wetsuite.datacollect.koop_repositories import cvdr_parse_identifier

    assert cvdr_parse_identifier('101404_1')      ==  ('101404', '101404_1')
    assert cvdr_parse_identifier('CVDR101405_1')  ==  ('101405', '101405_1')
    assert cvdr_parse_identifier('CVDR101406')    ==  ('101406',  None     )
    assert cvdr_parse_identifier('1.0:101407_1')  ==  ('101407', '101407_1')

    assert cvdr_parse_identifier('101404_1',     prepend_cvdr=True)  ==  ('CVDR101404', 'CVDR101404_1')
    assert cvdr_parse_identifier('CVDR101405_1', prepend_cvdr=True)  ==  ('CVDR101405', 'CVDR101405_1')
    assert cvdr_parse_identifier('CVDR101406',   prepend_cvdr=True)  ==  ('CVDR101406',  None     )
    assert cvdr_parse_identifier('1.0:101407_1', prepend_cvdr=True)  ==  ('CVDR101407', 'CVDR101407_1')

    # TODO: check about possible edge cases, like leading zeroes


#def test_cvdr_param_parse():
#    pass

