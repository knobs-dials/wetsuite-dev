#!/usr/bin/python3
'''
Fetches data from rechtspraak.nl's API

Note that the data.rechtspraak.nl/uitspraken/zoeken API is primarily for ranges - 
they do _not_ seem to allow text searches like the web interface does.

https://www.rechtspraak.nl/Uitspraken/paginas/open-data.aspx


If you want to save time, and server load for them, you would probably start with fetching OpenDataUitspraken.zip via
https://www.rechtspraak.nl/Uitspraken/paginas/open-data.aspx and inserting those so you can avoid 3+ million fetches.


There is an API at https://uitspraken.rechtspraak.nl/api/zoek that backs the website search
I'm not sure whether we're supposed to use it like this, but it's one of the better APIs I've seen in this context :)
'''

import json
import re
import urllib.parse

import requests

import wetsuite.helpers.net
import wetsuite.helpers.etree
import wetsuite.helpers.escape
import wetsuite.helpers.koop_parse


BASE_URL = "https://data.rechtspraak.nl/"
' base URL for search as well as value lists '

def search(params):
    ''' 
    Post a search to the public API on data.rechtspraak.nl,
    based on a dict of parameters.

    See also:
      - https://www.rechtspraak.nl/SiteCollectionDocuments/Technische-documentatie-Open-Data-van-de-Rechtspraak.pdf

    Note that when when you give it nonsensical parameters, like date=2022-02-30, 
    the service won't return valid XML, so the XML parse raises an exception.

    @param params: parameters like:
      -  max       (default is 1000)
      -  from      zero-based, defaults is 0
      -  sort      by modification date, ASC (default, oldest first) or DESC

      -  type      'Uitspraak' or 'Conclusie'
      -  date      yyyy-mm-dd              (once for 'on this date',        twice for a range)
      -  modified  yyyy-mm-ddThh:mm:ss     (once for a 'since then to now', twice for a range)
      -  return    DOC for things where there are documents; if omitted it also fetches things for which there is only metadata

      -  replaces  fetch ECLI for an LJN

      -  subject   URI of a rechtsgebied
      -  creator   
    These are handed to urlencode, so could be either a list of tuples, or a dict,
    but because you are likely to repeat variables to specify ranges, 'list of tuples' should be your habit, e.g.::
        [ ("modified", "2023-01-01), ("modified", "2023-01-05) ]

    @return:  etree object for the search (or raises an exception)
    CONSIDER: returning only the urls

    '''
    # constructs something like 'http://data.rechtspraak.nl/uitspraken/zoeken?type=conclusie&date=2011-05-01&date=2011-05-30'
    url = urllib.parse.urljoin(BASE_URL, "/uitspraken/zoeken?"+urllib.parse.urlencode(params))
    print( url )
    results = wetsuite.helpers.net.download( url )
    tree = wetsuite.helpers.etree.fromstring( results )
    return tree



def parse_search_results(tree):
    ''' Takes search result etree (as given by search()), and returns a list of dicts like::
            {      'ecli': 'ECLI:NL:GHARL:2022:7129',
                  'title': 'ECLI:NL:GHARL:2022:7129, Gerechtshof Arnhem-Leeuwarden, 16-08-2022, 200.272.381/01',
                'summary': 'some text made shorter for this docstring example',
                'updated': '2023-01-01T13:29:23Z',
                   'link': 'https://uitspraken.rechtspraak.nl/InzienDocument?id=ECLI:NL:GHARL:2022:7129',
                    'xml': 'https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:GHARL:2022:7129',
            }
        Notes: 
          - 'xml' is augmented based on the ecli and does not come from the search results
          - keys may be missing (in practice probably just summary?)
    '''
    tree = wetsuite.helpers.etree.strip_namespace(tree)
    # tree.find('subtitle') # its .text will be something like 'Aantal gevonden ECLI's: 3178259'
    ret = []
    for entry in tree.findall('entry'):
        entry_dict = {#'links':[]
                      }
        for ch in entry.getchildren():
            if ch.tag=='id':
                entry_dict['ecli'] = ch.text
                entry_dict['xml'] = 'https://data.rechtspraak.nl/uitspraken/content?id='+ch.text
            elif ch.tag=='title':
                entry_dict['title'] = ch.text
            elif ch.tag=='summary':
                txt = ch.text
                if txt!='-':
                #    txt = ''
                    entry_dict['summary'] = txt
            elif ch.tag=='updated':
                entry_dict['updated'] = ch.text
            elif ch.tag=='link':
                entry_dict['link'] = ch.get('href')
                #entry_dict['links'].append( ch.get('href') ) # maybe also type?
            else: # don't think this happens, but it'd be good to know when it does.
                raise ValueError( "Don't understand tag %r"%wetsuite.helpers.etree.tostring(ch) )
        ret.append( entry_dict )
    return ret


