#!/usr/bin/python3
' network/fetch related helper functions '
import sys
import wetsuite.helpers.format
import urllib, requests


def download( url, tofile_path = None, show_progress=False):
    ''' if tofile is not None, we stream to that file path, by name 
           tofile is None      we return the data (which means we kept it in RAM, which may not be wise for huge downloads)

        uses requests's stream=True, which is chunked HTTP transfer and/or just a TCP window?
    '''
    if tofile_path is not None:
        f = open(tofile_path,'wb')
        def handle_chunk(data):
            f.write(data)
    else:
        ret = []
        def handle_chunk(data):
            ret.append(data)

    def prog():
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

    chunk_size = 64*1024 # 524288
    if total_length is not None: 
        total_length = int(total_length)
        #show_progress = True
        #chunkrange = range(total_length/chunksize) 

    fetched = 0
    for data in response.iter_content(chunk_size=chunk_size):
        handle_chunk(data)
        fetched += len(data)
        if show_progress:
            sys.stderr.write( prog() )    
            sys.stderr.flush()

    if show_progress:
        sys.stderr.write( prog()+'\n' )
        sys.stderr.flush()

    if tofile_path is None:
        return b''.join( ret )




if __name__ == '__main__':
    download( "https://www.rechtspraak.nl/SiteCollectionDocuments/Technische-documentatie-Open-Data-van-de-Rechtspraak.pdf", tofile_path='test.dl', show_progress=True )
    #data = download( "https://www.rechtspraak.nl/SiteCollectionDocuments/Technische-documentatie-Open-Data-van-de-Rechtspraak.pdf", show_progress=True )
    #print( len(data))

    #download( "https://static.rechtspraak.nl/PI/OpenDataUitspraken.zip", tofile_path='test.dl', show_progress=True )
