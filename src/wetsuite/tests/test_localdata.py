import os
import pytest
import wetsuite.helpers.localdata



def test_crud():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', key_type=str, value_type=str)
    with pytest.raises(KeyError):
        kv.get('a')
    kv.put('a', 'b')
    assert len(kv)==1
    assert kv.get('a') == 'b'
    kv.delete('a')
    assert len(kv)==0

    kv.put('c', 'd')
    assert len(kv)==1
    kv.delete('c')
    assert len(kv)==0


def test_metacrud():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', key_type=str, value_type=str)
    with pytest.raises(KeyError):
        kv._get_meta('a')
    kv._put_meta('a', 'b')
    assert kv._get_meta('a') == 'b'
    kv._delete_meta('a')
    kv._put_meta('c', 'd')
    kv._delete_meta('c')


def test_moreapi():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, str) 
    #kv['a'] = 'b'
    #kv['c'] = 'd'
    kv.put('a', 'b')
    kv.put('c', 'd')
    assert list( kv.keys() )   == ['a', 'c']
    assert list( kv.values() ) == ['b', 'd']
    assert list( kv.items() )  == [('a','b'), ('c','d')]
    assert 'a' in kv
    
    wetsuite.helpers.localdata.list_stores()


def test_doublecommit():
    ' do not trip over excessive commits '
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, str)
    kv.commit()
    kv.put('1','2', commit=False)
    kv.commit()
    kv.commit()


def test_rollback():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, str)
    assert len( kv.keys() ) == 0
    kv.put('1','2', commit=False)
    #assert len( kv.keys() ) == 1    true but not relevant here
    kv.rollback()
    assert len( kv.keys() ) == 0
    kv.commit()  # just to be sure there's no leftover state
    assert len( kv.keys() ) == 0
    kv.rollback()  # check that it works if not in a transaction 
    # TODO: more complex tests


def test_truncate():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, str)
    assert len( kv.keys() ) == 0
    for i in range(10):
        kv.put(str(i),'blah', commit=False)
    kv.truncate()
    assert len( kv.keys() ) == 0
    kv.commit()
    assert len( kv.keys() ) == 0

    for i in range(10):
        kv.put(str(i),'blah', commit=False)
    kv.commit()
    assert len( kv.keys() ) > 0
    kv.truncate()
    assert len( kv.keys() ) == 0
    kv.commit()
    assert len( kv.keys() ) == 0

    for i in range(10):
        kv.put(str(i),'blah', commit=False)
    kv.commit()
    assert len( kv.keys() ) > 0
    kv.truncate(vacuum=False)
    assert len( kv.keys() ) == 0
    kv.commit()
    assert len( kv.keys() ) == 0


def test_bytesize():
    # mostly that it doesn't bork out
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, str)
    initial_size = kv.bytesize()
    assert initial_size > 0   # I believe it counts the overhead
    # it counts in pages, so add more than a few things
    for i in range(1000):
        kv.put(str(i),'blah', commit=False)
    kv.commit()
    assert kv.bytesize() > initial_size
    

def test_type():
    # default str:str
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, str)
    kv.put('1','2')
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put(  1, '2')
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put( '1', 2 )

    # str:bytes
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, bytes)
    kv.put( 'a', b'b' )
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put( 'a', 's' )

    # int:float
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', key_type=int, value_type=float)
    kv.put(1, 2.0)
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put( 'a','s' )



def TEMPORARILY_DISABLED_test_multiread_and_locking( tmp_path ): # disabled because the test takes longish (on purpose)
#def test_multiread_and_locking( tmp_path ):
    import sqlite3

    # test that both see the same data
    #   even if one was opened later
    path = tmp_path / 'test1.db'
    kv1 = wetsuite.helpers.localdata.LocalKV( path, str, str )
    kv1.put('a','b')

    kv2 = wetsuite.helpers.localdata.LocalKV( path, str, str )
    kv1.put('c','d')

    assert kv1.items() == kv2.items()
    assert kv1.items() != []


    # test that not committing leaves the database locked and other opens would fail   (defined sqlite3 behaviour)
    kv1.put('e','f', commit=False) # this would keep the database locked until 
    with pytest.raises(sqlite3.OperationalError, match=r'.*database is locked*'): # note this will take the default 5 secs to time out
        kv3 = wetsuite.helpers.localdata.LocalKV( path, str, str )
        kv3.items()

    # check that commit does fix that
    kv1.commit()
    kv4 = wetsuite.helpers.localdata.LocalKV( path, str, str )
    kv4.items()

    # check that a commit=true (default)  while in a transaction due to an earlier commit=false does a commit
    kv1.put('g','h', commit=False)
    kv1.put('i','j')
    kv4 = wetsuite.helpers.localdata.LocalKV( path, str, str )
    kv4.items()


    # check that delete has the same behaviour
    kv1.delete('i', commit=False) # this would keep the database locked until 
    with pytest.raises(sqlite3.OperationalError, match=r'.*database is locked*'): # note this will take the default 5 secs to time out ()
        kv5 = wetsuite.helpers.localdata.LocalKV( path, str, str )
        kv5.items()

    kv1.delete('g', commit=False) # this would keep the database locked until 
    kv1.delete('e') 
    kv6 = wetsuite.helpers.localdata.LocalKV( path, str, str )
    kv6.items()


