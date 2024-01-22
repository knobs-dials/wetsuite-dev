#!/usr/bin/python3
' network related helper functions, such as fetching from URLs '
import sys

import requests

import wetsuite.helpers.format


def download( url:str, tofile_path:str = None, show_progress=None, chunk_size=131072, timeout=10 ):
    ''' Mostly just requests.get(), for byte-data download, with some optional extras,
        that make it a little more specifically useful for downloading.

        the main addition is the option to stream-download to filesystem:     
          - if tofile is not None, we stream-save to that file path, by name  (and return None)
          - if tofile is None      we return the data as a bytes object (which means we kept it in RAM, which may not be wise for huge downloads) 
        uses requests's stream=True, which seems chunked HTTP transfer, or just a TCP window? TOCHECK

        @param tofile_path: If this is non-None, we open it as a filename and _stream_ the download to that if we can.
        @param show_progress: whether to print/show output on stderr while downloading.
        @param url: the URL to fetch data from
        @param chunk_size:

        @return: byte
        if the HTTP response code is >=400 (actually if !response.ok, see requests's documentation), we raise a ValueError 
    '''
    if tofile_path is not None:
        f = open(tofile_path,'wb')
        def handle_chunk(data):
            f.write(data)
    else:
        ret = []
        def handle_chunk(data):
            ret.append(data)  # CONSIDER: using bytesIO to collect that

    def progress_update():
        # TODO: consider using our own notebook.progress_bar here
        bar_str = ''
        if total_length is not None:
            frac = float(fetched)/total_length
            width = 50
            bar_str = '[%s%s]'%(
                '=' * int(frac*width), 
                ' ' * (width-int(frac*width))
            )
        return "\rDownloaded %8sB  %s"%(wetsuite.helpers.format.kmgtp( fetched, kilo=1024 ), bar_str)

    response = requests.get(
        url,
        stream=True,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'
        },
        timeout=timeout
    )
    total_length = response.headers.get( 'content-length' )

    if not response.ok:
        raise ValueError( str(response.status_code) )

    if total_length is not None:
        total_length = int( total_length )
        #show_progress = True
        #chunkrange = range(total_length/chunksize)

    fetched = 0
    for data in response.iter_content( chunk_size=chunk_size ):
        handle_chunk( data )
        fetched += len( data )
        if show_progress:
            sys.stderr.write( progress_update() )
            sys.stderr.flush()

    if show_progress:
        sys.stderr.write( progress_update()+'\n' )
        sys.stderr.flush()

    if tofile_path is None:
        return b''.join( ret )
