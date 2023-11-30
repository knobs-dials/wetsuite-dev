import pytest

import wetsuite.datacollect.rechtspraaknl

import wetsuite.helpers.net
import wetsuite.helpers.etree



def test_value_list_parsing():
    ' test that these fetch-and-parse things do not bork out '
    wetsuite.datacollect.rechtspraaknl.parse_instanties()
    wetsuite.datacollect.rechtspraaknl.parse_instanties_buitenlands()
    wetsuite.datacollect.rechtspraaknl.parse_proceduresoorten()
    wetsuite.datacollect.rechtspraaknl.parse_rechtsgebieden()
    wetsuite.datacollect.rechtspraaknl.parse_nietnederlandseuitspraken()


def test_search():
    import datetime

    #yesterday_date = ( datetime.datetime.now() - datetime.timedelta(days=1) ).date()
    #yesterday_str  = yesterday_date.strftime('%Y-%m-%d')

    results = wetsuite.datacollect.rechtspraaknl.search( params=[
        ('max',  '5'), 
        ('return', 'DOC'),                                         # DOC asks for things with body text only
        #('modified', '2023-10-01'), ('modified', '2023-11-01')     # date range    (keep in mind that larger ranges easily means we hit the max)
        ('modified', '2023-11-01'),
    ] )

    assert len(results) > 0

    wetsuite.datacollect.rechtspraaknl.parse_search_results( results )

def test_parse():
    bytes = wetsuite.helpers.net.download('https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:GHARL:2022:7129')
    tree = wetsuite.helpers.etree.fromstring( bytes )
    results = wetsuite.datacollect.rechtspraaknl.parse_content( tree )

    bytes = wetsuite.helpers.net.download('https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:PHR:2022:255')
    tree = wetsuite.helpers.etree.fromstring( bytes )
    results = wetsuite.datacollect.rechtspraaknl.parse_content( tree )


def test_website_zoek():
    wetsuite.datacollect.rechtspraaknl.website_zoek('fork')