def TEMPORARILY_DISABLED_test_thread( tmp_path ):
    ''' See whether (with the default autocommit behaviour) access is concurrent
        and not overly eager to time-and-error out - basically see if the layer we added forgot something.    

        TODO: loosen up the intensity, it may still race to fail under load
    '''
    import time, threading, logging, random
    # It seems threads may share the module, but not connections
    # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
    path = tmp_path / 'test_thr.db'

    def get_sqlite3_thread_safety(): # See https://ricardoanderegg.com/posts/python-sqlite-thread-safety/ for why this is here
        " the sqlite module's threadsafety module is hardcoded for now, asking the library is more accurate "
        import sqlite3
        conn = sqlite3.connect(":memory:")
        threadsafe_val = conn.execute( "SELECT *  FROM pragma_compile_options  WHERE compile_options LIKE 'THREADSAFE=%'" ).fetchone()[0]
        conn.close()
        threadsafe_val = int(threadsafe_val.split("=")[1])
        return {0:0, 2:1, 1:3}[threadsafe_val] #sqlite's THREADSAFE values to DBAPI2 values


    if get_sqlite3_thread_safety() in (1,3): # in both you can share the module, but only in 3 could you share a connection
        start = time.time()
        end = start + 7

        def writer(end, path):
            myid = threading.get_ident()%10000
            mycount = 0
            while time.time() < end:
                mykv = wetsuite.helpers.localdata.LocalKV( path, str, str )
                mykv.put( '%s_%s'%(myid, mycount), '01234567890'*500)
                mycount+=1
                #time.sleep(0.01) # it seems that without this it wil
                #mykv.close()

        #mykv = wetsuite.helpers.localdata.LocalKV( path )
        #time.sleep(0.1)
        # also leave this open as reader, why not

        started = []
        #writer(end, path)
        for _ in range(3): # it seems to take a few dozen concurrent writers (on an SSD, that's probably relevant) to make it time itself out.
            th = threading.Thread(target=writer, args=(end, path))
            th.start()
            started.append( th )
            #time.sleep(0.1)

        while time.time() < end: # main thread watches what the others are managing to do
            #logging.warning( ' FILESIZE   '+str(os.stat(path).st_size) )
            mykv = wetsuite.helpers.localdata.LocalKV( path, str, str )
            #logging.warning( ' AMTO     '+str(len(mykv)) )
            #logging.warning('%s'%mykv.keys())
            mykv.close()
            time.sleep(0.5)

        for th in started:
            th.join()

    else: # thread-safety is 0
        raise EnvironmentError('SQLite is compiled single-threaded, we can be fairly sure it  would fail')






def test_vacuum( tmp_path ):
    # test that vacuum actually reduces file size
    path = tmp_path / 'test1.db'
    kv = wetsuite.helpers.localdata.LocalKV( path, str, str )
    keys = []
    for i in range(1000):
        key = 'key%s'
        keys.append(key)
        kv.put(key,'1234567890'*10000, commit=False)
    kv.commit()

    size_before_vacuum = os.stat(kv.path).st_size
    for key in keys:
        kv.delete( key )
    kv.vacuum()

    size_after_vacuum = os.stat(kv.path).st_size
    
    assert size_after_vacuum < size_before_vacuum


def test_cached_fetch():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, bytes) 
    bytedata, fromcache = wetsuite.helpers.localdata.cached_fetch(kv, 'https://www.google.com/')
    assert fromcache==False
    assert b'<html' in bytedata

    bytedata, fromcache = wetsuite.helpers.localdata.cached_fetch(kv, 'https://www.google.com/')
    assert fromcache==True
    assert b'<html' in bytedata

    kv = wetsuite.helpers.localdata.LocalKV(':memory:', str, str) 
    with pytest.raises(TypeError, match=r'.*expects*'): # complaint about type
        wetsuite.helpers.localdata.cached_fetch(kv, 'https://www.google.com/')


def test_msgpack_crud():
    kv = wetsuite.helpers.localdata.MsgpackKV(':memory:')
    with pytest.raises(KeyError):
        kv.get('a')
    kv.put('a', (2,3,4))
    assert len(kv)==1
    assert kv.get('a') == [2,3,4]   # list, not tuple
    kv.delete('a')
    assert len(kv)==0

    kv.put('b', {1:2, b'b':[ {'a':'b'},{'c':[2,1,'0']}]} )

    kv.put('c', {1:2, 'v':'a'})
    assert len(kv)==2
    # checks that strict_map_key is not enforced (things other than str or bytes)
    kv.items()
    kv.values()

    kv.delete('c')
    assert len(kv)==1






# if __name__ == '__main__':
#     #import pprint
#     import os

#     #os.unlink("test.db")

#     local_store = LocalKV("test.db")
#     print( 'getfoo', local_store.get('foo') )
#     #print('1')
#     local_store.put('foo', 'bar') 
#     #print('2')
#     #local_store.put(b'foo', b'quu') 
#     #print('3')
#     print( 'getfoo', local_store.get('foo') )

#     local_store['blee'] = 'bla'
    

#     if 0:
#         print( "Deleting" )
#         for key in local_store.keys():
#             if key.startswith('kv-ah'):
#                 local_store.delete( key, commit=False)
#         local_store.commit()
#         print( "Done" )

#     #print('4')
#     #local_store.close()


#     print( len(local_store) )

#     if 0:
#         import wetsuite.datasets
#         kv = wetsuite.datasets.load('kamervragen')
#         #print(kv.data)
#         import pprint
#         i=0
#         for k, d in kv.data.items():
#             local_store.put('kv-%s'%k, pprint.pformat(d) )
#             i+=1
#             if (i%10)==0:
#                 print( 'commit', i )
#                 local_store.commit()
#             if i>30:
#                 break
#         local_store.commit()

#     #or value in local_store.values():
#     #    print( value )

#     #print( local_store.values() )
#     print( local_store.keys() )
#     #print( list( local_store ) ) 

