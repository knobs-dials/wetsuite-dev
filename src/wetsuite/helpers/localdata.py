'''
    This is intended to provide a way to store collections of data on disk, in a in key-value store way.
    See the docstring on the LocalKV class for more.

    How to use
    - This module contain a global, docstore
        OR 
    - You can create your own specific stores by doing something like:
        mystore_path = os.path.join( wetsuite.datasets.wetsuite_dir()[0], 'docstore.db')
        mystore = LocalKV( mystore_path )
    
    Notes:
    - Using an absolute, repeatable path like that is recommended 
        to avoid confusing yourself by unintentionally creating a database in each working directory.
    - The global is a quick and dirty way to get a singleton, because SQLite doesn't like concurrent writes. 
        CONSIDER: be a little more resistant to that via retries
    - By default, writes are done autocommit style, because the driver defaults to that.
        so you can get bulk writes to be more performant by using put() with commit=False parameter and doing an explicit commit() after

    TODO: test that keeping it open is a good idea.
'''
import os 

import sqlite3

import wetsuite.datasets


class LocalKV:    # maybe inherit from dict for instanceof-like reasons?
    ''' A key-value store backed by a local filesystem.
        This is currently a fairly thin wrapper around SQLite - this may change.

        Because SQLite is duck typed (it just stores whatever), 
        we try to enforce the types going in -- by default str keys and str values.
        You could change both - e.g. the cached_fetch function expects a str:bytes store

        Given
            db = LocalKv('path/to/dbfile')
        Basic use is:
            db.put('foo', 'bar')
            db.get('foo')
            # this way also exposes some sqlite things (commit, vacuum) for when you know how to use them.

        the dict way is a little simpler:
            db['foo'] = 'bar'
            db['foo']

        As per basic sqlite behaviour multiple processes can read the same database,
        but only one can write, and currently when you do any other readers would bork out on the fact it's locked (CONSIDER: having it retry).

        CONSIDER: add expiry
    '''
    def __init__(self, path, key_type=str, value_type=str):
        ''' Specify the path to the database file to open. 

            Will be created if it does not yet exist so you proably want think to think about repeating the same path in absolute sense.
            (This is also often the answer to "why do I have an empty database")
            You may like to use open_store() to have our code place it in the same place.
        '''
        self.path = path
        self._in_transaction = False
        self._open()
        self.key_type = key_type
        self.value_type = value_type


    def _open(self):
        #print('open(%r)'%self.filename)
        first = not os.path.exists( self.path )
        self.conn = sqlite3.connect( self.path )
        # Note: curs.execute its the regular DB-API way,  conn.execute is a shorthand  and gets a cursor temporarily
        self.conn.execute("PRAGMA auto_vacuum = INCREMENTAL") # TODO: see that that works
        if first:
            self.conn.execute("CREATE TABLE IF NOT EXISTS kv (key text unique NOT NULL, value text)")
        self.conn.commit()


    def _checktype_key(self, val):
        if not isinstance(val, self.key_type):
            raise TypeError('Only keys of type %s are allowed, you gave a %s'%(self.key_type.__name__, type(val).__name__))
        
    def _checktype_value(self, val):
        if not isinstance(val, self.value_type):
            raise TypeError('Only values of type %s are allowed, you gave a %s'%(self.value_type.__name__, type(val).__name__))



    def get(self, key):
        self._checktype_key(key)
        with self.conn: # context manager for a commit
            curs = self.conn.cursor()
            curs.execute("SELECT value FROM kv WHERE key=?", (key,) )
            row = curs.fetchone()
            if row is None:
                return None
            else:
                return row[0]


    def put(self, key, value, commit=True):
        ''' Note that if you use commit=False, we '''
        self._checktype_key(key)
        self._checktype_value(value)

        curs = self.conn.cursor()
        if not commit  and  not self._in_transaction:
            curs.execute('BEGIN')
            self._in_transaction = True

        curs.execute('INSERT INTO kv (key, value) VALUES (?, ?)  ON CONFLICT (key) DO UPDATE SET value=?', (key,value, value) )
        if commit:
            self.commit()


    def delete(self, key, commit=True):
        ''' delete item by key 

            You should not expect the file to shrink until you also do a vacuum(), which will need to rewrite the file.
        '''
        self._checktype_key(key)
        curs = self.conn.cursor() # TODO: check that's correct when commit==False
        if not commit  and  not self._in_transaction:
            curs.execute('BEGIN')
            self._in_transaction = True
        curs.execute('DELETE FROM kv where key=?', ( key,) )
        if commit:
            self.commit()


    def commit(self):
        ' commit changes - for when you use put() or delete() with commit=False to do things in a larger transaction '
        self.conn.commit()
        self._in_transaction = False


    def vacuum(self):
        ''' After a lot of deletes you could compact the store with vacuum() - but note this rewrite the file so the more data you store, the longer this takes '''
        self.conn.execute('vacuum')
    

    def close(self):
        self.conn.close()



    # make it act dict-like - based on code from https://stackoverflow.com/questions/47237807/use-sqlite-as-a-keyvalue-store
    def __getitem__(self, key):
        ret = self.get(key)
        if ret is None:
            raise KeyError()
        
    #def has_key(self, key)
    #    return self.get(key) is not None

    def __setitem__(self, key, value):
        self.put(key, value)

    def __delitem__(self, key):
        # TODO: check whether we can ignore it not being there, or must raise KeyError for interface correctness
        #if key not in self:
        #    raise KeyError(key)
        self.conn.execute('DELETE FROM kv WHERE key = ?', (key,)) 

    def __contains__(self, key):
        return self.conn.execute('SELECT 1 FROM kv WHERE key = ?', (key,)).fetchone() is not None

    def __iter__(self): # TODO: check
        return self.iterkeys()


    def __len__(self):
        return self.conn.execute('SELECT COUNT(*) FROM kv').fetchone()[0] # TODO: double check

    def iterkeys(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT key FROM kv'):
            yield row[0]

    def keys(self): 
        return list( self.iterkeys() )

    def itervalues(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT value FROM kv'):
            yield row[0]

    def values(self): 
        return list( self.itervalues() )

    def iteritems(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT key, value FROM kv'):
            yield row[0], row[1]

    def items(self):
        return list( self.iteritems() )
    

    def __repr__(self):
        return '<LocalKV(%r)>'%( os.path.basename(self.path), )




# class ExpiringLocalKV(LocalKV):
#     ''' A vartiation of LocalKV that can remove items based on an expiration date '''
#     def __init__(self):
#         super().__init__()

#     def _open(self):
#         print('open(%r)'%self.filename)
#         first = not os.path.exists( self.filename )
#         self.conn = sqlite3.connect( self.filename )
#         curs = self.conn.cursor()
#         curs.execute("PRAGMA auto_vacuum = INCREMENTAL") # TODO: see that that works
#         if first:
#             print( "creating database %r"%self.filename)
#             curs.execute("CREATE TABLE IF NOT EXISTS kv (key text unique NOT NULL, value text, expiry integer)")
#         curs.close()
#         self.conn.commit()

#     def clean()



def open_store(dbname, key_type=str, value_type=str):
    ''' Returns a LocalKV, stored under the local directory wetsuite picks to store things in.
        Give this a relative filename, e.g. 
          docs = open_store('docstore.db')
    '''
    if os.sep in dbname:
        raise ValueError('This function is meant to within the wetsuite directory. If you want to use an absolute path, you can instantiate LocalKV directly.')
    # CONSIDER: sanitize filename more?
    if dbname==':memory:':  # allow the sqlite special value of :memory: 
        ret = LocalKV( dbname, key_type=key_type, value_type=value_type )
    else:
        dirs = wetsuite.datasets.wetsuite_dir()
        _docstore_path = os.path.join( dirs['stores_dir'], dbname )
        ret = LocalKV( _docstore_path, key_type=key_type, value_type=value_type )
    return ret


def list_stores():
    ''' List all files in the directories that open_store() put things in '''
    dirs = wetsuite.datasets.wetsuite_dir()
    stores_dir = dirs['stores_dir']
    # CONSIDER: filter for actually openable files, with basic file magic test?
    return os.listdir( stores_dir )


def cached_fetch(store, url):
    ''' Lets you use a LocalKV (str:bytes) to cache URL fetches
        Is little more than 'if URL is a key in the store, return its value. 
                             if not,                       do wetsuite.helpers.net.download(url), store in store, and return.
    '''
    import wetsuite.helpers.net
    if store.key_type is not str  or  store.value_type is not bytes:
        raise TypeError('cached_fetch() expects a str:bytes store, not a %r:%r'%(store.key_type.__name__, store.value_type.__name__))

    ret = store.get(url)
    if ret is not None: # return cached version
        return ret
    else: # fetch and cache
        data = wetsuite.helpers.net.download( url ) 
        print( type(data) )
        store.put( url, data )
        return data





