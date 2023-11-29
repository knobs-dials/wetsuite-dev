''' Testing koop_parse and koop_repositories modules '''
import os

import pytest

from wetsuite.helpers.koop_parse import cvdr_parse_identifier, cvdr_meta, cvdr_text, cvdr_sourcerefs, cvdr_param_parse, cvdr_normalize_expressionid
from wetsuite.datacollect.koop_repositories import BWB, CVDR
import wetsuite.helpers.etree


def test_koop_repositories():
    ' mostly just that that they construct fine '
    BWB()
    CVDR()
    # SamenwerkendeCatalogi
    # LokaleBekendmakingen
    # LokaleBekendmakingen
    # TuchtRecht
    # WetgevingsKalender
    # PLOOI
    # PUCOpenData
    # EuropeseRichtlijnen



def test_cvdr_parse_identifier():
    ' test cvdr_parse_identifier basics '
    assert cvdr_parse_identifier('101404_1')      ==  ('101404', '101404_1')
    assert cvdr_parse_identifier('CVDR101405_1')  ==  ('101405', '101405_1')
    assert cvdr_parse_identifier('CVDR101406')    ==  ('101406',  None     )
    assert cvdr_parse_identifier('1.0:101407_1')  ==  ('101407', '101407_1')

    assert cvdr_parse_identifier('101404_1',     prepend_cvdr=True)  ==  ('CVDR101404', 'CVDR101404_1')
    assert cvdr_parse_identifier('CVDR101405_1', prepend_cvdr=True)  ==  ('CVDR101405', 'CVDR101405_1')
    assert cvdr_parse_identifier('CVDR101406',   prepend_cvdr=True)  ==  ('CVDR101406',  None     )
    assert cvdr_parse_identifier('1.0:101407_1', prepend_cvdr=True)  ==  ('CVDR101407', 'CVDR101407_1')

    # TODO: check about possible edge cases, like leading zeroes


def test_cvdr_param_parse():
    res = cvdr_param_parse('BWB://1.0:c:BWBR0008903&artikel=12&g=2011-11-08')
    assert res['artikel'] == ['12']
    assert res['g']       == ['2011-11-08']

    #TODO: bad amp parse


def get_test_data(fn):
    ' open a test file placed in the test directory - probably works unless something is being very protective '
    import test_koop  # that's intentional pylint: disable=W0406
    file = open( os.path.join( os.path.dirname( test_koop.__file__ ), fn), mode='rb' )
    filedata = file.read()
    file.close()
    return filedata


def get_test_etree(fn):
    ' read test data with read_testdata(), parse and return as etree object'
    return wetsuite.helpers.etree.fromstring( get_test_data(fn) )

# TODO: find example with different types of sourcerefs 

# just many is e.g.
# New best: 14 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/101112/2/xml/101112_2.xml'
# New best: 17 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR10324/2/xml/CVDR10324_2.xml'
# New best: 25 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR116909/2/xml/CVDR116909_2.xml'
# New best: 49 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR122433/2/xml/CVDR122433_2.xml'
# New best: 59 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR603481/2/xml/CVDR603481_2.xml'
# New best: 62 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR645418/1/xml/CVDR645418_1.xml'


def test_cvdr_normalize_expressionid():
    assert cvdr_normalize_expressionid('CVDR112779_1') == 'CVDR112779_1'
    assert cvdr_normalize_expressionid('112779_1')     == 'CVDR112779_1'
    with pytest.raises(ValueError, match=r'.*expression.*'):
        assert cvdr_normalize_expressionid('112779')     == 'CVDR112779'


def test_cvdr_meta():
    ' test cvdr_meta, mostly just for not borking out immediately '
    tree = get_test_etree( 'cvdr_example1.xml' )

    meta = cvdr_meta(tree)
    assert isinstance( meta['issued'], list ) # i.e. not flattened

    meta = cvdr_meta(tree, flatten=True)
    assert meta['identifier'] == '112779_1' # a value as expected  TODO: check that we normalize this?




def test_cvdr_text():
    ' test cvdr_text, currently just for not borking out immediately '
    tree = get_test_etree( 'cvdr_example1.xml' )
    cvdr_text(tree)



def test_cvdr_sourcerefs():
    ' test cvdr_text, currently just for not borking out immediately '
    tree = get_test_etree('cvdr_example1.xml')
    cvdr_sourcerefs(tree)

    tree = get_test_etree('cvdr_example2.xml')
    cvdr_sourcerefs(tree)


def test_search_related_parsing():
    ' do a bunch of search related parsing '
    # CONSIDER: currently based on an actual search - TODO: fetch a triple of XML files to not rely on taht
    import wetsuite.datacollect.koop_repositories
    from wetsuite.helpers.net import download
    from wetsuite.helpers.etree import fromstring
    bwb_sru =  wetsuite.datacollect.koop_repositories.BWB()
    for record in bwb_sru.search_retrieve('dcterms.identifier = BWBR0045754'):
        search_meta = wetsuite.helpers.koop_parse.bwb_searchresult_meta( record )


def test_more_parsing():
    ' do a bunch of search related parsing '
    # CONSIDER: currently based on an actual search - TODO: fetch a triple of XML files to not rely on taht
    # import wetsuite.datacollect.koop_repositories
    # from wetsuite.helpers.net import download
    # from wetsuite.helpers.etree import fromstring
    # bwb =  wetsuite.datacollect.koop_repositories.BWB()
    # for record in bwb.search_retrieve('dcterms.identifier = BWBR0045754'):
    #     search_meta = wetsuite.helpers.koop_parse.bwb_searchresult_meta( record )
    
    # test case is BWBR0045754
    toe_etree = get_test_etree('bwb_toestand.xml')
    toe_usefuls = wetsuite.helpers.koop_parse.bwb_toestand_usefuls( toe_etree )
    toe_text    = wetsuite.helpers.koop_parse.bwb_toestand_text(    toe_etree )
        
    wti_etree = get_test_etree('bwb_wti.xml')
    wti_usefuls = wetsuite.helpers.koop_parse.bwb_wti_usefuls(      wti_etree )

    man_etree = get_test_etree('bwb_manifest.xml')
    man_usefuls = wetsuite.helpers.koop_parse.bwb_manifest_usefuls( man_etree )

    merged = wetsuite.helpers.koop_parse.bwb_merge_usefuls(toe_usefuls, wti_usefuls, man_usefuls)



#alineas_with_selective_path



# TODO:
# bwb_searchresult_meta

# bwb_toestand_usefuls

# bwb_wti_usefuls

# cvdr_versions_for_work


# alineas_with_selective_path

# merge_alinea_data

# merge_alinea_data