def _para_text(treenode):
    ' TODO: '
    ret = []

    for ch in treenode.getchildren():

        if isinstance(ch, (wetsuite.helpers.etree._Comment, wetsuite.helpers.etree._ProcessingInstruction)):
            continue
        
        if ch.tag in ('para', 'title', 'bridgehead', 'nr',
                      'footnote', 'blockquote'):
            if len( ch.getchildren() )>0:
                # HACK: just assume it's flattenable
                ret.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
                #raise ValueError("para has children")
            else:
                if ch.text is None:
                    ret.append('')
                else:
                    ret.append(ch.text)


        elif ch.tag in ('orderedlist','itemizedlist'):
            ret.append('')
            ret.extend(_para_text(ch))
            ret.append('')

        elif ch.tag in ('listitem',):
            ret.append('')
            ret.extend(_para_text(ch))
            ret.append('')


        elif ch.tag in ('informaltable', 'table'):
            ret.append('')
            # HACK: just pretend it's flattenable
            ret.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
            ret.append('')
        #elif ch.tag in ('tgroup','colspec','tobody','row','entry',''):
        #    ret.append('')
        #    ret.append(_para_text(ch))
        #   ret.append('')


        elif ch.tag in ('mediaobject','inlinemediaobject','imageobject', 'imagedata'):
            pass

        elif ch.tag =='uitspraak.info':
            #TODO: parse this
            pass
        elif ch.tag =='conclusie.info':
            #TODO: parse this
            pass

        elif ch.tag =='section':
            ret.append('')
            ret.extend(_para_text(ch))
            ret.append('')

        elif ch.tag =='parablock':
            ret.append('')
            ret.extend(_para_text(ch))
            ret.append('')

        elif ch.tag =='paragroup':
            ret.append('')
            ret.extend(_para_text(ch))
            ret.append('')

        else:
            raise ValueError("Do not understand tag name %r"%ch.tag)


    return ret # '\n'.join( ret )


    # # we try to abuse our own
    # alinea_data = wetsuite.helpers.koop_parse.alineas_with_selective_path( tree, alinea_elemname='para' )
    # #pprint.pprint(alinea_data)
    # merged = wetsuite.helpers.koop_parse.merge_alinea_data( alinea_data ) # TODO: explicit if_same ?
    # #pprint.pprint(merged)
    # return merged

    # for elem in tree.getchildren():
    #     if elem.tag == 'para':
    #         if elem.text is not None:
    #             ret.append( elem.text )
    #         pass
    #     elif elem.tag == 'parablock':
    #         #print('parablock')
    #         pbtext = []
    #         for chelem in elem.getchildren():
    #             if elem.tag == 'para':
    #                 pbtext.append( elem.text )
    #         if len(pbtext)>0:
    #             ret.append( pbtext )
    #     else:
    #         raise ValueError("Don't know element %r"%elem.tag)

    # return ret


