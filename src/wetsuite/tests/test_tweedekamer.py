''' '''
import pytest
import wetsuite.datacollect.tweedekamer_nl

#def DISABLED_test_fetch_all():
def test_fetch_all():
    ' test that we can fetch and merge '
    #etrees = wetsuite.datacollect.tweedekamer_nl.fetch_all( 'Zaal') #, break_actually=True )
    etrees = wetsuite.datacollect.tweedekamer_nl.fetch_all( 'Zaal', break_actually=True )

    merged_tree = wetsuite.datacollect.tweedekamer_nl.merge_etrees( etrees )

    wetsuite.datacollect.tweedekamer_nl.entries( merged_tree )


# def test_fetch_resource():
#     ' test that '
#     with pytest.raises(ValueError, match=r'.*400.*'):
#         wetsuite.datacollect.tweedekamer_nl.fetch_resource('sdfsdf')

#     wetsuite.datacollect.tweedekamer_nl.fetch_resource('2d1a7837-c0c4-4971-9e32-feacaa50961b')
        
