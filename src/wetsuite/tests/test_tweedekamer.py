''' '''

import wetsuite.datacollect.tweedekamer_nl

def test_fetch():
    etrees = wetsuite.datacollect.tweedekamer_nl.fetch_all( 'Zaal' )

    merged_tree = wetsuite.datacollect.tweedekamer_nl.merge_etrees( etrees )