def parse_content(tree):
    '''
    Parse the type of XML you get when you stick an ECLI onto  https://data.rechtspraak.nl/uitspraken/content?id=
    and tries to give you metadata and text. 
    CONSIDER: separating those

    @return: a dict with TODO
        
    TODO: actually read the schema - see https://www.rechtspraak.nl/Uitspraken/paginas/open-data.aspx
    '''
    ret = {}
    tree = wetsuite.helpers.etree.strip_namespace( tree )

    for descr in tree.findall('RDF/Description'): # TODO: figure out why there are multiple
        for key in ('identifier', 'issued', 'publisher', 'replaces', 'date', 'type',  # maybe make this a map so we can give it better names
                    #'format', 'language',
                    'modified',
                    'zaaknummer', 
                    'title', 
                    'creator', 'subject',

                    # TODO: inspect to see whether they need specialcasing. And in general which things can appear multiple times
                    'spatial',
                    #'procedure', # can have multiple

                    ):
            kelem = descr.find(key)
            if kelem is not None:
                ret[key] = kelem.text

        # things where we want attributes
        #creator, subject, relation

        # other specific cases
        #hasVersion

        break # for now assume that the most recent update (RDF/Description block) is the first, and the most detailed

    #for elem in list(RDF):
    #    print( wetsuite.helpers.etree.debug_pretty(elem))
    #ret['identifier'] = RDF.find

    inhoudsindicatie = tree.find('inhoudsindicatie')
    if inhoudsindicatie is not None:
        ret['inhoudsindicatie'] = re.sub(  '[\n]{2,}','\n\n',   '\n'.join( _para_text( inhoudsindicatie ) )  )

    conclusie = tree.find('conclusie')
    if conclusie is not None:
        ret['conclusie'] = re.sub(  '[\n]{2,}','\n\n',   '\n'.join( _para_text( conclusie ) )  )
        #_, t = _para_text( uitspraak )
        #ret['conclusie'] = ' '.join(t)

    uitspraak = tree.find('uitspraak')
    if uitspraak is not None:
        ret['uitspraak'] = re.sub(  '[\n]{2,}','\n\n',   '\n'.join( _para_text( uitspraak ) )  )
        #_, t = _para_text( uitspraak )
        #ret['uitspraak'] = ' '.join(t)

    return ret




## fetch and parse waardelijsten

_INSTANTIES_URL                = urllib.parse.urljoin(BASE_URL, "/Waardelijst/Instanties")
_INSTANTIES_BUITENLANDS_URL    = urllib.parse.urljoin(BASE_URL, "/Waardelijst/InstantiesBuitenlands")
_RECHTSGEBIEDEN_URL            = urllib.parse.urljoin(BASE_URL, "/Waardelijst/Rechtsgebieden")
_PROCEDURESOORTEN_URL          = urllib.parse.urljoin(BASE_URL, "/Waardelijst/Proceduresoorten")
_FORMELE_RELATIES_URL           = urllib.parse.urljoin(BASE_URL, "/Waardelijst/FormeleRelaties")
_NIET_NEDERLANDSE_UITSPRAKEN_URL = urllib.parse.urljoin(BASE_URL, "/Waardelijst/NietNederlandseUitspraken")


def parse_instanties():
    ''' Parse the 'instanties' value list
    
    @return: a list of flat dicts, 
    with keys   Naam, Afkorting, Type, BeginDate, Identifier, for example::
        {'Identifier': 'http://psi.rechtspraak.nl/AG DH',
               'Naam': "Ambtenarengerecht 's-Gravenhage",
          'Afkorting': 'AGSGR',
               'Type': 'AndereGerechtelijkeInstantie',
          'BeginDate': '1913-01-01'},
    '''
    instanties_bytestring = wetsuite.helpers.net.download( _INSTANTIES_URL )
    tree  = wetsuite.helpers.etree.fromstring( instanties_bytestring )
    ret = []
    for instantie in tree:
        kv = wetsuite.helpers.etree.kvelements_to_dict( instantie ) # this happens to be a flat structure, saves us some code
        ret.append( kv )
    return ret


