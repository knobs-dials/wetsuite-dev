#!/usr/bin/python3
''' Fetch and load already-created datasets that we provide.

    As this is often structured data, each dataset may work a little differently, 
    so there is an describe() to get you started, that each dataset should fill out.

    TODO: 
    * decide how often to re-fetch the index client-side. 
        Each interpreter (which is what it does right now)?   
        Store and base on mtime with possible override? 
        Decide it's cheap enough to fetch each time? (but fall back onto stored?)
    * decide how to store and access. For very large datasets we may want something like HDF5 
        because right now we don't have a choice but to have all the dataset in RAM
'''

import sys, os, json, tempfile, bz2

import wetsuite.helpers.util
import wetsuite.helpers.net
import wetsuite.helpers.localdata
from wetsuite.helpers.notebook import is_interactive





### Index of current datasets
# This needs to become a remotely stored thing.  
#   right now it's hardcoded because I'm figuring out the loading API in general
# TODO: figure out hosting, and where to put the base URL

_index_url = 'https://wetsuite.knobs-dials.com/datasets/index.json'

_index = None


def list_datasets():
    global _index
    if _index is None:
        _index = fetch_index()
    return list( _index.keys() )
    #return list( _index.items() )


def fetch_index():
    ''' Index is expected to be a list of dicts, each with keys includin
        - url
        - version             (should probably become semver)
        - short_description   summary of what this is   (details of use is part of the dataset itself)
        - download_size       how much transfer you'll need
        - real_size           Disk storage we expect to need once decompressed
        - type                type of dataset, 
                              currently MIME type 
                              currently indicating it's either 
                              - a JSON file (for small things) or 
                              - an SQLite3 database that would be opened via the localdata module
          {'datasetname':{url:'http://example.com/dataset.tgz', 'description':'Blah'}}

        CONSIDER: keep hosting generic (HTTP fetch?) so that any hoster will do.
    '''
    if True: # HACK: the index is currently hardcoded, it should probably come from the host, and from listing uploaded metadata there
        index_dict = {
            'rvsadviezen-struc':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/raadvanstate_adviezen.json.bz2',
                                                'version':'preliminary', 
                                      'short_description':'The advice under https://raadvanstate.nl/adviezen/ provided as plain text in a nested structure with metadata. ',  
                                          'download_size':5460023,
                                              'real_size':34212068,   # or maybe more directly readable  '5MB' and '34MB'?
                                                   'type':'application/json',
            },


            'kamervragen-struc':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/kamervragen.json.bz2',             
                                                'version':'preliminary',
                                      'short_description':'Questions from ministers to the government. Provided as a nested data structure.',    
                                          'download_size':74218609,
                                              'real_size':506814395,
                                                   'type':'application/json',
            },


            'bwb-mostrecent-xml':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/bwb_latestonly_xml.db.xz',
                                                'version':'preliminary',
                                      'short_description':'The latest revision from each BWB-id',
                                          'download_size':-1,  
                                              'real_size':-1,
                                                   'type':'application/json',
            },
            'bwb-mostrecent-meta':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/bwb_latestonly_meta.db.xz',
                                                'version':'preliminary',
                                      'short_description':'The latest revision from each BWB-id',
                                          'download_size':-1,  
                                              'real_size':-1,
                                                   'type':'application/json',
            },
            'bwb-mostrecent-text':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/bwb_latestonly_text.db.xz',
                                                'version':'preliminary',
                                      'short_description':'The latest revision from each BWB-id',
                                          'download_size':-1,  
                                              'real_size':-1,
                                                   'type':'application/json',
            },


            'cvdr-mostrecent-xml':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/cvdr_latestonly_xml.db.xz',
                                                'version':'preliminary',
                                      'short_description':'The latest expression from each CVDR work',
                                          'download_size':603843736,  
                                              'real_size':5586030592,
                                                   'type':'application/json',
            },
            'cvdr-mostrecent-meta':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/cvdr_latestonly_meta.db.xz',
                                                'version':'preliminary',
                                      'short_description':'The latest expression from each CVDR work',
                                          'download_size':603843736,  
                                              'real_size':5586030592,
                                                   'type':'application/json',
            },
            'cvdr-mostrecent-text':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/cvdr_latestonly_text.db.xz',
                                                'version':'preliminary',
                                      'short_description':'The latest expression from each CVDR work',
                                          'download_size':603843736,  
                                              'real_size':5586030592,
                                                   'type':'application/json',
            },

                
            'woo-besluiten-meta':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/woo_besluiten_meta.db',
                                                'version':'preliminary',
                                      'short_description':'',
                                          'download_size':708608,
                                              'real_size':708608,
                                                   'type':'application/json',
            },
            'woo-besluiten-text':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/woo_besluiten_docs_text.db.xz',
                                                'version':'preliminary',
                                      'short_description':'',
                                          'download_size':7191376,
                                              'real_size':40292352,
                                                   'type':'application/json',
            },


            # TODO: meta as well
            'kansspelautoriteit-sancties-txt':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/kansspelautoriteit_plain.json.bz2', 
                                                'version':'preliminary', 
                                      'short_description':'Sanction decisions, in plain text, extracted from from the case PDFs under https://kansspelautoriteit.nl/aanpak-misstanden/sanctiebesluiten/',
                                          'download_size':1147517,
                                              'real_size':7604025,
                                                   'type':'application/json',
            },



            # just metadata
            'gemeentes':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/gemeentes.json',    
                                                'version':'preliminary', 
                                      'short_description':'List of municipalities, and some basic information about them.', 
                                          'download_size':397740,
                                              'real_size':397740,
                                                   'type':'application/json',
            },
            # 'gerechtcodes':{
            #                                         'url':'https://wetsuite.knobs-dials.com/datasets/gerechtcodes.json',      
            #                                     'version':'preliminary',
            #                           'short_description':'List of gerechtcodes as e.g. they appear in ECLI identifiers',
            #                               'download_size':0,
            #                                   'real_size':0,
            #                                        'type':'application/json',
            # },


            'wetnamen':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/wetnamen.db',
                                                'version':'preliminary',
                                      'short_description':'Some more and less official name variants that are used to refer to laws.',
                                          'download_size':4405025,
                                              'real_size':4405025,
                                                   'type':'application/json',
            },


            'tweedekamer-fracties-struc':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/fracties.json',
                                                'version':'preliminary',
                                      'short_description':'',
                                          'download_size':18596,
                                              'real_size':18596,
                                                   'type':'application/json',
            },
            'tweedekamer-fracties-membership-struc':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/fractie_membership.json',
                                                'version':'preliminary',
                                      'short_description':'',
                                          'download_size':502694,
                                              'real_size':502694,
                                                   'type':'application/json',
            },


            # Empty template
            # '':{
            #                                         'url':'https://wetsuite.knobs-dials.com/datasets/',
            #                                     'version':'preliminary',
            #                           'short_description':'',
            #                               'download_size':0,
            #                                   'real_size':0,
            #                                        'type':'application/json', # 'application/x-sqlite3'
            # },

        }
        
    else:
        try:
            index_data = wetsuite.helpers.net.download( _index_url )
            index_dict = json.loads( index_data )
        except:
            raise

    return index_dict





