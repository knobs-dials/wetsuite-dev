#!/usr/bin/python3
'''  Very minimal SRU implementation - just enough to access KOOP's repositories. 

     Used by the koop_repositories module.

     Not meant to be a generic implementation - it was written because existing python SRU libraries we tried 
     didn't seem to like the apparently-custom URL component (x-connection) that the KOOP rpositories use, 
     so until we figure out a cleaner solution, here's a just-enough-to-work implementation for our specific use cases.
'''
# https://www.loc.gov/standards/sru/sru-1-1.html

import time, sys

import requests

import wetsuite.helpers.escape
import wetsuite.helpers.etree


# TODO: centralize parsing of originalData / enrichedData as much as we can, so that each individual user doesn't have to.



class SRUBase(object):
    def __init__(self, base_url:str, x_connection:str=None, extra_query:str=None, verbose=False):
        ''' base_url should be everything up to the ?
            
            Notes:
            - x_connection is used to specify the collection within a server, and seems to be non-standard and required

            - extra_query is used to let us AND something into the query, and is intended to restrict to a subset of documents
              in these cases, x_connection seems to include in extra sets, and the combination is sometimes too much (?)
        '''
        self.base_url        = base_url
        self.x_connection    = x_connection
        self.sru_version     = '1.2'
        self.extra_query     = extra_query
        self.verbose         = verbose
        self.numberOfRecords = None # hackish, TODO: rethink

        
    def _url(self):
        """ combines the basic URL parts given to the constructor, and ensures there's a ?  (so you know you can add &k=v)
            This can probably go into the constructor, when I know how much is constant across SRU URLs
        """
        ret = self.base_url
        if '?' not in ret: 
            ret += '?'
        #escape.uri_dict might be a little clearer/cleaner
        if self.sru_version not in ('',None):
            ret += '&version=%s'%self.sru_version
        if self.x_connection not in ('',None):
            ret += '&x-connection=%s'%wetsuite.helpers.escape.uri_component(self.x_connection)   # #all the x-connection values I've seen are [a-z] so the escape is superfluous
        return ret

    
    def explain(self, readable=True, strip_namespaces=True): 
        ''' Does an explain operation,
            Returns the XML
            - if readable==False, it returns it as-is
            - if readable==True (default), it will ease human readability:
                - strips namespaces
                - reindent 
            The XML is a unicode string (for consistency with ourselves)
        '''
        url = self._url() 
        url += '&operation=explain'
        r = requests.get( url )
        if readable:
            tree = wetsuite.helpers.etree.fromstring(r.content)
            if strip_namespaces==True:
                wetsuite.helpers.etree.strip_namespace_inplace(tree) # easier without namespaces
            wetsuite.helpers.etree.indent_inplace(tree)
            return wetsuite.helpers.etree.tostring(tree, encoding='unicode')
        else:
            return r.content.decode('utf-8')


    def explain_parsed(self):
        ''' Does an explain operation
            Returns a dict with some of the more interesting details
            TODO: actually read the standard instead of assuming things.
        '''
        url = self._url() 
        url += '&operation=explain'

        ret = {
            'explain_url':url
        }

        if self.verbose:
            print( url )
        r = requests.get( url )
        tree = wetsuite.helpers.etree.fromstring( r.content )
        wetsuite.helpers.etree.strip_namespace_inplace(tree) # easier without namespaces
        #wetsuite.helpers.etree.indent_inplace(tree) # debug

        explain = tree.find('record/recordData/explain')

        def get_attrtext(treenode, name, attr):
            ' under etree object :treenode:, find a node called :name:, and get the value of its :attr: attribute '
            if treenode is not None:
                node = treenode.find(name)
                if node is not None:
                    return name, attr, node.get(attr)
        
        def get_nodetext(treenode, name):
            ' under etree object :treenode:, find a node called :name:, and get the inital text under it '
            if treenode is not None:
                node = treenode.find(name)
                if node is not None:
                    return node.text
            return None
        
        for (treenode, name, attr) in ( 
            (explain.find('serverInfo'), 'database', 'numRecs'),
        ):
            name, attr, val = get_attrtext(treenode, name, attr)
            ret[f'{name}/{attr}'] = val

        for treenode, name in ( # TODO: make this more complete
            (explain.find('serverInfo'), 'host'),
            (explain.find('serverInfo'), 'port'),
            (explain.find('databaseInfo'), 'title'),
            (explain.find('databaseInfo'), 'description'),
            (explain.find('databaseInfo'), 'extent'),
        ):
            val = get_nodetext(treenode, name)
            ret[name] = val

        indices, sets = [], []
        indexInfo = explain.find('indexInfo')
        for index in indexInfo.findall('index'):
            map  = index.find('map')
            name = map.find('name')
            set  = name.get('set')
            val  = name.text
            indices.append( (set, val) )

        for set in indexInfo.findall('set'):
            name       = set.get('name')
            identifier = set.get('identifier')
            title = None
            if set.find('title') is not None:
                title = set.find('title').text
            sets.append( (name, identifier, title) )

        ret['indices'] = indices
        ret['sets'] = sets
        return ret


    def num_records(self):
        ''' 
        After you do a search_retrieve, this should be set to a number.
        
        This function may change.
        '''
        return self.numberOfRecords


    def search_retrieve(self, query:str, start_record=None, maximum_records=None, callback=None, verbose=False):
        ''' Fetches a range of results for a particular query. 
            
            Returns each result record as a separate ElementTree object.
            Exactly what this contains varies per repo, but you may well _want_ this raw because it can contain metadata not easily fetched from the results themselves.

            You mat want to fish out the number of results (TODO: make that easier)
            
            Notes:
            - strips namespaces from the results - makes writing code more convenient
            
            - query is LoC's CQL
              - which indices you can use (e.g. e.g. 'dcterms.modified>=2000-01-01') varies with each repo
              take a look at explain_parsed() (a parsed summary) or explain() (the actual explain XML)

            - start_record and maximum_records describe the range to fetch
              - start_record uses one-based counting

            - if callback is not None, this function calls it for each such record node.

            - Repos may have a (lowish) limit on maximum_records,
              so if you care about _all_ results, you probably want to use search_retrieve_many() instead.

            CONSIDER:
            - option to returning URL instead of searching
        ''' 

        if self.extra_query is not None:
            query = '%s and %s'%(self.extra_query, query)
        
        url = self._url() 
        url += '&operation=searchRetrieve'

        if start_record is not None:
            url += '&startRecord=%d'%start_record
        if maximum_records is not None:
            url += '&maximumRecords=%d'%maximum_records

        url += '&query=%s'%wetsuite.helpers.escape.uri_component(query)

        if self.verbose:
            print( "[SRU searchRetrieve] fetching %r"%url )

        try:
            r = requests.get( url, timeout=(20,20) ) # CONSIDER: use general fetcher?
        except requests.exceptions.ReadTimeout: 
            r = requests.get( url, timeout=(20,20) ) # TODO: this makes no sense, don't do it
            
        if r.status_code == 500:
            raise RuntimeError( "SRU server reported an Internal Server Error (HTTP status 500) for %r"%url )

        tree = wetsuite.helpers.etree.fromstring( r.content )

        # easier without namespaces, they serve no disambiguating function in most of these cases anyway
        # TODO: think about that, user code may not expact that
        wetsuite.helpers.etree.strip_namespace_inplace(tree) 

        if tree.tag=='diagnostics': # TODO: figure out if this actually happened 
            raise RuntimeError( wetsuite.helpers.etree.strip_namespace(tree).find( 'diagnostic/message' ).text )
        elif tree.find( 'diagnostics') is not None:
            raise RuntimeError( wetsuite.helpers.etree.strip_namespace(tree).find( 'diagnostics/diagnostic/message' ).text )

        elif tree.tag=='explainResponse':
            wetsuite.helpers.etree.strip_namespace_inplace(tree) # bit lazy
            raise RuntimeError( 'search returned explain response instead' )
        
        if verbose:
            print( wetsuite.helpers.etree.tostring( wetsuite.helpers.etree.indent( tree )) .decode('u8') )

        self.numberOfRecords = int(tree.find('numberOfRecords').text)
        if verbose:
            print('numberOfRecords:', self.numberOfRecords, file=sys.stderr)
        
        ret = []
        for record in tree.findall('records/record'):  
            ret.append(record)
            if callback is not None:
                callback( record )    # CONSIDER: callback( record, query )  and possibly pas other things
        return ret # maybe return list, like _many does?


    def search_retrieve_many(self, query:str, at_a_time:int=10, start_record:int=1, up_to:int=250, callback=None, wait_between_sec:float=0.5, verbose=False):
        ''' While search_retrieve() could be used directly to e.g. see if there are results at all,
            it is really a helpfer for this funtion, which adds "fetch all results in chunks",
            by calling search_retrieve repeatedly.

            Like search_retrueve, it (eventually) returns each result record as an elementTree objects,
            and if callback is not None, it is called on each of those.
            This can be more convenient way of dealing with many results while they come in,

            Notes:
            - up_to is the absolute offset, e.g. start_offset=200, up_to=250 gives you records 200..250, not 200..450

            - since we fetch in chunks, we may fetch more records than you asked for, by up to at_a_time amount of entries. We could be slightly nicer about that.

            - wait_between_sec is a backoff sleeps between each search chunk, to avoid hammering a server too much. 
              you can lower this where you know this is overly cautious
              note that we skip this sleep if one fetch was enough

            CONSIDER: 
            - maybe yield something including numberOfRecords before yielding results?
        '''
        ret = []
        offset = start_record

        while True: # offset < up_to:
            records = self.search_retrieve(query=query, start_record=offset, maximum_records=at_a_time, callback=None, verbose=verbose)
            if len(records)==0:
                break

            for chunk_offset, record in enumerate(records):
                ret.append( record )
                if callback is not None:
                    callback( record )
                
                if offset+chunk_offset >= up_to: # we fetched more than was needed
                    break

            offset += at_a_time
            
            if offset >= up_to: # crossed beyond what was asked for  (we don't return it even if we fetched it)
                break

            if self.numberOfRecords is not None and offset > self.numberOfRecords: # crossed beyond what exists in the search result
                break

            time.sleep( wait_between_sec ) # note that this is avoided if a single fetch was enough

        return ret

