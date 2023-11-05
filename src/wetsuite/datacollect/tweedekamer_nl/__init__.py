#!/usr/biny/python3
''' As described at https://opendata.tweedekamer.nl/documentatie/odata-api
    though so far we implement only the Atom/SyncFeed API, not the OData one.

    The full information model is fairly complex, see https://opendata.tweedekamer.nl/documentatie/informatiemodel

    The data almost certainly comes from a relational database and is exposed in basically the same way,
    with not only references but also many-to-many tables.

    Our initial need was simple, so this only fetches a few parts, with no dependencies.
    If you want a much more complete implementation, look to https://github.com/openkamer/openkamer

    
    It is unclear to me how to do certain things with this interface, e.g. list the items in a kamerstukdossier.
    (we can get those via e.g. https://zoek.officielebekendmakingen.nl/dossier/36267 though)
'''

import wetsuite.helpers.net
import wetsuite.helpers.etree

resource_types = ( 
    'Activiteit', 'ActiviteitActor', 'Agendapunt', 'Besluit', 'Commissie', 'CommissieContactinformatie', 'CommissieZetel', 
    'CommissieZetelVastPersoon', 'CommissieZetelVastVacature', 'CommissieZetelVervangerPersoon', 'CommissieZetelVervangerVacature', 
    'Document', 'DocumentActor', 'DocumentVersie', 'Fractie', 'FractieAanvullendGegeven', 'FractieZetel', 'FractieZetelPersoon', 
    'FractieZetelVacature', 'Kamerstukdossier', 'Persoon', 'PersoonContactinformatie', 'PersoonGeschenk', 'PersoonLoopbaan', 
    'PersoonNevenfunctie', 'PersoonNevenfunctieInkomsten', 'PersoonOnderwijs', 'PersoonReis', 'Reservering', 'Stemming', 
    'Vergadering', 'Verslag', 'Zaak', 'ZaakActor', 'Zaal'
)





## First interface: SyncFeed/Atom

syncfeed_base = 'https://gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/'
#                        gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/Feed
#                        gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/Entiteiten/<id>     single entity. The type 
#                        gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/Resources/<id>      resources for entity



#Feed?category
#Resources seem to be either
#- referenced e.g. in enclosure tags
#- implied, e.g. each Document can be fetched its listed Id, 

#/Resources 
#/Entiteiten is the document metadata


def fetch_resource(id):
    ''' Note that if these don't exist, they will cause a 500 Internal Server Error '''
    url = f'{syncfeed_base}Resources/%s'%id
    return wetsuite.helpers.net.download( url )


def fetch_all(soort="Persoon"):
    ''' Fetches all feed items of a single soort.

        Returns items from what might be multiple documents, because this API has a "and here is a link for more items from the same search" feature
        Keep in mind that for some categories of things, this can be a _lot_ of fetches.

        Returns as a list of etree documents
        which are also stripped of namespaces (atom for the wrapper, tweedekamer for <content>).
    '''
    url = f'{syncfeed_base}Feed?category=%s'%soort
    ret = []
    while True:
        #print( url )
        xml  = wetsuite.helpers.net.download( url )
        tree = wetsuite.helpers.etree.fromstring( xml )
        tree = wetsuite.helpers.etree.strip_namespace( tree )

        # is there a next page?
        url = None
        links = tree.findall('link')
        for link in links:   # we're looking for something like    <link rel="next" href="https://gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/Feed?category=Persoon&amp;skiptoken=11902974"/>
            rel = link.get('rel')
            href = link.get('href')
            if rel == 'next':
                url = href
            # edict['links'].append( (rel,href) )

        ret.append( tree ) 

        if url is None: # no 'next' link, we're done.
            break
        
    return ret


def merge_etrees( trees ):
    ''' Merges a list of documents (etree documents, as fetch_all gives you) into a single etree document.
        Tries to pick up only the interesting data.
    '''
    ret = wetsuite.helpers.etree.Element('feed') # decide what to call that document
    for tree in trees:
        tree = wetsuite.helpers.etree.strip_namespace( tree ) # redundant if you use fetch_all,  still here in case you're reading your own separate documents
        for entry in tree.findall('entry'):
            ret.append(entry)
    return ret


def entries(feed_etree):
    ''' Returns all <entry> nodes from en etree, as a list of dicts 
        Most values are strings, while e.g. links are (rel, url) pairs.
    '''
    ret = []
    for entry in feed_etree.findall('entry'):
        edict = {}
        #edict['title']    = entry.findtext('title')  #which seems the be the GUID
        #edict['id']       = entry.findtext('id')
        edict['updated']  = entry.findtext('updated')
        edict['category'] = entry.find('category').get('term')
        content = entry.find('content')
        item = content[0]
        for elem in item:
            if elem.attrib.get('nil','false') == 'true':
                edict[ elem.tag ] = None  # .text should be anyway, but this is at least clearer
                continue

            if len(elem.attrib)==0:
                edict[ elem.tag ] = elem.text
                continue

            refval = elem.attrib.get('ref', None)
            if refval != None:
                edict[ elem.tag ] = ('ref', refval)
                continue

            raise ValueError( "ERROR: programmer didn't think of case like %r"%wetsuite.helpers.etree.tostring(elem) )
            # as debug
            #print(  )
            #print( elem )
            #print( elem.attrib )
        edict['id'] = item.get('id') # it's in three places and should aways be identical, but this seems the most sensible place, should it ever change

        #print()
        #print( wetsuite.helpers.etree.tostring( wetsuite.helpers.etree.indent(content) ).decode('u8') )
        #import pprint
        #pprint.pprint( edict )

        ret.append( edict )
    return ret





## Other interface: OData

odata_base = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/'

# list all items of soort:
# url = f'{odata_base}/{%s}'%(soort,)

# list metadata for specific item:
# url = f'{odata_base}/{%s}(%s)'%(soort, id)

# document for specific item (if present):
# url = f'{odata_base}/{%s}(%s)/resource'%(soort, id)


# Searches are done with a filter function, often added to the query for a specific soort
# url = f'{odata_base}/{%s}?$filter=$s'%(
#   'Persoon', 
#   escape_uri('Verwijderd eq false and (Functie eq 'Eerste Kamerlid' or Functie eq 'Tweede Kamerlid')') 
# )
# /Persoon?$filter=Verwijderd%20eq%20false%20and%20(Functie%20eq%20%27Eerste%20Kamerlid%27%20or%20Functie%20eq%20%27Tweede%20Kamerlid%27)


