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
from wetsuite.helpers.notebook import is_interactive


def hash(data: bytes):
    ' Calculate SHA1 hash of some byte data,  returns that hash as a hex string. '
    s1h = hashlib.sha1()
    s1h.update( data )
    return s1h.hexdigest()




class Dataset:
    ''' This object does little more than 
        * take a dict
        * put its ['description'] into a .description attribute    
            that describes the structure to that data.
        * put its ['data'] into a  .data attribute        
            that contains all the data

        ...and exists laregely so that a str() doesn't accidentally print hundreds of megabytes to your console.

        NOTE: This is provisional, and likely to change.
    '''
    def __init__(self, dict_data, name=''):
        self._data = dict_data

        #for key in self.data:
        #    setattr(self, key, self.data[key])
        # the above seems powerful but potentially iffy, so for now:
        self.data        = dict_data.get('data')
        self.description = dict_data.get('description')
        self.name        = name
        self.num_items   = len(self.data)
        
    def __str__(self):
        return '<wetsuite.datasets.Dataset name=%r num_items=%r>'%(self.name, self.num_items)



def load(dataset_name: str, verbose=None, force_refetch=False):
    ''' Takes a dataset name,
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

    ### Figure out where the dataset is stored, or should be
    ## check directory
    home_dir = os.path.expanduser("~")
    data_dir = os.path.join( home_dir, '.wetsuite', 'datasets' )

    if not os.path.exists( data_dir ): 
        os.makedirs( data_dir )

    if not os.access(data_dir, os.W_OK):
        raise OSError("We cannot write to our data directory, %r"%data_dir)
    # TODO: more permission checking, so we could give clearer errors


    ## figure out path in that directory
    dataset_details = _index[dataset_name]
    data_url        = dataset_details['url']
    location_hash   = hash( data_url.encode('utf8') ) 
    data_path = os.path.join( data_dir, location_hash )      # CONSIDER: using dataset_name instead of location_hash  (BUT that would mean restricting the characters allowed in there)
    # right now the data_path is a single file per dataset, expected to be a JSON file. TODO: decide on whether that is our standard, or needs changing

    # If we don't have it in our cache, or a re-fetch was forced, then download it.
    if force_refetch or not os.path.exists( data_path ):
        if verbose:
            print( "Downloading %r to %r"%(data_url, data_path), file=sys.stderr )

        # CONSIDER: using context manager variant if that's cleaner
        tmp_handle, tmp_path = tempfile.mkstemp(prefix='download', dir=data_dir)
        os.close(tmp_handle)  # the open file handle is fairly secure, but here we only care about a non-clashing filename

        # download it to that temporary filename
        wetsuite.helpers.net.download( data_url, tofile_path=tmp_path, show_progress=verbose)

        ## if it was compressed, decompress it in the cache - as part of the download, not the load
        # compressed into its fina place.   There is a race condition in multiple loads() of the same thing. CONSIDER: fixing that via a second temporary file
        # CONSIDER: it may be preferable to store it compressed, and decompress every load. Or at least make this a parameter
        if data_url.endswith('.bz2'):
            #print('Decompressing...', file=sys.stderr)
            uncompressed_data_bytes = 0
            with bz2.BZ2File(tmp_path, 'rb') as compressed_file_object:
                with open(data_path,'wb') as write_file_object:
                    while True:
                        data = compressed_file_object.read( 2*1048576 )
                        if len(data)==0:
                            break
                        write_file_object.write(data)
                        uncompressed_data_bytes += len(data)
                        if verbose:
                            print( "\rDecompressing... %3sB"%(wetsuite.helpers.format.kmgtp( uncompressed_data_bytes, kilo=1024 ), ), end='', file=sys.stderr )
                if verbose:
                    print('', file=sys.stderr)
            print('  done.', file=sys.stderr)
            os.unlink( tmp_path )
        else: # assume it was uncompressed, just move it into place
            os.rename( tmp_path, data_path )
        # CONSIDER: add gz and zip cases, because they're standard library anyway

    ### Finally the real loading bit: read from disk, and return.
    with open(data_path) as f:
        return Dataset( dict_data=json.loads( f.read() ), name=dataset_name )
        



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
    return _index.keys()


def fetch_index():
    ''' Index is expected to be
          {'datasetname':{url:'http://example.com/dataset.tgz', 'description':'Blah'}}

        CONSIDER: keep hosting generic (HTTP fetch?) so that any hoster will do.
    '''
    if True:
        index_dict = {
            'kamervragen':         {  'url':'https://wetsuite.knobs-dials.com/datasets/kamervragen.json.bz2',              'version':'preliminary', 'short_description':'',    },
            'kansspelautoriteit':  {  'url':'https://wetsuite.knobs-dials.com/datasets/kansspelautoriteit_plain.json.bz2', 'version':'preliminary', 'short_description':'',    },
            'rvsadviezen':         {  'url':'https://wetsuite.knobs-dials.com/datasets/raadvanstate_adviezen.json.bz2',    'version':'preliminary', 'short_description':'Plain text version of advice under https://raadvanstate.nl/adviezen/',   },

            # just metadata, no text
            'gemeentes':            {  'url':'https://wetsuite.knobs-dials.com/datasets/gemeentes.json',                    'version':'preliminary', 'short_description':'List of municipalities',    },
            #'fracties_membership': {  }
        }
        
    else:
        try:
            index_data = wetsuite.helpers.net.download( _index_url )
            index_dict = json.loads( index_data )
        except:
            raise

    return index_dict

