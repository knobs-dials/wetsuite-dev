''' This is intended to provide an easier way way to store collections of data on disk, in a in key-value store way.
    See the docstring on the LocalKV class for more details.

    
    How to use:
    - You can create your own specific stores by doing something like:
        mystore_path = os.path.join( project_data_dir, 'docstore.db')  # OS-agnostic path join
        mystore = LocalKV( mystore_path )
    OR
        open_store( 'docstore.db' ), which places it in the wetsuite directory in your homedir

    "Why two ways?"
        The first gives you direct control, but
            ...with relative paths it will create in whatever is the current working directory,
               which makes it easy for you to confuse yourself with databases all over the place
            ...with absolute paths you will easily make things less portable.
        The latter just gives the same store for the same name
            (if you want to know where exactly, use .path)
          
    Note that by default, writes are done autocommit style, because SQlite's driver defaults to that.
      so you can get bulk writes to be more performant by using put() with commit=False parameter and doing an explicit commit() after.

    CONSIDER: meta table for e.g. 'description'
    CONSIDER: writing a ExpiringLocalKV that cleans up old entries
    CONSIDER: writing variants that do convert specific data, letting you e.g. set/fetch dicts, or anything else you could pickle

    
    "Could I access these SQLite databases myself?"
    Sure, particularly when just reading.
    The code is only there for convenience, there is nothing special about them. Consider:
      sqlite3 store.db 'select key,value from kv limit 1 ' | less
'''
import os, pickle, json

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

        
        Notes:
        - It is a good idea to open the store with the same typing each  or you will still confuse yourself.
            CONSIDER: storing typing in the file 
        - doing it via functions is a little more typing yet also exposes some sqlite things (using transactions, vacuum) for when you know how to use them.
            and is arguably clearer than 'this particular dict-like happens to get stored magically'
        - On concurrency: As per basic sqlite behaviour, multiple processes can read the same database,
          but only one can write, and when you leave a writer with uncommited data for nontrivial amounts of time,
          readers are likely to bork out on the fact it's locked (CONSIDER: have it retry / longer).
          This is why by default we leave it on autocommit, even though that can be slower.

        - It wouldn't be hard to also make it act like a dict, but we're trying to to avoid this to avoid a case of
          "this is so hidden in the semantics that it what and how become really opaque " style leaky abstraction.
          So we choose to make you type out get(), put(),  keys(), values(), and items(), and their iter variants),
          because those can at least have docstrings to warn you, rather than breaking your reasonable expectations. 
          ...exceptions are
            __len__        for amount of items                   CONSIDER: making that len()
            __contains__   backing 'is this key in the store'),  CONSIDER: making that has_key() instead
            __iter__       which is actually iterkeys()       so CONSIDER: removing it
    '''
    def __init__(self, path, key_type, value_type, read_only=False):
        ''' Specify the path to the database file to open. 

            key_type and value_type do not have defaults, so that you think about how you are using these,
            but we often use   str,str  and  str,bytes

            The database file will be created if it does not yet exist 
            so you proably want think to think about repeating the same path in absolute sense.
            (This is also often the answer to "why do I have an empty database")
            ...if you want to think about that less, consider using open_store().

            read_only is enforced in this wrapper to give slightly more useful errors. (we also give SQLite a PRAGMA)
        '''
        self.path = path
        self.read_only = read_only
        self._open()
        # here in part to remind us that we _could_ be using converters  https://docs.python.org/3/library/sqlite3.html#sqlite3-converters
        if key_type not in (str, bytes, int, None):
            raise ValueError("We are currently a little overly paranoid about what to allow as key types (%r not allowed)"%key_type.__name)
        if value_type not in (str, bytes, int, float, None):
            raise ValueError("We are currently a little overly paranoid about what to allow as value types (%r not allowed)"%value_type.__name)
        self.key_type = key_type
        self.value_type = value_type
        self._in_transaction = False


    def _open(self):
        #make_tables = (self.path==':memory:')  or  ( not os.path.exists( self.path ) )  # will be creating that file, or are using an in-memory database ?
        self.conn = sqlite3.connect( self.path )
        # Note: curs.execute is the regular DB-API way,  conn.execute is a shorthand that gets a temporary cursor
        with self.conn:
            self.conn.execute("PRAGMA auto_vacuum = INCREMENTAL")  # TODO: see that this does what I think it does
                                                                   # https://www.sqlite.org/pragma.html#pragma_auto_vacuum
            if self.read_only:
                self.conn.execute("PRAGMA query_only = true") # https://www.sqlite.org/pragma.html#pragma_query_only
            #if make_tables:
            self.conn.execute("CREATE TABLE IF NOT EXISTS meta (key text unique NOT NULL, value text)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS kv   (key text unique NOT NULL, value text)")


    def _checktype_key(self, val):
        if self.key_type is not None  and  not isinstance(val, self.key_type): # None means don't check 
            raise TypeError('Only keys of type %s are allowed, you gave a %s'%(self.key_type.__name__, type(val).__name__))


    def _checktype_value(self, val):
        if self.value_type is not None  and  not isinstance(val, self.value_type):
            raise TypeError('Only values of type %s are allowed, you gave a %s'%(self.value_type.__name__, type(val).__name__))


    def get(self, key, missing_as_none:bool=False): 
        ''' Gets value for key. 
            The key type is checked against how you constructed this localKV class (doesn't guarantee it matches what's in the database)
            If not present, this will raise KeyError (by default) or return None (if you set missing_as_None=True)
            (this is unlike a dict.get, which has a default=None)
        '''
        self._checktype_key(key)
        curs = self.conn.cursor()
        curs.execute("SELECT value FROM kv WHERE key=?", (key,) )
        row = curs.fetchone()
        if row is None:
            if missing_as_none:
                return None
            else:
                raise KeyError("Key %r not found"%key)
        else:
            return row[0]


    def put(self, key, value, commit:bool=True):
        ''' Sets/updates value for a key. 
            
            Types will be checked according to what you inited this class with.
            
            commit=False lets us do bulk commits, mostly when you want to a load of small changes without becoming IOPS bound.
            If you care less about speed, and/or more about parallel access, you can ignore this.
        '''
        if self.read_only:
            raise RuntimeError('Attempted put() on a store that was opened read-only.  (you can subvert that but may not want to)')

        self._checktype_key(key)
        self._checktype_value(value)

        curs = self.conn.cursor()
        if not commit  and  not self._in_transaction:
            curs.execute('BEGIN')
            self._in_transaction = True

        curs.execute('INSERT INTO kv (key, value) VALUES (?, ?)  ON CONFLICT (key) DO UPDATE SET value=?', (key,value, value) )
        if commit:
            self.commit()


    def delete(self, key, commit:bool=True):
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


    def _get_meta(self, key:str, missing_as_none=False):
        ''' For internal use, preferably don't use.
            This is an extra str:str table in there that is intended to be separate, with some keys special to these classes.
              ...you could abuse this for your own needs if you wish, but try not to.
        '''
        curs = self.conn.cursor()
        curs.execute("SELECT value FROM meta WHERE key=?", (key,) )
        row = curs.fetchone()
        if row is None:
            if missing_as_none:
                return None
            else:
                raise KeyError("Key %r not found"%key)
        else:
            return row[0]


    def _put_meta(self, key:str, value:str):
        ''' For internal use, preferably don't use.   See also _get_meta() '''
        if self.read_only:
            raise RuntimeError('Attempted _put_meta() on a store that was opened read-only.  (you can subvert that but may not want to)')
        curs = self.conn.cursor()
        curs.execute('BEGIN')
        curs.execute('INSERT INTO meta (key, value) VALUES (?, ?)  ON CONFLICT (key) DO UPDATE SET value=?', (key,value, value) )
        self.commit()


    def _delete_meta(self, key:str):
        ''' For internal use, preferably don't use.   See also _get_meta() '''
        if self.read_only:
            raise RuntimeError('Attempted _put_meta() on a store that was opened read-only.  (you can subvert that but may not want to)')
        curs = self.conn.cursor() # TODO: check that's correct when commit==False
        curs.execute('DELETE FROM meta where key=?', ( key,) )
        self.commit()



    def commit(self):
        ' commit changes - for when you use put() or delete() with commit=False to do things in a larger transaction '
        self.conn.commit()
        self._in_transaction = False

    # # TODO: test
    # def rollback(self):
    #     ' roll back changes '
    #     # maybe only if _in_transaction?
    #     self.conn.rollback()
    #     self._in_transaction = False


    def estimate_waste(self):
        return self.conn.execute('SELECT (freelist_count*page_size) as FreeSizeEstimate  FROM pragma_freelist_count, pragma_page_size').fetchone()[0]

    # def incremental_vacuum(self):
    #     ' assuming we created with "PRAGMA auto_vacuum = INCREMENTAL" we can do cleanup. Ideally you do with some interval when you remove/update things '
    #     # https://www.sqlite.org/pragma.html#pragma_auto_vacuum
    #     if self._in_transaction:
    #         self.commit()
    #     self.conn.execute('PRAGMA schema.incremental_vacuum')

    def vacuum(self):
        ''' After a lot of deletes you could compact the store with vacuum().
            However, note this rewrites the entire file, so the more data you store, the longer this takes.
            
            Note that if we were left in a transaction (due to commit=False), ths is commit()ed first. 
        '''
        if self._in_transaction:
            self.commit()
        self.conn.execute('vacuum')


    # def size(self):
    #     ' Returns the approximate amount of the contained data, in bytes '
    #     curs = self.conn.cursor()
    #     curs.execute("select page_size, page_count from pragma_page_count, pragma_page_size")
    #     page_size, page_count = curs.fetchone()
    #     curs.close()
    #     return page_size *page_count
    #     #return os.stat( self.path ).st_size


    # # TODO: test
    # def truncate(self, key, vacuum=True):
    #     ''' remove all kv entries.
    #         If we were still in a transaction, we roll that back  first
    #     '''
    #     self._checktype_key(key)
    #     curs = self.conn.cursor() # TODO: check that's correct when commit==False
    #     if self._in_transaction:
    #         self.rollback()
    #         self._in_transaction = True
    #     curs.execute('DELETE FROM kv')  # https://www.techonthenet.com/sqlite/truncate.php
    #     if vacuum:
    #         self.vacuum()


    def close(self):
        self.conn.close()

     
    def iterkeys(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT key FROM kv'):
            yield row[0]
        curs.close()


    def keys(self): 
        return list( self.iterkeys() )


    def itervalues(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT value FROM kv'):
            yield row[0]
        curs.close()


    def values(self): 
        return list( self.itervalues() )


    def iteritems(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT key, value FROM kv'):
            yield row[0], row[1]
        curs.close()


    def items(self):
        return list( self.iteritems() )


    def __iter__(self): # TODO: check
        return self.iterkeys()


    def __repr__(self):
        return '<LocalKV(%r)>'%( os.path.basename(self.path), )


    def __len__(self):
        return self.conn.execute('SELECT COUNT(*) FROM kv').fetchone()[0]  # TODO: double check


    # Choice not to actually have it behave like a dict - this seems like a leaky abstraction,
    # so we make you write out the .get and .put to make you realize it's different behaviour not like a real dict
    # ...bit still a sneaky contains:
    def __contains__(self, key):
        return self.conn.execute('SELECT 1 FROM kv WHERE key = ?', (key,)).fetchone() is not None


    #def __getitem__(self, key):
    #    ret = self.get(key)
    #    if ret is None:
    #        raise KeyError()
    #    return ret
        
    #def __setitem__(self, key, value):
    #    self.put(key, value)

    #def __delitem__(self, key):
    #    # TODO: check whether we can ignore it not being there, or must raise KeyError for interface correctness
    #    #if key not in self:
    #    #    raise KeyError(key)
    #    self.conn.execute('DELETE FROM kv WHERE key = ?', (key,)) 





class PickleKV(LocalKV):
    ''' Like localKV, but 
        - typing fixed at str:bytes 
        - put() stores using pickle, get() unpickles
        Will be a bit slower, but lets you more transpoarently store e.g. nested python structures, like dicts

        Note that
         - pickle isn't the most interoperable choice  (json or msgpack would be preferable)
         - pickle isn't the fastest choice             (msgpack would be preferable)
         - pickle is chosen mostly in case we want to store a date or datetime (json and msgpack don't like those)

        Currently only intended to be used by datasets, though feel free to 
    '''
    def __init__(self, path, protocol_version=3):
        ''' defaults to pickle protocol 3 to support all of py3.x (though not 2)
            consider getting/setting meta to check that an existing store actually _should_ be used like this
        '''
        super(PickleKV, self).__init__( path, key_type=str, value_type=bytes )
        self.protocol_version = protocol_version

    def get(self, key:str):
        " Note that unpickling could fail "
        value = super(PickleKV, self).get( key )
        unpickled = pickle.loads(value)
        return unpickled
        
    def put(self, key:str, value):
        " See LocalKV.put().   Unlike that, value is not checked for type, just pickled. Which can fail. "
        pickled = pickle.dumps(value, protocol=self.protocol_version)
        super(PickleKV, self).put( key, pickled )


    def itervalues(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT value FROM kv'):
            yield pickle.loads( row[0] )

    def iteritems(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT key, value FROM kv'):
            yield row[0], pickle.loads( row[1] )


# msgpack would be faster than pickle, more interoperable, and safer - but an extra dependency

# json is more interoperable, but slower and doesn't e.g. deal with date/datetime

# class JSONKV(LocalKV):
#     ''' Like localKV, but 
#         - typing fixed at str:str 
#         - put() and get() will store as JSON
#         More interoperable, but won't store quite as many things as PickleKV
#     '''
#     def __init__(self, path):
#         super(JSONKV, self).__init__( path, key_type=str, value_type=str )

#     def get(self, key:str):
#         value = super(JSONKV, self).get( key )
#         dec = json.loads(value)
#         return dec
        
#     def put(self, key:str, value):
#         " See LocalKV.put().   Unlike that, value is not checked for type, just dumped into JSON. Which can fail. "
#         enc = json.dumps(value)
#         super(JSONKV, self).put( key, enc )


#     def itervalues(self):
#         curs = self.conn.cursor()
#         for row in curs.execute('SELECT value FROM kv'):
#             yield json.loads( row[0] )

#     def iteritems(self):
#         curs = self.conn.cursor()
#         for row in curs.execute('SELECT key, value FROM kv'):
#             yield row[0], json.loads( row[1] )



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
    if store.key_type not in (str,None)  or  store.value_type not in (bytes, None):
        raise TypeError('cached_fetch() expects a str:bytes store (or for you to disable checks with None,None),  not a %r:%r'%(store.key_type.__name__, store.value_type.__name__))
    # yes, the following could be a few lines shorter, but this is arguably a little more readable
    if force_refetch == False:
        try:
            ret = store.get(url)
            #print("CACHED")
            return ret, True
        except KeyError as ke:
            data = wetsuite.helpers.net.download( url ) 
            #print("FETCHED")
            store.put( url, data )
            return data, False
    else: # force_refetch == True
        data = wetsuite.helpers.net.download( url ) 
        #print("FORCE-FETCHED")
        store.put( url, data )
        return data, False


def open_store(dbname:str, key_type, value_type):
    ''' A helper that opens a LocalKV in the local wetsuite directory, 
        mostly so that you don't have to think about handing in a reproducable absolute path yourself.

        Just a filename, e.g.
          docs = open_store('docstore.db')
        will open the same store regardless of the directory the interpreter is currently considered to be in.
        It's suggested you use descriptive names so that you don't open existing stores without meaning to.

        for notes on key_type and value_type, see LocalKV.__init__()

        CONSIDER: listening to a WETSUITE_BASE_DIR to override our "put in user's homedir" behaviour,
                  this might make more sense e.g. to point it at distributed storage without symlink juggling
    '''
    if os.sep in dbname:
        raise ValueError('This function is meant to take a name, not an absolute path.  If you prefer to determine an absolute path, you can instantiate LocalKV directly.')
    # CONSIDER: sanitize filename?
    if dbname == ':memory:':  # allow the sqlite special value of :memory: 
        ret = LocalKV( dbname, key_type=key_type, value_type=value_type )
    else:
        dirs = wetsuite.datasets.wetsuite_dir()
        _docstore_path = os.path.join( dirs['stores_dir'], dbname )
        ret = LocalKV( _docstore_path, key_type=key_type, value_type=value_type )
    return ret


def list_stores():
    ''' Lookin the directory that open_store() put things in, check which ones seem to be stores.
        Returns a list of  (relative filename in there,  absolute path)
    '''
    dirs = wetsuite.datasets.wetsuite_dir()
    stores_dir = dirs['stores_dir']

    ret = []
    for basename in os.listdir( stores_dir ):
        abspath = os.path.join( stores_dir, basename )
        if os.path.isfile( abspath ):
            if is_file_a_store( abspath ):
                ret.append( (basename, abspath) )
    return ret


def is_file_a_store(path, skip_table_check=False):
    ''' Checks that the path seems to point to one of our stores.
        More specifailly: whether it is an sqlite(3) database, and has a table called 'kv'
    '''
    is_sqlite3 = None
    with open(path, 'rb') as f:
        is_sqlite3 = (f.read(15) == b'SQLite format 3' )
    if not is_sqlite3:
        return False

    if skip_table_check:
        return True
    else:
        has_kv_table = None
        conn = sqlite3.connect( path )
        curs = conn.cursor()
        curs.execute("SELECT name  FROM sqlite_master  WHERE type='table'")
        for tablename, in curs.fetchall():
            if tablename=='kv':
                has_kv_table = True
        conn.close()
        return has_kv_table
