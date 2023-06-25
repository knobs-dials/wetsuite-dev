''' This is intended to provide an easier way way to store collections of data on disk, in a in key-value store way.
    See the docstring on the LocalKV class for more details.

    How to use
    - You can create your own specific stores by doing something like:
        mystore_path = os.path.join( 'project_data', 'docstore.db')
        mystore = LocalKV( mystore_path )
    OR
    - use open_store( 'docstore.db' ), which places it in the wetsuite directory in your homedir
      which should make it easier to always open the same thing without having to think about absolute paths 

    
    Notes:
    - Using an absolute, repeatable path like that is recommended 
        to avoid confusing yourself by unintentionally creating a database in each working directory.
    - The global is a quick and dirty way to get a singleton, because SQLite doesn't like concurrent writes. 
        CONSIDER: be a little more resistant to that via retries
    - By default, writes are done autocommit style, because the driver defaults to that.
        so you can get bulk writes to be more performant by using put() with commit=False parameter and doing an explicit commit() after

    TODO: test that keeping it open is a good idea.

    CONSIDER: writing a ExpiringLocalKV that cleans up old entries
    CONSIDER: writing variants that do convert specific data, letting you e.g. set/fetch dicts, or anything else you could pickle
'''
import os 

import sqlite3

import wetsuite.datasets     # to get wetsuite_dir
import wetsuite.helpers.net


class LocalKV:
    ''' A key-value store backed by a local filesystem.
        This is currently a fairly thin wrapper around SQLite - this may change.

        SQLite will still just store the type it gets, and this won't do conversions for you,
        it only enforces the values that go in are of the type you said you would put in.
        This will makes things more consistent, but is not a strict guarantee.
        
        You could change both key and value types - e.g. the cached_fetch function expects a str:bytes store

        Given
            db = LocalKv('path/to/dbfile')      # (note that open_store() may be more convenient)
        Basic use is:
            db.put('foo', 'bar')
            db.get('foo')

        the dict way is a little less typing:
            db['foo'] = 'bar'
            db['foo']

        Notes:
        - It is a good idea to open the store with the same typing each  or you will still confuse yourself.
            CONSIDER: storing typing in the file 
        - doing it via functions is a little more typing yet also exposes some sqlite things (using transactions, vacuum) for when you know how to use them.
            and is arguably clearer than 'this particular dict-like happens to get stored magically'
        - On concurrency: As per basic sqlite behaviour, multiple processes can read the same database,
          but only one can write, and when you leave a writer with uncommited data for nontrivial amounts of time,
          readers are likely to bork out on the fact it's locked (CONSIDER: have it retry / longer).
          This is why by default we leave it on autocommit, even though that can be slower.
    '''
    def __init__(self, path, key_type, value_type):
        ''' Specify the path to the database file to open. 

            key_type and value_type do not have defaults, so that you think about how you are using these,
            but we often use   str,str  and  str,bytes

            The database file will be created if it does not yet exist 
            so you proably want think to think about repeating the same path in absolute sense.
            (This is also often the answer to "why do I have an empty database")
            ...if you want to think about that less, consider using open_store().
        '''
        self.path = path
        self._open()
        # here in part to remind us that we _could_ be using converters  https://docs.python.org/3/library/sqlite3.html#sqlite3-converters
        if key_type not in (str, bytes, int):
            raise ValueError("We are currently a little overly paranoid about what to allow as key types (%r not allowed)"%key_type.__name)
        if value_type not in (str, bytes, int, float):
            raise ValueError("We are currently a little overly paranoid about what to allow as value types (%r not allowed)"%value_type.__name)
        self.key_type = key_type
        self.value_type = value_type
        self._in_transaction = False


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
        ' gets value for key '
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
        ''' Sets a value for a key.
            Types will be checked according to what you inited this class with.
            
            commit=False lets us do bulk commits, mostly when you want to a load of small changes without becoming IOPS bound.
            If you care less about speed, and/or more about parallel access, you can ignore this.
        '''
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
        ''' delete item by key.

            You should not expect the file to shrink until you do a vacuum()  (which will need to rewrite the file).
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
        ''' After a lot of deletes you could compact the store with vacuum() - but note this rewrite the file so the more data you store, the longer this takes 
            Note that if we were left in a transaction (due to commit=False), ths is commit()ed first. 
        '''
        if self._in_transaction:
            self.commit()
        self.conn.execute('vacuum')
    

    def close(self):
        self.conn.close()


    # make it act dict-like - based on code from https://stackoverflow.com/questions/47237807/use-sqlite-as-a-keyvalue-store
    def __getitem__(self, key):
        ret = self.get(key)
        if ret is None:
            raise KeyError()
        return ret
        
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




def cached_fetch(store, url:str, force_refetch:bool=False):
    ''' Helper to use a str-to-bytes LocalKV to cache URL fetch results.

        Takes a store to get/put data from, and a url to fetch,
        returns (data, came_from_cache)

        May raise 
        - whatever requests.get may range
        - ValueError when !response.ok, or if the HTTP code is >=400
          (which is behaviour from wetsuite.helpers.net.download())
          ...to force us to deal with issues and not store error pages.

        Is little more than 
        - if URL is a key in the store, return its value
        - if URL not in store,          do wetsuite.helpers.net.download(url), store in store, and return its value
    '''
    if store.key_type is not str  or  store.value_type is not bytes:
        raise TypeError('cached_fetch() expects a str:bytes store, not a %r:%r'%(store.key_type.__name__, store.value_type.__name__))
    # yes, the following could be a few lines shorter, but this is arguably a little more readable
    if force_refetch == False:
        ret = store.get(url)
        if ret is not None: # return cached version
            #print("CACHED")
            return ret, True
        else:
            data = wetsuite.helpers.net.download( url ) 
            #print("FETCHED")
            store.put( url, data )
            return data, False
    else: # force_refetch == True
        data = wetsuite.helpers.net.download( url ) 
        #print("FORCE-FETCHED")
        store.put( url, data )
        return data, False


def open_store(dbname, key_type, value_type):
    ''' A helper that opens a LocalKV in the local wetsuite directory, 
        mostly so that you don't have to think about handing in a reproducable absolute path yourself.

        Just a filename, e.g.
          docs = open_store('docstore.db')
        will open the same store regardless of the directory the interpreter is currently considered to be in.
        It's suggested you use descriptive names so that you don't open existing stores without meaning to.
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
    ''' List all files in the directories that open_store() put things in 
        CONSIDER: filter for things that actually look like stores (with basic file magic test)
    '''
    dirs = wetsuite.datasets.wetsuite_dir()
    stores_dir = dirs['stores_dir']
    return os.listdir( stores_dir )