def parse_instanties_buitenlands():
    ''' 
    Parse the 'buitenlandse instanties' value list
     
    @return: a list of flat dicts, with keys  Naam, Identifier, Afkorting, Type, BeginDate, for example::
        {'Identifier': 'http://psi.rechtspraak.nl/instantie/ES/#AudienciaNacionalNationaalHof',
               'Naam': 'Audiencia Nacional (Nationaal Hof)',
          'Afkorting': 'XX',
               'Type': 'BuitenlandseInstantie',
          'BeginDate': '1950-01-01'}
    '''
    instanties_buitenlands_bytestring = wetsuite.helpers.net.download( _INSTANTIES_BUITENLANDS_URL )
    tree  = wetsuite.helpers.etree.fromstring( instanties_buitenlands_bytestring )
    ret = []
    for instantie in tree:
        kv = wetsuite.helpers.etree.kvelements_to_dict( instantie ) # this happens to be a flat structure, saves us some code
        ret.append( kv )
    return ret


def parse_proceduresoorten():
    '''
    Parse the 'proceduresoorten' value list (assmed to be fixed).

    @return: A list of flat dicts, 
    with keys   Naam, Identifier, for example::
        {'Identifier': 'http://psi.rechtspraak.nl/procedure#artikel81ROzaken', 'Naam': 'Artikel 81 RO-zaken'}
    '''
    proceduresoorten_bytestring = wetsuite.helpers.net.download( _PROCEDURESOORTEN_URL )
    tree  = wetsuite.helpers.etree.fromstring( proceduresoorten_bytestring )
    ret = []
    for proceduresoort in tree:
        kv = wetsuite.helpers.etree.kvelements_to_dict( proceduresoort ) # this happens to be a flat structure, saves us some code
        ret.append( kv )
    return ret


def parse_rechtsgebieden():
    '''
    Parse the 'rechtsgebieden' value list (assumed to be fixed), 
    the data of which seems to be a depth-2 tree. 
    
    @return: as a dict with items like::
        'http://psi.rechtspraak.nl/rechtsgebied#bestuursrecht': ['Bestuursrecht'],
    and::
        'http://psi.rechtspraak.nl/rechtsgebied#bestuursrecht_ambtenarenrecht': ['Ambtenarenrecht', 'Bestuursrecht'],
    
    Where 
      - Bestuursrecht is a grouping of this and more, 
      - Mededingingsrecht one of several specific parts of it 
    '''
    # TODO: figure out what the data means and how we want to return it
    rechtsgebieden_bytestring = wetsuite.helpers.net.download( _RECHTSGEBIEDEN_URL )
    tree  = wetsuite.helpers.etree.fromstring( rechtsgebieden_bytestring )
    ret = {}
    for rechtsgebied1 in tree:
        #group = {}
        identifier1 = rechtsgebied1.find('Identifier').text
        naam1       = rechtsgebied1.find('Naam').text
        ret[identifier1] = [naam1]
        for rechtsgebied2 in rechtsgebied1.findall('Rechtsgebied'): #.find?
            #print( Rechtsgebied2)
            identifier2 = rechtsgebied2.find('Identifier').text
            naam2       = rechtsgebied2.find('Naam').text
            ret[ identifier2 ] = [naam2, naam1]
    return ret


#def parse_formelerelaties():
#    # TODO: figure out how we want to return that
#    pass


