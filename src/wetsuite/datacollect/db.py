''' Cache HTTP fetches in a database

    Currently backed by postgres
    CONSIDER: generalize and default to something easier to install.
'''
from typing import Tuple
import time, math


import requests
import psycopg2


def connect():
    # TODO: decide whether to also return a created cursor, to save some typing on each use
    return psycopg2.connect('dbname=wetsuite user=postgres host=localhost connect_timeout=5')


#import psycopg2.pool
# _ppg2pool = None
# def poolconnect():
#     '''
#         TODO: decide whether this can be removed, I don't think there's anything for which the 10ms savings are worth it
#     '''
#     global _ppg2pool 
#     if _ppg2pool==None:
#         print( "First-time pool init" )
#         _ppg2pool = psycopg2.pool.SimpleConnectionPool(1, 20,user = "postgres", host = "localhost",  port = "5432",  database = "wetsuite")
#     else:
#         print( "reusing pool" )
#     conn = _ppg2pool.getconn()
#     curs = conn.cursor()
#     return conn,curs


def cached_fetch(url:str, dbonly:bool=False, force_refetch:bool=False, timeout_sec:float=300, given_conn=None, verbose:bool=False, backoff_sec:float=0.0) -> Tuple[bytes, str, bool]:
    ''' Returns (bytestring, content_type, came_from_cache)
        
        May raise an exception if
        - we didn't have it and dbonly==True
        - we failed to fetch it (404, 500, etc.)

        If we don't have an entry for that url in database
           and dbonly==False  (default), try to fetch it and store it
           and dbonly==True, then we raise a ValueError signifying that

        force_fetch fetches and replaces even if we have it, e.g. for content you exect to change regularly

        timeout_sec is two minutes, because there are a few large, slow downloads

        given_conn - givingthis an existing connection is slightly faster than making a connection -- hekps

        TODO: split out to have function behaviour be more obvious
    '''
    if given_conn is not None:
        conn = given_conn
    else:
        conn = connect()
    curs = conn.cursor()
    
    try:
        if not force_refetch:
            curs.execute('select data, content_type FROM fetched WHERE url=%s', (url,) )
            if curs.rowcount==1:
                if verbose:
                    print( "CACHED %s"%url )
                content, content_type = curs.fetchone()
                content = bytes(content) # psycopg2 gives a memoryview, we want to return bytes
                return content, content_type, True
        
        # implied else: 0 rows matched, or we were told not to try
        if dbonly:
            raise ValueError("Don't have that")

        headers = { 'User-Agent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36', }
        resp = requests.get(url, timeout=timeout_sec, headers=headers) # verify=False,
        #except:
        #    #print( resp.history )
        #    raise

        if not resp.ok:
            raise ValueError("Couldn't fetch, status=%s (on %r)"%(resp.status_code, url))

        if verbose:
            print( "FETCHED %s"%url )

        time.sleep( backoff_sec )

        content = resp.content
        content_type = resp.headers.get('content-type', 'application/octet-stream')
        content_length = len(content)
        # maybe handle in exception so that we don't insert data twice?
        curs.execute('INSERT INTO fetched (url, data, content_type, content_length) VALUES (%s,%s,%s,%s)  ON CONFLICT (url)  DO UPDATE SET data=%s, content_type=%s, content_length=%s',
            (url, content, content_type, content_length,
                 content, content_type, content_length))
        conn.commit()
        return content, content_type, False

    #except psycopg2.errors.UniqueViolation as uv:
    except Exception as e:
        #print(e)
        raise 
    
    finally:
        conn.rollback()
        if given_conn is None:
            conn.close()



minute =   60.
hour   =   60 * minute
day    =   24 * hour
week   =    7 * day
month  = 30.5 * day
year   =  365 * day



#  *_generated is meant as a key-value store that is more persistent than a memcache, but as free-form in use as one.
#  It is currently backed by a postgres table, but TODO: add some NoSQL options in the longer run
# 
#  It still takes care to not build up over time.
# 
# Meant for things like "Hey the OCR was intensive to do, let's store that somewhere"
# 
#  There is the 'remove after this time' column, yet
#  - this is mainly checked by get_generated - but that only does anything on frequented keys
#  - you can put cleanup_generated on a crontab
#  - if you plan for temporary sets, you can use 'collection' on set_generated, and later remove all by collection

