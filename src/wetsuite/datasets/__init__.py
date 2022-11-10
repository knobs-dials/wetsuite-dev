#!/usr/bin/python3
''' Fetch and load already-created datasets that we provide.

    As this is often structured data, each dataset may work a little differently, 
    so there is an describe() to get you started, that each dataset should fill out.

    TODO: 
    * think about having stable datasets, for things like benchmarking
      maybe "any dataset that has a date is fixed, any other may be updated over time" ?

    CONSIDER:
    * hosting on github, or some other sensible place?
    * Make datasets shared-and-installable , e.g. like spacy does? (maybe not?)
'''

import sys, os, json, hashlib, tempfile, bz2

import wetsuite.helpers.net


class Dataset:
    ''' This object does little more than 
        * have an  .data attribute        that contains all the data
        * have a   .description attribute that describes the structure to that data.

        (...and exists in part to not accidentally print the entire dataset to your console)
    '''
    def __init__(self, dict_data):
        self._data = dict_data

        self.data        = dict_data.get('data')
        self.description = dict_data.get('description')
        #for key in self.data:
        #    setattr(self, key, self.data[key])



def hash(data):
    ' calculate SHA1 hash of some data. '
    s1h = hashlib.sha1()
    s1h.update( data )
    return s1h.hexdigest()



def load(dataset_name, show_progress=True):
    ''' Loads a dataset into memory, by name.   

        Which may involve fetching it first. Fetched datasets are cached in your home directory.
    '''
    ### Figure out where it is, or would be, stored
    home_dir = os.path.expanduser("~")
    data_dir = os.path.join( home_dir, '.wetsuite', 'datasets' )

    # TODO: more permission checking so we could give clearer errors?
    if not os.path.exists( data_dir ): 
        os.makedirs( data_dir )

    if not os.access(data_dir, os.W_OK):
        raise OSError("We cannot write to our data directory, %r"%data_dir)

    if dataset_name not in _index:
        raise ValueError("Do not know dataset name %r"%dataset_name)

    dataset_details = _index[dataset_name]
    data_url        = dataset_details['url']
    location_hash   = hash( data_url.encode('utf8') )


    ### If we don't have it in our cache, then download it.
    data_path = os.path.join( data_dir, location_hash )
    if not os.path.exists( data_path ):
        
        #with open(data_path,'wb') as f:
        print( "Downloading %r to %r"%(data_url, data_path) )

        tmp_handle, tmp_path = tempfile.mkstemp(prefix='download', dir=data_dir)
        os.close(tmp_handle) # open file handle is sorta secure, but that's not really our goal here

        wetsuite.helpers.net.download( data_url, tofile_path=tmp_path, show_progress=show_progress)

        ### THINK: it may be preferable to store it compressed, and decompress every load. Or at least make this a parameter
        # if it was compressed, decompress it in the cache
        if data_url.endswith('.bz2'):
            #print('Decompressing...', file=sys.stderr)
            uncompressed_data_bytes = 0
            with bz2.BZ2File(tmp_path, 'rb') as compressed_file_object:
                with open(data_path,'wb') as write_file_object:
                    while True:
                        data = compressed_file_object.read( 1048576 )
                        if len(data)==0:
                            break
                        write_file_object.write(data)
                        uncompressed_data_bytes += len(data)
                        if show_progress:
                            print( "\rDecompressing... %3sB"%(wetsuite.helpers.format.kmgtp( uncompressed_data_bytes, kilo=1024 ), ), end='' )

            print('  done.', file=sys.stderr)
            os.unlink( tmp_path )
        # CONSIDER: add gz, zip, because they're standard library anyway
        else: # assume it was uncompressed
            os.rename( tmp_path, data_path )


    ### Finally the real bit: read from disk, and return.
    with open(data_path) as f:
        return Dataset( json.loads( f.read() ) )
        



### Index of current datasets
# this needs to become a remotely stored thing.  Right now it's hardcoded because I'm figuring out the loading API to be in general,

_index_url = 'https://'

_index = {
    'kamervragen':{  'url':'https://beep.knobs-dials.com/datasets/kamervragen.json.bz2',   'description':'',   'version':'preliminary'  }
}


def list_datasets():
    if _index==None:
        fetch_index()
    return _index.keys()


def fetch_index():
    ''' Index is expected to be
          {'datasetname':{url:'http://example.com/dataset.tgz', 'description':'Blah'}}

        Current hosting is on github. TODO: keep it generic so that any hoster will do?
    '''
    index_data = wetsuite.helpers.net.download( _index_url )

    try:
        index_dict = json.loads( index_data )
    except:
        raise