class Dataset:
    ''' If you're looking for details about the specific dataset, look at the .description

        Mostly meant to be instantiated by load()

        This class is provisional and likely to change. Right now it does little more than
        - put a description into a .description attribute 
        - put data into .data attribute
            without even saying what that is 
            though it's probably an interable giving individually useful things, and be able to tell you its len()gth
        ...also so that it's harder to accidentally dump gigabytes of text to your console.

        This is not the part that does the interpretation.
        This just contains its results.
    '''
    def __init__(self, description, data, name=''):
        #for key in self.data:
        #    setattr(self, key, self.data[key])
        # the above seems powerful but potentially iffy, so for now:
        self.data        = data 
        self.description = description 
        self.name        = name
        self.num_items   = len(self.data)
        
    def __str__(self):
        return '<wetsuite.datasets.Dataset name=%r num_items=%r>'%(self.name, self.num_items)


def merge_datasets(map): # maybe make this a @staticmethod on Dataset?
    '''
    If you want to take related datasets and see them on one object, this 
    - takes a dict like
        { dataset_object:'xml',
        dataset_object:'meta',
        dataset_object:'text'}
        }
    Ret
    '''
    ret = Dataset('joined dataset of %s. .data will be None but see attributes called %s'%(
        ', '.join(ds.name for ds in map.keys()),
        ', '.join(map.values())
        ), data=[])

    for dataset_object, attrib_name in map.items():
        setattr(ret, attrib_name, dataset_object.data)
    return ret