# a cache in database
def set_generated(key:str, data:bytes, collection:str=None, given_conn=None, remove_sec:float=month, max_byte_size=524288):
    ''' Sets a byte value for a key, to fetch later with 

        remove is how long to keep it, in seconds (takes a float or int but is ceil()'d to an int), default a month
        Can be None, meaning 'keep indefinitely', but you may not want to.

        Removal is, by default, only done whenever a key is fetched. 

        Think hard before you store large things here. There's a "self-imposed maximum so you don't accidentally store a few gbyte" thing here.

        collection is optional, set and indexed, and only meant to make cleanup or complete removal of subsets easir
    '''
    if type(data) is not bytes:
        msg = "The value should be bytes, not %s"%type(data)
        if type(data) is str:
            msg += "  (for unicode strings consider .encode('utf-8'))"
        raise TypeError( msg )
    
    if len(data) > max_byte_size:
        raise ValueError( "Data size %d is larger than the self-imposed limit of %d.  Raise this in your call if you're sure."%( len(data), max_byte_size) )

    if given_conn is not None:
        conn = given_conn
    else:
        conn = connect()
    curs = conn.cursor()
    try:
        curs.execute("INSERT INTO generated (key, data, remove_after, collection) VALUES (%%s,%%s,NOW() + INTERVAL '%d second', %%s)   ON CONFLICT (key)  DO UPDATE SET data=%%s, collection=%%s; "%(
            int(math.ceil(remove_sec))),
            (key, data, collection,   data, collection)
        )
    finally:
        conn.commit()
        if given_conn is None:
            conn.close()


def get_generated(key:str, given_conn=None):
    ''' Returns either a stored bunch of bytes, or None

        Note that this is not meant as a memcache, in a few details,
        including that every fetch checks whether it should try deleting the key.
    '''
    if given_conn is not None:
        conn = given_conn
    else:
        conn = connect()
    curs = conn.cursor()
    try:
        curs.execute('SELECT data, remove_after  FROM generated  WHERE key=%s', (key,))
        conn.rollback()
        if curs.rowcount==0:
            return None
        else:
            value, remove = curs.fetchone()
            if remove is not None  and  (time.time() - 3600) > time.mktime(remove.timetuple()):
                curs.execute('DELETE FROM generated  WHERE key=%s AND NOW() > remove_after ', (key,))
                conn.commit()
                if curs.rowcount==0:
                    pass # print( 'not REMOVED yet' )
                else:
                    print( 'REMOVED: %d'%curs.rowcount ) # should only ever be 1
            return value.tobytes()
    finally:
        conn.rollback()
        if given_conn is None:
            conn.close()


def cleanup_generated(collection=None):
    ' go through _all_ entries and remove any that should be. You may want this on a cronjob or such '
    conn = connect()
    curs = conn.cursor()
    try:
        if collection is not None:
            curs.execute('DELETE FROM generated  WHERE collection=%s AND remove_after < now() ', (collection,))
        else:
            curs.execute('DELETE FROM generated  WHERE remove_after < now() ')
        print( "cleanup removed %d"%curs.rowcount)
    finally:
        conn.commit()
        conn.close()


def cleanup_generated_remove_all_in_collection(collection):
    ' go through _all_ entries and remove any that should be. You may want this on a cronjob or such '
    conn = connect()
    curs = conn.cursor()
    try:
        curs.execute('DELETE FROM generated  WHERE collection=%s', (collection,))
        print( "collection delete removed %d"%curs.rowcount)
    finally:
        conn.commit()
        conn.close()


def test():
    import time, random

    conn = connect()

    try:
        set_generated('foo', b'bar1', remove_sec=3, given_conn=conn)
        set_generated('bar', b'bar2', remove_sec=1, given_conn=conn)

        for i in range(5000):
            n = random.randint(0,6)
            set_generated('bar%d'%i, ('bar_%s'%i).encode('u8'), remove_sec=n, given_conn=conn)
            set_generated('bar%d'%i, ('bar_%s'%i).encode('u8'), remove_sec=n, given_conn=conn, collection='foo')

        print( get_generated('foo') )
        print( get_generated('bar') )

        time.sleep( 1 )
        cleanup_generated()
        time.sleep( 1 )
        cleanup_generated()
        time.sleep( 1 )
        cleanup_generated()
        time.sleep( 1 )
        cleanup_generated()
        time.sleep( 1 )
        cleanup_generated()
        time.sleep( 1 )
        cleanup_generated()
        time.sleep( 1 )
        cleanup_generated()
        time.sleep( 1 )
        cleanup_generated()

        print( get_generated('foo') )
        print( get_generated('bar') )

        time.sleep( 5 )
        cleanup_generated()

    finally:
        conn.close()


if __name__ == '__main__':
    test()

