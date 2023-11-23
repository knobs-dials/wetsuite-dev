#!/usr/bin/python3
'''
An experiment whether it is useful to provide a "fetch me things from downloaded datasets
and/or online data and/or some local files". In idea stage.


See also:
  - the datasets module,    
    which deals with data in the sense of pre-generated collections you can download as a file and load in RAM
    ...but can be incomplete or out of date, and may not fit in RAM

  - the datacollect module, which queries the govermnent databases
    ...but can be slow and not always search the thing you want


The same API supports this code as well as a website view.

CONSIDER:
  - describe how to host your own.

  - We may want to effectively create a 2-stage search, 
  - the first a predetermined set of fields from a remote server that determines what we fetch
    - cannot change much in that even if it's not an API change, it's a change in e.g. fields that the code has to assume are there (unless maybe we reinvent SRU)
  - the second a more flexible way of sifting through what you have downloaded

  - Same API to search in a downloaded dataset
  - should prove faster, and may be longer-lived due to only needing file hosting, not service hosting
    though there are more RAM concerns

  - Very similar API for live search
    the argument against this that it's a leaky abstraction when a unified API works differently for fairly hidden reasons
    BUT in case we ever still want to, with loud footnotes, it's a good idea to think about that unified API

  - split out code into one source per file, something patterny like registering factories ?
'''

import warnings

import requests

import wetsuite.datacollect.koop_repositories
import wetsuite.helpers.net
import wetsuite.helpers.etree
import wetsuite.helpers.koop_parse
#import wetsuite.helpers.localdata


warnings.warn('the wetsuite.datasearch interface likely to change over time, especially in these early days')




def document_url_by_identifier(ident, type_hint=None):
    ''' Return the link to the web version, and to the data version, 
    '''
    return _SearchBase().urls_for_identifier(ident, type_hint=type_hint)


#def document_by_identifier(ident):
#    url = document_url_by_identifier(ident, type_hint)
#    return wetsuite.helpers.net.download(url)


#def plaintext_by_identifier(ident, type_hint=None):
#    pass



class _SearchBase:
    ''' The communication part, so we can share it '''
    def __init__(self, base_url='https://labs.scarfboy.com/wet/search-api?reload=y'):
        self.base_url = base_url


    def _interact(self):
        ''' Sends self.form to self.base_url.
            This lets us share interaction between things like search() and fetch_identifers()
        '''
        resp = requests.post( self.base_url, data=self.form )
        try:
            self.response = resp.json()
        except Exception as e:
            #resp.status_code
            #print(e)
            #print(repr(resp.content))
            raise
        return self.response


    def urls_for_identifier(self, ident, type_hint=None):
        ''' If you have just a BWB, CVDR, ECLI or CELEX (TODO) identifier,
            this should tell you URL(s) you can find that at.

            Note that 
              - you do not need to do this if you _came_ from a search, 
                its hits already contains these URLs -- if we know it.
              - this can be less reliable than search, in that 
                if you didn't normalize it quite like we did it may not return a result.
        '''
        #if ident.startswith('BWB'):
        #if ident.startswith('CVDR'):
        #if ident.startswith('ECLI'):
        #if ident.startswith('CELEX'):

        # TODO: some informed normalization of that identifier
        self.form = {'identifier':ident}
        #print(self.form)
        response = self._interact()
        #print(response)

        ret = {'web_urls':[], 'xml_urls':[], 'identifier':[ident]}
        for hit in self.response['hits']['hits']:
            # make it a little less ElasticSearchy
            _source = hit['_source']
            hit.update( _source )
            del hit['_source']
            #if _source.get('identifier') == ident:
            if 'identifier' in _source:
                resp_ident = _source.get('identifier')
                if resp_ident is not None and resp_ident not in ret['identifier']:
                    ret['identifier'].append( resp_ident )
            if 'web_url' in _source:
                ret['web_urls'].append( _source['web_url'] )
            if 'xml_url' in _source:
                ret['xml_urls'].append( _source['xml_url'] )


        return ret