def parse_nietnederlandseuitspraken():
    ''' Parse the 'niet-nederpanse uitspraken' value list 

        @return: a list of items like::
            {'id': 'ECLI:CE:ECHR:2000:0921JUD003224096', 'ljn': ['AD4213']},
            {'id': 'ECLI:EU:C:2000:679',                 'ljn': ['AD4227']},
            {'id': 'ECLI:EU:C:2000:689',                 'ljn': ['AD4228']},
            {'id': 'ECLI:EU:C:2001:112',                 'ljn': ['AD4244', 'AL3652']},
    '''
    nietnederlandseuitspraken_bytestring = wetsuite.helpers.net.download( _NIET_NEDERLANDSE_UITSPRAKEN_URL )
    tree  = wetsuite.helpers.etree.fromstring( nietnederlandseuitspraken_bytestring )
    ret = []
    modified = tree.find('modified').text
    for entry in tree.findall('entry'):
        ret.append({ # TODO: check that that's valid.
            'id':entry.find('id').text,
            'ljn':list(e.text for e in entry.findall('ljn')),
        })
    return modified, ret


def website_zoek(term, start=0, amt=10, timeout=10):
    ''' Experiment that searches in the API at https://uitspraken.rechtspraak.nl/api/zoek

        ...which is NOT the public-facing API as as detailed by the documentation at https://www.rechtspraak.nl/Uitspraken/paginas/open-data.aspx
        but the one that is behind the current webpage search at https://uitspraken.rechtspraak.nl/
    
        Result items look something like::
            {                   'Titel': 'Gerecht in Eerste Aanleg van Aruba, 06-04-2021, UA202000260',
                        'TitelEmphasis': 'ECLI:NL:OGEAA:2021:125',
              'GerechtelijkProductType': 'uitspraak',
                   'UitspraakdatumType': 'uitspraak',
                       'Uitspraakdatum': '06-04-2021',
                     'Publicatiestatus': 'gepubliceerd',
                      'Publicatiedatum': '13-04-2021',
                  'PublicatiedatumDate': '2021-04-13T09:37:29+02:00',
                     'Proceduresoorten': ['Eerste aanleg - enkelvoudig', 'Beschikking'],  # interface calls this 'Bijzondere kenmerken'
                       'Rechtsgebieden': ['Civiel recht; Arbeidsrecht'],
              'InformatieNietGepubliceerdMessage': 'De publicatie van de uitspraak staat gepland op 13-04-2021 om 09:37 uur',
                           'InterneUrl': 'https://uitspraken.rechtspraak.nl/#!/details?id=ECLI:NL:OGEAA:2021:125&showbutton=true&keyword=test',
                          'DeeplinkUrl': 'https://deeplink.rechtspraak.nl/uitspraak?id=ECLI:NL:OGEAA:2021:125',
                           'IsInactief': False,
                  'RelatieVerwijzingen': [],
                        'Tekstfragment': 'Arbeid. Ontslag nietig. De stap van een niet '
                                        'afgenomen test, die gelijk wordt gesteld met '
                                        'een geweigerde test kan naar het oordeel van '
                                        'het Gerecht niet zonder meer worden genomen, '
                                        'waarbij het Gerecht de situatie van een niet '
                                        'afgenomen test niet ziet als een niet '
                                        'afgenomen test maar een niet voltooide test.',
                         'Vindplaatsen': [{'Vindplaats': 'Rechtspraak.nl',
                                         'VindplaatsAnnotator': '',
                                         'VindplaatsUrl': ''}]
            },
    '''

    req_d = {
        "StartRow":start,
        "PageSize":amt,
        "ShouldReturnHighlights":False,
        "ShouldCountFacets":False,
        "SortOrder":"Relevance",
        #"SortOrder":"UitspraakDatumDesc",
        "SearchTerms":[ {"Term":term, "Field":"AlleVelden"}, ],
        "Contentsoorten":[],
        "Proceduresoorten":[],
        "Rechtsgebieden":[],
        "Instanties":[],
        "DatumPublicatie":[],
        "DatumUitspraak":[],
        "Advanced":{"PublicatieStatus":"AlleenGepubliceerd"},
    }
    req_json = json.dumps( req_d )
    response = requests.post(
        'https://uitspraken.rechtspraak.nl/api/zoek', 
        data=req_json,
        headers={'Content-type': 'application/json'},
        timeout=timeout)
    return response.json()
