#!/usr/bin/python3
' network/fetch related helper functions '
import sys

import requests

import wetsuite.helpers.format
from wetsuite.helpers.notebook import is_interactive



def download( url:str, tofile_path:str = None, show_progress:bool=None, chunk_size=131072 ):
    ''' Wrapper around requests.get() with some optional extras.

        One of them is the option to stream-download to filesystem:     
         if tofile is not None, we stream-save to that file path, by name  (and return None)
            tofile is None      we return the data as a bytes object (which means we kept it in RAM, which may not be wise for huge downloads) 
        uses requests's stream=True, which seems chunked HTTP transfer, or just a TCP window? TOCHECK

        show_progress: whether to print/show output while downloading.
    '''
    if tofile_path is not None:
        f = open(tofile_path,'wb')
        def handle_chunk(data):
            f.write(data)
    else:
        ret = []
        def handle_chunk(data):
            ret.append(data)

    def progress_update():
        bar = ''
        if total_length is not None:
            frac = float(fetched)/total_length
            width = 50
            bar = '[%s%s]'%(
                '=' * int(frac*width), 
                ' ' * (width-int(frac*width))
            )
        return "\rDownloaded %8sB  %s"%(wetsuite.helpers.format.kmgtp( fetched, kilo=1024 ), bar)

    response = requests.get(url, stream=True) # TODO: 
    total_length = response.headers.get('content-length')

    if not response.ok:
        raise ValueError( response.status_code )

    if total_length is not None: 
        total_length = int(total_length)
        #show_progress = True
        #chunkrange = range(total_length/chunksize) 

    fetched = 0
    for data in response.iter_content(chunk_size=chunk_size):
        handle_chunk(data)
        fetched += len(data)
        if show_progress:
            sys.stderr.write( progress_update() )    
            sys.stderr.flush()

    if show_progress:
        sys.stderr.write( progress_update()+'\n' )
        sys.stderr.flush()

    if tofile_path is None:
        return b''.join( ret )

