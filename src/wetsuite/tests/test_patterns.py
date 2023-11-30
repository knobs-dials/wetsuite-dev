
from wetsuite.helpers.patterns import find_identifier_references, find_nonidentifier_references


def test_reference_parse():
    import datetime, pytest

    matches = find_nonidentifier_references('artikel 5:9, aanhef en onder b, Awb')
    d = matches[0]['details']
    assert d['artikel'] == '5:9'


    matches = find_nonidentifier_references('artikel 4, tweede lid, aanhef en onder d, van het reglement van orde voor de ministerraad')
    d = matches[0]['details']
    assert d['artikel'] == '4'
    assert 'tweede' in d['lid']
    assert 2 in d['lid_num']
    assert d['aanhefonder'] == 'aanhef en onder d'

    #with pytest.raises(ValueError, match=r'.*of type.*'):
    #    date_range( (2022,1,1), (2022,1,1) )



# def test_cleanup_basics():
#     # some "are those helper functions roughly working at all" tests?
#     assert cleanup_basics( 'artikel 2.1 Wet ruimtelijke ordening' )              == 'Wet ruimtelijke ordening'

#     assert cleanup_basics( 'artikel 10.23, eerste lid van de Wet milieubeheer' ) == 'Wet milieubeheer'

#     assert name_from_extref_tag( 
#         wetsuite.helpers.etree.fromstring(
#         '<extref doc="http://wetten.overheid.nl/cgi-bin/deeplink/law1/title=Wet%20milieubeheer/article=10.23" struct="BWB">artikel 10.23, eerste lid van de Wet milieubeheer</extref>' 
#         )
#         ) == 'Wet milieubeheer'





def test_identifier_parse():
    ' find each type in isolation '

    for test_string, expect in (
        ('asdf ECLI:NL:CBB:1996:ZG0749 asdf'         , {'type':'ecli',         'text':'ECLI:NL:CBB:1996:ZG0749'}),
        ('asdf Stb. 2005 asdf'                       , {'type':'vindplaats',   'text':'Stb. 2005'     } ),
        ('asdf 33684R2020 asdf'                      , {'type':'celex',        'text':'33684R2020'    } ),
        ('asdf Trb.\xa01966 asdf'                    , {'type':'vindplaats',   'text':'Trb.\xa01966'  } ),
        ('asdf Trb. 1966, 91 asdf'                   , {'type':'vindplaats',   'text':'Trb. 1966, 91' } ),
        ('asdf Kamerstukken II 1992/1993, 22 asdf'   , {'type':'kamerstukken', 'text':'Kamerstukken II 1992/1993, 22'} ),
        ('asdf BB7360 asdf'                          , {'type':'ljn',          'text':'BB7360'        } ),
        #('asdf BB 7360 asdf'                         , {'type':'ljn',          'text':'BB 7360'       } ),
        # TODO: complete

        #('asdf Stb 2005 asdf'                       ),
        #('asdf Kamerstukken 1992/1993, 22 asdf'     ),        
    ):

        found = find_identifier_references( test_string, 
            ljn=True, ecli=True, celex=True, kamerstukken=True, vindplaatsen=True, nonidentifier=True, euoj=True, eudir=True
        )
        for key, value in expect.items():
            assert found[0].get( key ) == value

def test_identifier_almost():
    ' test that it does not accept things that are close but not quite '
    for test_string in (
        ('asdf 3684R2020 asdf'                      ),
        #('asdf ECLI:N:CBB:1996:ZG0749 asdf'         ), # 
        
    ):

        assert len( find_identifier_references( test_string, 
            ljn=True, ecli=True, celex=True, kamerstukken=True, vindplaatsen=True, nonidentifier=True, euoj=True, eudir=True
        ) ) == 0




for test in [
    #'artikel 4, tweede lid, aanhef en onder d, van het reglement van orde voor de ministerraad                     ', 
    #'artikel 4, tweede lid, onder d, van het reglement                     ', 
    #'artikel 2, lid 1                   ',
    #'artikel 2, lid\n1                   ',
    #'artikel 2, eerste\nlid               ',
    #'artikel 2, eerste lid                 ',
    'artikel 2, eerste en vijfde lid        ',
    #'artikel 2, eerste, tweede, en vijfde lid',

    'artikel 5:9, aanhef en onder b, Awb',
    'artikel 8, aanhef en onder c, Wet bescherming persoonsgegevens (Wbp).'
    'artikel 10, tweede lid, aanhef en onder e, van de Wob',
    "artikel 4, tweede lid, aanhef en onder d, van het reglement van orde voor de ministerraad",
    "artikel 2, eerste, tweede, vijfde, even zesenzestigste lid",
    "Artikel 10, tweede lid, aanhef en onder e van de. Wet openbaarheid van bestuur",
    "artikel 6:80 lid 1 aanhef en onder b BW",
    'artikel 142, eerste lid, aanhef en onder b (en derde lid), van het Wetboek van Strafvordering',
    'artikel 4, aanhef en onder d en g, van de standaardvoorwaarden',
    'artikel 3.3, zevende lid, aanhef en onder i, Woo',
    'artikel 3.3, zevende lid jo. vijfde lid, aanhef en onder i, Woo',
    'artikel 79, aanhef en onder 6\xBA',
    'artikel 15, aanhef en onder a of c (oud) RWN',
    'Wabo, art. 2.12, eerste lid, aanhef en onder a, sub 1\xBA',
    'artikel 4:25, 4:35 van de Awb en artikel 10 van de ASV'

    # Note that these can be references to "gelet op" (Intitule) begipsbepalingen - e.g. the last (from CVDR662488/1) doesn't strictly _define_ Awb or ASV, but 
    #  of the options of lines like "artikel 5 van de Tijdelijke aanvulling Algemene subsidieverordening Hoeksche Waard 2020" we can pick a probably option.

]:
    find_nonidentifier_references( test )