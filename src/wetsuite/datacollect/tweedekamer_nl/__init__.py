#!/usr/biny/python3
''' Fetches from the APIs provided by U{opendata.tweedekamer.nl<https://opendata.tweedekamer.nl>}

    Described at https://opendata.tweedekamer.nl/documentatie/odata-api
    though so far we implement and use mostly the Atom/SyncFeed API,
    not the OData one.

    The full information model is fairly complex,
    see https://opendata.tweedekamer.nl/documentatie/informatiemodel

    The data almost certainly comes from a relational database 
    and is exposed in basically the same way,
    with not only references but also many-to-many tables.

    Our initial need was simple, so this only fetches a few parts, with no dependencies.
    If you want a much more complete implementation and pleasant presentation, 
    look to https://github.com/openkamer/openkamer

    
    It is unclear how to do certain things with this interface, 
    e.g. list the items in a kamerstukdossier.
    (though we can get those via e.g. https://zoek.officielebekendmakingen.nl/dossier/36267)
'''

import wetsuite.helpers.net
import wetsuite.helpers.etree

resource_types = ( # copy. Presumably won't change.
    'Activiteit', 'ActiviteitActor', 'Agendapunt', 'Besluit', 
    'Commissie', 'CommissieContactinformatie', 'CommissieZetel', 
    'CommissieZetelVastPersoon', 'CommissieZetelVastVacature', 
    'CommissieZetelVervangerPersoon', 'CommissieZetelVervangerVacature', 
    'Document', 'DocumentActor', 'DocumentVersie', 
    'Fractie', 'FractieAanvullendGegeven', 'FractieZetel', 
    'FractieZetelPersoon', 'FractieZetelVacature', 
    'Kamerstukdossier',
    'Persoon', 'PersoonContactinformatie', 'PersoonGeschenk', 'PersoonLoopbaan', 
    'PersoonNevenfunctie', 'PersoonNevenfunctieInkomsten', 'PersoonOnderwijs', 'PersoonReis',
    'Reservering', 'Stemming', 
    'Vergadering', 'Verslag', 'Zaak', 'ZaakActor', 'Zaal'
)



## First interface: SyncFeed/Atom

SYNCFEED_BASE = 'https://gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/'
' Base URL for a few different fetches (mostly /Feed) '

# TODO: figure out and provide more of interface
# /SyncFeed/2.0/Feed
# /SyncFeed/2.0/Entiteiten/<id>     single entity. The type
# /SyncFeed/2.0/Resources/<id>      resources for entity
#
# Feed?category
#
# Resources seem to be either
# - referenced   e.g. in enclosure tags
# - implied (?), e.g. each Document can be fetched its listed Id


def fetch_resource( resource_id ):
    ''' Note that if these don't exist, they will cause a 500 Internal Server Error,
        which should get thrown as an exception(VERIFY) 
    '''
    url = f'{SYNCFEED_BASE}Resources/%s'%resource_id
    return wetsuite.helpers.net.download( url )


def fetch_all(soort="Persoon", break_actually=False, timeout=60):
    ''' Fetches all feed items of a single soort.

        Returns items from what might be multiple documents,
        because this API has a "and here is a link for more items from the same search" feature.
        Keep in mind that for some categories of things, this can be a _lot_ of fetches and data.

        @param soort: what object type to fetch everything for.
        For the available values, see e.g. https://opendata.tweedekamer.nl/documentatie/introductie
        Note that if you misspell the soort, it returns an empty list rather than erroring out.

        @param break_actually: break after first fetch, mostly for faster debug and testing

        
        @return: a list of etree objects, which are also stripped of namespaces 
        (atom for the wrapper, tweedekamer for <content>).

        This is not immediately useful,
        and you probably want to feed this into L{merge_etrees} to make a single large document
        (some types are hundreds of MByte, though).
    '''
    url = f'{SYNCFEED_BASE}Feed?category=%s'%soort
    ret = []
    while True:
        xml  = wetsuite.helpers.net.download( url, timeout=timeout )
        tree = wetsuite.helpers.etree.fromstring( xml )
        tree = wetsuite.helpers.etree.strip_namespace( tree )

        # is there a next page?
        url = None
        links = tree.findall('link')
        for link in links:
            # we're looking for something like
            #  <link rel="next" href="https://gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/Feed?category=Persoon&amp;skiptoken=11902974"/>
            rel = link.get('rel')
            href = link.get('href')
            if rel == 'next':
                url = href
            # edict['links'].append( (rel,href) )

        ret.append( tree )

        if break_actually:
            break

        if url is None: # no 'next' link, we're done.
            break

    return ret


def merge_etrees( trees ):
    ''' Merges a list of documents (etree documents, as fetch_all gives you) 
        into a single etree document.
        Tries to pick up only the interesting data.
    '''
    ret = wetsuite.helpers.etree.Element('feed') # decide what to call that document
    for tree in trees:
        # redundant if you use fetch_all, here in case you're reading your own documents
        tree = wetsuite.helpers.etree.strip_namespace( tree )

        for entry in tree.findall('entry'):
            ret.append(entry)
    return ret


def _entry_dict_from_node(entry_node):
    ''' Helper for L{entry_dicts}. 

        Given a single etree node (that came from an <entry>),
        returns the contained information in a dict. 
        This is mostly key-value (elem.tag, elem.value) but flattens a few details.
    '''
    #warnings.warn('Picking up ddetails from a ')
    edict = {}
    edict['title']    = entry_node.findtext('title')  #which seems the be the GUID, not a title?

    edict['updated']  = entry_node.findtext('updated')
    edict['category'] = entry_node.find('category').get('term')

    #I believe this is always "Tweede Kamer der Staten-Generaal" which is not very useful
    #if entry_node.find('author') is not None:
    #    edict['author/name']  = entry_node.findtext('author/name')

    # try to simplify wat <content> is doing
    content_elem = entry_node.find('content')
    if content_elem is not None:
        edict['content'] = []
        # assumption that there is just one - TODO: check that's true
        content_content = list(content_elem)[0]
        #print( wetsuite.helpers.etree.debug_pretty(conte))
        cd = {'refs':{}}
        # flatten attribs and sub-elements for now - TODO: check this assumption makes sense
        cd['tagname'] = content_content.tag # probably won't clash
        for name, val in content_content.attrib.items():
            cd[name] = val
        for ccsubelem in list(content_content):
            # assumption: either a reference to another id,  or a kv-style node with just text
            ref = ccsubelem.attrib.get('ref')
            if ref is not None:
                cd['refs'][ccsubelem.tag] = ref
            else:
                cd[ ccsubelem.tag ] = ccsubelem.text


        #edict['content'].append( cd )
        edict['content'] = cd

    # it's in three places and should aways be identical,
    # but this seems the most sensible place, should it ever change
    edict['id'] = entry_node.find('id').text
    #edict['id'] = entry_node.get('id')
    return edict


def entry_dicts( feed_etree ):
    ''' @param feed_etree: an etree object for a syncfeed list.
        ...mostly made for the output of L{merge_etrees}. 

        @return: A list of dicts, one for each <entry> nodes from that etree.
        Most values are strings, while e.g. links are (rel, url) pairs.
    '''
    ret = []
    for entry_node in feed_etree.findall('entry'):
        ret.append( _entry_dict_from_node( entry_node ) )
    return ret
