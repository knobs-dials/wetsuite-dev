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

import sys, os, json, hashlib, tempfile, bz2

import wetsuite.helpers.net
import wetsuite.helpers.localdata
from wetsuite.helpers.notebook import is_interactive


def hash(data: bytes):
    ' Given some byte data, calculate SHA1 hash.  Returns that hash as a hex string. '
    s1h = hashlib.sha1()
    s1h.update( data )
    return s1h.hexdigest()


def wetsuite_dir():
    ''' Figure out where we can store data.
    
        Returns a dict with keys mentioning directories:
          wetsuite_dir: a directory in the user profile we can store things
          datasets_dir: a directory inside wetsuite_dir first that datasets.load() will put dataset files in
          stores_dir:   a directory inside wetsuite_dir that localdata.open_store will put sqlite files in

          CONSIDER: a tmp_dir
          CONSIDER: listen to an expicit and/or environment variable to override that base directory, 
                    to allow people to direct where to store this (might be useful e.g. on clustered filesystems)

        TODO: more checking, so we can give clearer errors
    '''
    ret = {}

    # Note: expanduser("~") works on all OSes including windows, 
    #   these additional tests are mainly for the case of AD-managed workstations, to try to direct it to store it in a shared area
    #   HOMESHARE is picked up (and preferred over USERPROFILE) because in this context, USERPROFILE might be a local, non-synced directory
    #   even if most of its contents are junctions to places that _are_ 
    
    userprofile = os.environ.get('USERPROFILE') # we assume these are only filled when it's actually windows - we could test that too via os.name or platform.system()
    homeshare   = os.environ.get('HOMESHARE')
    chose_dir = None
    if homeshare is not None:
        r_via_hs = os.path.join(homeshare, 'AppData', 'Roaming')
        if os.path.exists( r_via_hs ):
            chose_dir = os.path.join( r_via_hs, '.wetsuite' )
    elif userprofile is not None:
        r_via_up = os.path.join(userprofile, 'AppData', 'Roaming')
        if os.path.exists( r_via_up ):
            chose_dir = os.path.join( r_via_up, '.wetsuite' )

    if chose_dir is None:  # probably linux or osx, or weird windows
        home_dir = os.path.expanduser("~")
        ret['wetsuite_dir'] = os.path.join( home_dir, '.wetsuite' )
    else:
        ret['wetsuite_dir'] = chose_dir
    
    if not os.path.exists( ret['wetsuite_dir'] ):
        os.makedirs( ret['wetsuite_dir'] )
    if not os.access(ret['wetsuite_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory, %r"%ret['wetsuite_dir'])

    ret['datasets_dir'] = os.path.join( ret['wetsuite_dir'], 'datasets' )
    if not os.path.exists( ret['datasets_dir'] ):
        os.makedirs( ret['datasets_dir'] )
    if not os.access(ret['datasets_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory of datasets, %r"%ret['datasets_dir'])

    ret['stores_dir'] = os.path.join( ret['wetsuite_dir'], 'stores' )
    if not os.path.exists( ret['stores_dir' ] ):
        os.makedirs( ret['stores_dir'] )
    if not os.access(ret['stores_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory of datasets, %r"%ret['stores_dir'])
    
    return ret



class Dataset:
    ''' If you're looking for details about the specific dataset, look at the .description

        This class is provisional and likely to change. Right now it does little more than
        - put a description into a .description attribute 
        - put data into .data attribute
            without even saying what that is 
            though it's probably an interable giving individually useful things, and be able to tell you its len()gth
        ...also so that it's harder to accidentally dump gigabytes of text to your console.
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
    



def load(dataset_name: str, verbose=None, force_refetch=False):
    ''' Takes a dataset name (that you learned of from the index),
        - downloads it if necessary - after the first time it's cached in your home directory
        - loads it into memory
        
        Returns a Dataset object - which is a container with 
        - a .description string 
        - a .data member that is probably some nested python structure

        verbose - tells you more about the download (on stderr)
           can be given True or False. By default, we try to detect whether we are in an interactive context.
        force_refetch - whether to remove the current contents before fetching
           dataset naming should prevent the need for this (except if you're the wetsuite programmer)
    '''
    global _index
    if _index == None:
        _index = fetch_index()

    if verbose is None:
        verbose = is_interactive() # only show if interactive

    if dataset_name not in _index:
        raise ValueError("Do not know dataset name %r"%dataset_name)

    ws_dir       = wetsuite_dir()['wetsuite_dir']
    datasets_dir = wetsuite_dir()['datasets_dir']


    ## figure out path in that directory
    dataset_details = _index[dataset_name]
    data_url        = dataset_details['url']
    location_hash   = hash( data_url.encode('utf8') ) # quick and dirty way to get a safe filename regardless of index contents
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

    ### Finally the real loading bit: read from disk, and return.
    f = open(data_path,'rb')
    first_bytes = f.read(15)
    f.seek(0)

    if first_bytes == b'SQLite format 3':
        f.close()
        data        = wetsuite.helpers.localdata.LocalKV( data_path, None, None, read_only=True ) # the type enforcement is irrelevant when opened read-only
        description = data._get_meta('description', missing_as_none=True)

    else: # Assume JSON - expected to be a dict with two main keys
        loaded = json.loads( f.read() ) 
        f.close()
        data        = loaded.get('data')
        description = loaded.get('description')

    return Dataset( data=data, description=description, name=dataset_name )

        



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
    if True:
        index_dict = {
            'rvsadviezen':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/raadvanstate_adviezen.json.bz2',
                                                'version':'preliminary', 
                                      'short_description':'The advice under https://raadvanstate.nl/adviezen/ provided as plain text in a nested structure with metadata. ',  
                                          'download_size':5460023,
                                              'real_size':34212068,   # or maybe more directly readable  '5MB' and '34MB'?
                                                   'type':'application/json',
            },

            'kamervragen':{
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
                                          'download_size':168996888,  
                                              'real_size':2981859328,
                                                   'type':'application/json',
            },

            'cvdr-mostrecent-xml':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/cvdr_lastonly_xml.db.xz',
                                                'version':'preliminary',
                                      'short_description':'The latest expression from each CVDR work',
                                          'download_size':603843736,  
                                              'real_size':5586030592,
                                                   'type':'application/json',
            },
                
            'woobesluiten':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/',
                                                'version':'preliminary', 
                                      'short_description':'',    
                                          'download_size':0,   
                                              'real_size':0,
                                                   'type':'application/json',
            },

            'kansspelsancties-txt':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/kansspelautoriteit_plain.json.bz2', 
                                                'version':'preliminary', 
                                      'short_description':'Sanction decisions, in plain text, extracted from from the case PDFs under https://kansspelautoriteit.nl/aanpak-misstanden/sanctiebesluiten/',
                                          'download_size':1147517,
                                              'real_size':7604025,
                                                   'type':'application/json',
            },

            # just metadata, no text documents to analyse
            'gemeentes':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/gemeentes.json',    
                                                'version':'preliminary', 
                                      'short_description':'List of municipalities, and some basic information about them.', 
                                          'download_size':397740,
                                              'real_size':397740,
                                                   'type':'application/json',
            },
            'gerechtcodes':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/gerechtcodes.json',      
                                                'version':'preliminary',
                                      'short_description':'List of gerechtcodes as e.g. they appear in ECLI identifiers',
                                          'download_size':0,
                                              'real_size':0,
                                                   'type':'application/json',
            },

            'wetnamen':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/wetnamen.json',
                                                'version':'preliminary',
                                      'short_description':'Some more and less official name variants that are used to refer to laws.',
                                          'download_size':4405025,
                                              'real_size':4405025,
                                                   'type':'application/json',
            },

            'fracties':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/wetnamen.json',
                                                'version':'preliminary',
                                      'short_description':'Some more and less official name variants that are used to refer to laws.',
                                          'download_size':4405025,
                                              'real_size':4405025,
                                                   'type':'application/json',
            },

            'fractie_meme':{
                                                    'url':'https://wetsuite.knobs-dials.com/datasets/wetnamen.json',
                                                'version':'preliminary',
                                      'short_description':'Some more and less official name variants that are used to refer to laws.',
                                          'download_size':4405025,
                                              'real_size':4405025,
                                                   'type':'application/json',
            },

            #'fracties_membership': {  }

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