def _load_bare(dataset_name: str, verbose=None, force_refetch=False):
    ''' Takes a dataset name (that you learned of from the index),
          downloads it if necessary - after the first time it's cached in your home directory
          Returns the filename we fetched to
    '''
    global _index
    if _index == None:
        _index = fetch_index()

    if verbose is None:
        verbose = is_interactive() # only show if interactive

    if dataset_name not in _index:
        raise ValueError("Do not know dataset name %r"%dataset_name)

    dir_dict = wetsuite.helpers.util.wetsuite_dir()
    ws_dir       = dir_dict['wetsuite_dir']
    datasets_dir = dir_dict['datasets_dir']


    ## figure out path in that directory
    dataset_details = _index[dataset_name]
    data_url        = dataset_details['url']
    location_hash   = wetsuite.helpers.util.hash_hex( data_url.encode('utf8') ) # quick and dirty way to get a safe filename regardless of index contents
    data_path       = os.path.join( datasets_dir, location_hash )      # CONSIDER: using dataset_name instead of location_hash  (BUT that would mean restricting the characters allowed in there)
    # right now the data_path is a single file per dataset, expected to be a JSON file. TODO: decide on whether that is our standard, or needs changing

    # If we don't have it in our cache, or a re-fetch was forced, then download it.
    if force_refetch or not os.path.exists( data_path ):
        if verbose:
            print( "Downloading %r to %r"%(data_url, data_path), file=sys.stderr )

        # CONSIDER: using context manager variant if that's cleaner
        tmp_handle, tmp_path = tempfile.mkstemp(prefix='tmp_dataset_download', dir=ws_dir)
        os.close(tmp_handle)  # the open file handle is fairly secure, but here we only care about a non-clashing filename

        # download it to that temporary filename
        wetsuite.helpers.net.download( data_url, tofile_path=tmp_path, show_progress=verbose)

        # TODO: detect arrow (file magic: b'ARROW1')

        ## if it was compressed, decompress it in the cache - as part of the download, not the load
        # compressed into its fina place.   There is a race condition in multiple loads() of the same thing. CONSIDER: fixing that via a second temporary file
        # CONSIDER: it may be preferable to store it compressed, and decompress every load. Or at least make this a parameter
        def decompress_stream(instream, outstream):
            uncompressed_data_bytes = 0
            while True:
                data = instream.read( 2*1048576 )
                if len(data)==0:
                    break
                outstream.write(data)
                uncompressed_data_bytes += len(data)
                if verbose:
                    print( "\rDecompressing... %3sB    "%(wetsuite.helpers.format.kmgtp( uncompressed_data_bytes, kilo=1024 ), ), end='', file=sys.stderr )
            if verbose:
                print('', file=sys.stderr)

        if data_url.endswith('.xz'): # or file magic, b'\xfd7zXZ\x00\x00'
            import lzma # standard library since py3.3, before that we could fall back to backports.lzma
            with lzma.open(tmp_path) as compressed_file_object:
                with open(data_path,'wb') as write_file_object:
                    decompress_stream( compressed_file_object, write_file_object )
            os.unlink( tmp_path )

        elif data_url.endswith('.bz2'):
            #print('Decompressing...', file=sys.stderr)
            with bz2.BZ2File(tmp_path, 'rb') as compressed_file_object:
                with open(data_path,'wb') as write_file_object:
                    decompress_stream( compressed_file_object, write_file_object )
            print('  done.', file=sys.stderr)
            os.unlink( tmp_path )

        # CONSIDER: add gz and zip cases, because they're standard library anyway

        else: # assume it was uncompressed, just move it into place
            os.rename( tmp_path, data_path )

    return data_path


def load(dataset_name: str, verbose=None, force_refetch=False, augment=True):
    ''' Takes a dataset name (that you learned of from the index),
        downloads it if necessary - after the first time it's cached in your home directory

        Returns a Dataset object - which is a container with little more than  
        - a .description string
        - a .data member, some kind of iterable of iterms.   The .description will mention what .data will contain and should give an example of how to use it.
        

        CONSIDER: have load datasetname-* automatically use merge_datasets,
            one for each matched datasets, with an attribute named for the last bit of the dataset name. 


        verbose - tells you more about the download (on stderr)
           can be given True or False. By default, we try to detect whether we are in an interactive context.
        force_refetch - whether to remove the current contents before fetching
           dataset naming should prevent the need for this (except if you're the wetsuite programmer)
    '''
    def path_to_data(data_path):
        ' read from disk, return the data and description regardless of what it is '
        f = open(data_path,'rb')
        first_bytes = f.read(15)
        f.seek(0)

        if first_bytes == b'SQLite format 3':
            f.close()
            data        = wetsuite.helpers.localdata.LocalKV( data_path, None, None, read_only=True ) # the type enforcement is irrelevant when opened read-only
            description = data._get_meta('description', missing_as_none=True)
            if data._get_meta('valtype', missing_as_none=True) == 'msgpack': # This is very hackish - TODO: avoid this
                data.close()
                data = wetsuite.helpers.localdata.MsgpackKV( data_path, None, None, read_only=True) 

        else: # Assume JSON - expected to be a dict with two main keys
            loaded = json.loads( f.read() ) 
            f.close()
            data        = loaded.get('data')
            description = loaded.get('description')
        return (data, description)

    #if '*' in dataset_name:
    global _index
    if _index == None:
        _index = fetch_index()
    all_dataset_names = list( _index.keys() )

    import fnmatch
    dataname_matches = fnmatch.filter(all_dataset_names, dataset_name)
    if len(dataname_matches)   == 0:
        raise ValueError("Your dataset pattern %r matched none of %s"%(dataset_name, ', '.join(all_dataset_names)))
    
    elif len(dataname_matches) == 1:
        data_path = _load_bare( dataname_matches[0] )
        data, description = path_to_data( data_path )
        data_path = _load_bare( dataset_name=dataname_matches[0], verbose=verbose, force_refetch=force_refetch )
        return Dataset( data=data, description=description, name=dataname_matches[0] )

    else:            # implied  >=1

        datasets = {} # list of (dataset, lastpartofname)

        for dataname_match in dataname_matches:
            data_path = _load_bare( dataname_match )
            data, description = path_to_data( data_path )
            data_path = _load_bare( dataset_name=dataname_match, verbose=verbose, force_refetch=force_refetch )
            datasets[ Dataset( data=data, description=description, name=dataname_match ) ] = dataname_match.rsplit('-')[-1]
        print( datasets)

        return merge_datasets( datasets )
        




        
