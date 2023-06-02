import os
import pytest
import wetsuite.helpers.localdata


def test_crud():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:')

    # dict-like
    with pytest.raises(KeyError):
        kv['a']
    kv['a'] = 'b'
    assert len(kv)==1
    del kv['a']
    assert len(kv)==0

    kv.put('c', 'd')
    assert len(kv)==1
    kv.delete('c')
    assert len(kv)==0


def test_moreapi():
    kv = wetsuite.helpers.localdata.LocalKV(':memory:') 
    kv['a'] = 'b'
    kv['c'] = 'd'
    assert kv.keys()             == ['a', 'c']
    assert list(kv.iterkeys())   == ['a', 'c']
    assert kv.values()           == ['b', 'd']
    assert list(kv.itervalues()) == ['b', 'd']
    assert kv.items()            == [('a','b'), ('c','d')]
    assert list(kv.iteritems())  == [('a','b'), ('c','d')]
    assert 'a' in kv
    
    wetsuite.helpers.localdata.list_stores()

def test_type():
    # default str:str
    kv = wetsuite.helpers.localdata.LocalKV(':memory:')
    kv.put('1','2')
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put(1,'2')
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put('1',2)

    # str:bytes
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', value_type=bytes)
    kv.put('a',b'b')
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put('a','s')

    # int:float
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', key_type=int, value_type=float)
    kv.put(1, 2.0)
    with pytest.raises(TypeError, match=r'.*are allowed*'):
        kv.put('a','s')


def TEMPORARILY_DISABLED_test_multiread_and_locking( tmp_path ):
    import sqlite3

    # test that both see the same data
    #   even if one was opened later
    path = tmp_path / 'test1.db'
    kv1 = wetsuite.helpers.localdata.LocalKV( path )
    kv1.put('a','b')

    kv2 = wetsuite.helpers.localdata.LocalKV( path )
    kv1.put('c','d')

    assert kv1.items() == kv2.items()
    assert kv1.items() != []


    # test that not committing leaves the database locked and other opens would fail   (defined sqlite3 behaviour)
    kv1.put('e','f', commit=False) # this would keep the database locked until 
    with pytest.raises(sqlite3.OperationalError, match=r'.*database is locked*'): # note this will take the default 5 secs to time out ()
        kv3 = wetsuite.helpers.localdata.LocalKV( path )
        kv3.items()

    # check that commit does fix that
    kv1.commit()
    kv4 = wetsuite.helpers.localdata.LocalKV( path )
    kv4.items()

    # check that a commit=true (default)  while in a transaction due to an earlier commit=false does a commit
    kv1.put('g','h', commit=False)
    kv1.put('i','j')
    kv4 = wetsuite.helpers.localdata.LocalKV( path )
    kv4.items()


    # check that delete has the same behaviour
    kv1.delete('i', commit=False) # this would keep the database locked until 
    with pytest.raises(sqlite3.OperationalError, match=r'.*database is locked*'): # note this will take the default 5 secs to time out ()
        kv5 = wetsuite.helpers.localdata.LocalKV( path )
        kv5.items()

    kv1.delete('g', commit=False) # this would keep the database locked until 
    kv1.delete('e') 
    kv6 = wetsuite.helpers.localdata.LocalKV( path )
    kv6.items()


def test_vacuum( tmp_path ):
    # test that vacuum actually reduces file size
    path = tmp_path / 'test1.db'
    kv = wetsuite.helpers.localdata.LocalKV( path )
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
    kv = wetsuite.helpers.localdata.LocalKV(':memory:', value_type=bytes) 
    assert b'<html' in wetsuite.helpers.localdata.cached_fetch(kv, 'https://www.google.com/')


    kv = wetsuite.helpers.localdata.LocalKV(':memory:') 
    with pytest.raises(TypeError, match=r'.*expects*'):
        wetsuite.helpers.localdata.cached_fetch(kv, 'https://www.google.com/')






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