class HostedSearch(_SearchBase):
    ''' Posts a form to a HTTP API.
        The query isn't specific to any specific backend, 
        though we expect ElasticResearch (-style) results back.
    '''

    def __init__(self, base_url='https://labs.scarfboy.com/wet/search-api'):
        super().__init__(base_url)
        #self.hit_ids = []
        self.response = None


    def search(self, **kwargs):
        ''' Takes keyword arguments, currently:
            - q: 

            Fetches
            - a full selection of identifiers (RECONSIDER?)
            - a description of the first 10
        '''
        self.form = {}
        q = kwargs.get('q', None)
        if q is not None:
            self.form['q'] = q

        self.response = self._interact()
        return self.response


    def num_hits(self):
        ''' Returns the ElasticSearch hits.total section as a python dict, which contains something like::
               {'relation': 'eq', 'value': 21}
            or::
               {'relation': 'gte', 'value': 10000}
            the latter meaning there were more.
        '''
        if self.response is None:
            raise ValueError('You need to search before you can have a result.')
        return self.response['hits']['total']


    def hits(self):
        ''' Note that these will only be the first so-many - defaulting to 100, enough for a 'is this a reasonable search' check.
        
        '''
        #return self.response['hits']['hits']

        ret = []
        for hit in self.response['hits']['hits']:
            # merge _source into the top level dict
            _source = hit['_source']
            del hit['_source']
            hit.update(_source)
            ret.append( hit )

        return ret



    def fetch_identifers(self, max=500):
        ''' If you are happy with the set search() seems to describe, fetch the identifiers of more of the result set.
            Defaults to fetch only the first 500, to avoid slowness.
        '''
        # this mostly amounts to a size from

####################################



####################################

# class BWBLiveSearch:
#     def __init__(self):
#         self.sru = wetsuite.datacollect.koop_repositories.BWB()

#     def search(self, q):
#         sru_bwb.search_retrieve_many( 'dcterms.identifier = BWBR0045754', up_to=5 )

#         query = []
#         #q = kwargs.get('q')
#         #if q is not None:
#         #    query.append()
#         identifier = identifier.get('q')
#         if

#         identifier=None
#         dcterms.identifier = BWBR0045754


# class CVDRLiveSearch:
#     " Search CVDR via KOOP's SRU interface "
#     def __init__(self):
#         self.sru = wetsuite.datacollect.koop_repositories.CVDR()


#     def search(self, q):
#         sru_bwb.search_retrieve_many( 'dcterms.identifier = BWBR0045754', up_to=5 )

#         query = []
#         q = kwargs.get('q')
#         if q is not None:
#             query.append()
#         identifier = identifier.get('q')


#class RechtspraakLiveSearch:
#    pass




#class RechtspraakLocalSearch:
#    pass


#class CVDRLocalSearch:
#    pass


#class BWBLocalSearch:
#    pass



# class _LazyDoc:
#     ''' we parse lazily. CONSIDER: a document collection so we can do that en masse '''
#     def _lazy_load(self):
#         if self.etree == None:
#             self.etree = wetsuite.helpers.etree.fromstring( self.xml_bytestring )
#             self.self.xml_bytestring = None # save a little RAM



# class RechtspraakDocument(_LazyDoc):
#     ''' A class that tries to present documents a little nicer than "here is some XML, good luck" '''
#     def __init__(self, xml_bytestring):
#         self.xml_bytestring = xml_bytestring
#         self.etree = None

#     def plain_text(self):
#         self._lazy_load()

#     def section_text(self, ):
#         self._lazy_load()

#     def meta(self, ):
#         self._lazy_load()


# class CVDRDocument(_LazyDoc):
#     ''' A class that tries to present documents a little nicer than "here is some XML, good luck" '''
#     def __init__(self, xml_bytestring):
#         self.xml_bytestring = xml_bytestring
#         self.etree = None

#     def plain_text(self):
#         self._lazy_load()

#     def section_text(self, ):
#         self._lazy_load()

#     def meta(self, ):
#         self._lazy_load()


# class BWBDocument(_LazyDoc):
#     ''' A class that tries to present documents a little nicer than "here is some XML, good luck" '''
#     def __init__(self, toestand_bytestring): # maybe also the wti and metadata?  Maybe separate laziness because they would probably be used less?
#         self.toestand_bytestring = toestand_bytestring
#         self.etree = None


####################################
