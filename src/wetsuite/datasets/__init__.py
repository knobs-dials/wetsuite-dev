#!/usr/bin/python3
'''
Fetch and load already-created datasets that we provide. (to see a list of actual datasets, look for the wetsuite_datasets.ipynb notebook)

As this is often structured data, each dataset may work a little differently, 
so there is an describe() to get you started, that each dataset should fill out.

CONSIDER:
  - "treat collections of files as datasets?" or is that your own responsibility
    ...i.e. more of a notebook "how to deal with pdf, odt, and make that a thing to iterate through"


TODO: 
  - decide how often to re-fetch the index client-side. 
    Each interpreter (which is what it does right now)?   
    Store and base on mtime with possible override? 
    Decide it's cheap enough to fetch each time? (but fall back onto stored?)
  - decide how to store and access. For very large datasets we may want something like HDF5 
    because right now we don't have a choice but to have all the dataset in RAM
'''

import sys
import os
import re
import json
import time
import tempfile
import bz2
import fnmatch
import lzma # standard library since py3.3, before that we could fall back to backports.lzma
import zipfile

import wetsuite.helpers.util
import wetsuite.helpers.net
import wetsuite.helpers.date
import wetsuite.helpers.localdata
from wetsuite.helpers.notebook import is_interactive


### Index of current datasets
# TODO: figure out hosting, and where to put the base URL

_INDEX_URL = 'https://wetsuite.knobs-dials.com/datasets/index.json'
_index_data = None  # should be None, or a dict once loaded
_index_fetch_time = 0
_index_fetch_no_more_often_than_sec = 600


def generated_today_text():
    ' Used when generating datasets, returns a string like "This dataset was generated on 2024-02-02" '
    return 'This dataset was generated on %s'%( wetsuite.helpers.date.date_today().strftime("%Y-%m-%d") )


def list_datasets():
    ' fetch index, report dataset names (see fetch_index if you also want the details)'
    global _index_data
    fetch_index()
    return sorted( _index_data.keys() )
    #return list( _index.items() )


def fetch_index():
    ''' Index is expected to be a list of dicts, each with keys includin
          - url
          - version             (should probably become semver)
          - description_short   one-line summary of what this is
          - description         longer description, perhaps with some example data
          - download_size       how much transfer you'll need
          - real_size           Disk storage we expect to need once decompressed
          - download_size_human, real_size_human: more readable version, 
            e.g. where real_size might be the integer 397740, real_size_human would be 388KiB
          - type                content type of dataset 
         
        TODO: an example

        CONSIDER: keep hosting generic (HTTP fetch?) so that any hoster will do.
    '''
    global _index_data, _index_data, _index_fetch_time, _index_fetch_no_more_often_than_sec

    if (_index_data is None  or
         time.time() - _index_fetch_time > _index_fetch_no_more_often_than_sec):
        #print('FETCHING INDEX')
        try:
            _fetched_data = wetsuite.helpers.net.download( _INDEX_URL )
            _index_data = json.loads( _fetched_data )
            #print("Fetched index")
            _index_fetch_time = time.time()
        except Exception as e:
            raise
    #else:
    #    print('CACHED INDEX')
    return _index_data



class Dataset:
    '''
    If you're looking for details about the specific dataset, look at the .description

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


    def export_files(self, in_dir_path=None, to_zipfile_path=None):
        ''' This is primarily for people who want to see their data in file form.

            It also only makes sense when the dataset values are bytes objects
        '''

        if to_zipfile_path is not None:

            if os.path.exists(to_zipfile_path):
                raise RuntimeError("Target ZIP file (%r) exists, playing safe and refusing. If you wanted a new export, rename or remove it."%to_zipfile_path)
            zob = zipfile.ZipFile(to_zipfile_path, 'a', compression=zipfile.ZIP_DEFLATED, allowZip64=True)

        if in_dir_path is not None:
            if not os.path.exists(in_dir_path):
                os.mkdir(in_dir_path)

        if in_dir_path is None and to_zipfile_path is None:
            raise ValueError("Specify either in_dir_path to dump a lot of files to that directory, or to_zipfile_path to dump all into a single ZIP file")


        i=0
        for key, value in self.data.items():
            i += 1
            #if i > 200:
            #    break

            ## figure out bytes to store,    also estimate decent file extension from the content
            if isinstance(value, bytes):
                if b'<?xml' in value[:50]:
                    typ   = 'xml'
                else:
                    typ   = 'bin'
            elif isinstance(value, dict):
                typ   = 'json' # assumption based on what datasets we currently provide, may not keep in the future
                value = json.dumps(value).encode('u8')
            elif isinstance(value, str):
                typ   = 'txt'
                value = value.encode('u8')
            else:
                raise ValueError("Do not know what to do with %r"%type(value))


            safe_fn = '%08d_%s__%s.%s'%(
                i,                                                            # for uniqueness
                wetsuite.helpers.util.hash_hex(key)[:12],                     # likely to make it unique even without that counter
                re.sub('[^A-Za-z0-9_-]','', re.sub('[.:/]+','-',key))[:220],  # not for uniqueness, but for some indication of what this is. Primarily aimed at URLs
                typ[:5],
            )[:254]


            ## write out
            if in_dir_path is not None:
                ffn = os.path.join( in_dir_path, safe_fn )

                if os.path.exists(ffn):
                    raise IOError("You probably did not mean to overwrite %r, please remove anything existing before retrying. "%ffn)
                # implied else: either it doesn't exist, or overwrite==True

                with open(ffn, 'wb') as f:
                    f.write( value )

            if to_zipfile_path is not None:
                # note: for content you know won't compress well, you can save some time with , you can compress_type=zipfile.ZIP_STORED
                zob.writestr( safe_fn , value )

        if to_zipfile_path is not None:
            zob.close()





def _load_bare(dataset_name: str, verbose=None, force_refetch=False):
    ''' Note: You normally would use load(), which takes the same name but gives you a usable object, not a filename

        Takes a dataset name (that you learned of from the index),
        Downloads it if necessary - after the first time it's cached in your home directory

        If compressed, will uncompress. 
        Does not think about the type of data
        
        @return: the filename we fetched to
    '''
    global _index_data
    if _index_data is None:
        _index_data = fetch_index()

    if verbose is None:
        verbose = is_interactive() # only show if interactive

    if dataset_name not in _index_data:
        raise ValueError( "Do not know dataset name %r"%dataset_name )

    dir_dict = wetsuite.helpers.util.wetsuite_dir()
    ws_dir       = dir_dict['wetsuite_dir']
    datasets_dir = dir_dict['datasets_dir']


    ## figure out path in that directory
    dataset_details = _index_data[dataset_name]
    data_url        = dataset_details['url']
    # quick and dirty way to get a safe filename regardless of index contents
    location_hash   = wetsuite.helpers.util.hash_hex( data_url.encode('utf8') )
    # CONSIDER: using dataset_name instead of location_hash
    #   (BUT that would mean restricting the characters allowed in there)
    data_path       = os.path.join( datasets_dir, location_hash )
    # right now the data_path is a single file per dataset, expected to be a JSON file.
    # TODO: decide on whether that is our standard, or needs changing

    # If we don't have it in our cache, or a re-fetch was forced, then download it.
    if force_refetch or not os.path.exists( data_path ):
        if verbose:
            print( "Downloading %r to %r"%(data_url, data_path), file=sys.stderr )

        # CONSIDER: using context manager variant if that's cleaner
        tmp_handle, tmp_path = tempfile.mkstemp(prefix='tmp_dataset_download', dir=ws_dir)
        os.close(tmp_handle)  # the open file handle is fairly secure, but here we only care about a non-clashing filename

        # download it to that temporary filename
        wetsuite.helpers.net.download( data_url, tofile_path=tmp_path, show_progress=verbose)

        ## if it was compressed, decompress it in the cache -
        # as part of the download, not the load compressed into its fina place.
        # There is a race condition in multiple loads() of the same thing. CONSIDER: fixing that via a second temporary file
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
                    print( "\rDecompressing... %3sB    "%(wetsuite.helpers.format.kmgtp( uncompressed_data_bytes, kilo=1024 ), ),
                           end='', file=sys.stderr )
            if verbose:
                print('', file=sys.stderr)

        if data_url.endswith('.xz'): # or file magic, b'\xfd7zXZ\x00\x00'
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


def _path_to_data(data_path):
    ''' Given a filename,
        return the data and description (based on contents)
        regardless of what data type it is
    '''
    f = open(data_path,'rb')
    first_bytes = f.read(15)
    f.seek(0)

    if first_bytes == b'SQLite format 3':
        f.close()

        # the type enforcement is irrelevant when opened read-only
        data = wetsuite.helpers.localdata.LocalKV( data_path, None, None, read_only=True )

        description = data._get_meta('description', missing_as_none=True)
        # This seems very hackish - TODO: avoid this
        if data._get_meta('valtype', missing_as_none=True) == 'msgpack':
            data.close()
            data = wetsuite.helpers.localdata.MsgpackKV( data_path, None, None, read_only=True)

    elif first_bytes.strip().startswith(b'{'): # Assume that's a decent indicator of JSON
        # expected to be a dict with two main keys, 'data' and 'description'
        loaded = json.loads( f.read() )
        f.close()

        # TODO: remove the need for JSON, or at least make this alternative go away
        #       by being more consistent in dataset generation
        if 'description' in loaded:
            data        = loaded.get('data')
            description = loaded.get('description')
        else:
            raise ValueError("This JSON does not have the structure we expect.")
    else:
        f.close()
        raise ValueError("Don't know how to deal with file called %r  that starts with %r"%(
                         os.path.basename(data_path), first_bytes))

    return (data, description)


def load(dataset_name: str, verbose=None, force_refetch=False, augment=True):
    ''' Takes a dataset name (that you learned of from the index),
        downloads it if necessary - after the first time it's cached in your home directory

        Returns a Dataset object - which is a container with little more than  
          - a .description string
          - a .data member, some kind of iterable of iterms.
            The .description will mention what .data will contain 
            and should give an example of how to use it.

        CONSIDER: have load('datasetname-*') automatically merge_datasets,
        one for each matched datasets, with an attribute named for the last bit of the dataset name.
        However, this only makes sense if dataset convention _and_ dataset naming convention are always considered,
        so maybe the benefit is not enough here.

        @param verbose: tells you more about the download (on stderr)
        can be given True or False. By default, we try to detect whether we are in an interactive context.

        @param force_refetch: whether to remove the current contents before fetching
        dataset naming should prevent the need for this (except if you're the wetsuite programmer)
    '''

    #if '*' in dataset_name:
    global _index_data
    if _index_data is None:
        _index_data = fetch_index()
    all_dataset_names = list( _index_data.keys() )

    dataname_matches = fnmatch.filter(all_dataset_names, dataset_name)
    if len(dataname_matches)   == 0:
        raise ValueError("Your dataset name/pattern %r matched none of %s"%(dataset_name, ', '.join(all_dataset_names)))

    elif len(dataname_matches) == 1:
        data_path = _load_bare( dataname_matches[0] )
        data, description = _path_to_data( data_path )
        data_path = _load_bare( dataset_name=dataname_matches[0], verbose=verbose, force_refetch=force_refetch )
        return Dataset( data=data, description=description, name=dataname_matches[0] )

    else:            # implied  >=1
        raise ValueError("Your dataset pattern %r matched %d of %s. We might give you a merger in the future, but right now, choose more specifically."%(
            dataset_name, 
            len(dataname_matches),
            ', '.join(all_dataset_names)))

        # datasets = {} # list of (dataset, lastpartofname)

        # for dataname_match in dataname_matches:
        #     data_path = _load_bare( dataname_match )
        #     data, description = _path_to_data( data_path )
        #     data_path = _load_bare( dataset_name=dataname_match, verbose=verbose, force_refetch=force_refetch )
        #     datasets[ Dataset( data=data, description=description, name=dataname_match ) ] = dataname_match.rsplit('-')[-1]
        # print( datasets)
    
        # return merge_datasets( datasets )



# @classmethod
# def files_as_dataset(self, in_dir):
#     ''' Notes that this does _nothing_ for you other than making it a little easier to iterate though the _contents_ of these files '''
#     store = wetsuite.helpers.localdata.LocalKV( ':memory:', None, None )
#     for r, ds, fs in os.walk(in_dir):
#         for fn in fs:
#             ffn = os.path.join( r, fn )
#             #if os.path.is_file():
#             with open(ffn,'rb') as f:
#                 store.put(ffn, f.read() )
#     ret = Dataset(  description='Files loaded from %r'%in_dir,
#                     data=store,
#                     name='filesystem-'+re.sub('[^A-Za-z0-9]+','-',in_dir)  )
#     return ret
