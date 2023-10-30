''' This is intended to store store collections of data on disk,
      relatively unobtrusive to use    (better than e.g. lots of files),
      and with quick random access     (better than e.g. JSONL).

    It currently centers on a key-value store.
    See the docstring on the LocalKV class for more details.

    This is used e.g. by various data collection, and by distributed datasets.
    

    HOW TO USE:
    - You can create your own specific stores by doing something like:
        mystore_path = os.path.join( project_data_dir, 'docstore.db')  # OS-agnostic path join
        mystore = LocalKV( mystore_path )
    OR
        open_store( 'docstore.db' ), which places it in the wetsuite directory in your homedir

    "Why two ways?"
        The first gives you direct control, 
            ...but with relative paths, it will create in whatever is the current working directory,
               which makes it easy for you to confuse yourself with databases all over the place
            ...but with absolute paths you will easily make things less portable via hardcoded paths
        The latter ensures that whenever you give the same name, you open the same store, 
            no thought about where it goes exactly  (if you want to know where exactly, use .path)

                     
    By default, each write is committed individually, (because SQlite3's driver defaults to autocommit)
    If you want more performant bulk writes, 
      use put() with commit=False, and
      do an explicit commit() afterwards
      ...BUT if a script borks in the middle of something uncommited, you will need to do manual cleanup.

      
    "Could I access these SQLite databases myself?"
        Sure, particularly when just reading.
        The code is mainly there for convenience and checks. Consider:
          sqlite3 store.db 'select key,value from kv limit 10 ' | less
        It only starts getting special once you using MsgpackKV, or the extra parsing and wrapping that wetsuite.datasets adds.

      
    CONSIDER: writing a ExpiringLocalKV that cleans up old entries
    CONSIDER: writing variants that do convert specific data, letting you e.g. set/fetch dicts, or anything else you could pickle
'''
import os
from typing import Tuple
import collections.abc
import sqlite3
import wetsuite.helpers.util     # to get wetsuite_dir
import wetsuite.helpers.net
import wetsuite.helpers.format


   
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
            CONSIDER: storing typing in the file in the meta table
        - doing it via functions is a little more typing yet also exposes some sqlite things (using transactions, vacuum) for when you know how to use them.
            and is arguably clearer than 'this particular dict-like happens to get stored magically'
        - On concurrency: As per basic sqlite behaviour, multiple processes can read the same database,
          but only one can write, and when you leave a writer with uncommited data for nontrivial amounts of time,
          readers are likely to bork out on the fact it's locked (CONSIDER: have it retry / longer).
          This is why by default we leave it on autocommit, even though that can be slower.

        - It wouldn't be hard to also make it act largely like a dict,   implementing __getitem__, __setitem__, and __delitem__
          but this muddies the waters as to its semantics, in particularly when things you set are actually saved. 

          So we try to avoid a leaky abstraction, by making you write out all the altering operatiopns, 
            and actually all of them, e.g.  get(), put(),  keys(), values(), and items(),
            because those can at least have docstrings to warn you, rather than breaking your reasonable expectations. 

          ...exceptions are
            __len__        for amount of items                   CONSIDER: making that len()
            __contains__   backing 'is this key in the store'),  CONSIDER: making that e.g. has_key() instead
          and also:
            __iter__       which is actually iterkeys()         CONSIDER: removing it
            __getitem__    supports the views-with-a-len  
          The last were tentative until keys(), values(), and items() started giving views.  

          TODO: make a final decision where to sit between clean abstractions and convenience.
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
        # 
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


    def _open(self, timeout=2.0):
        ' Open file path set by init.  Could be merged into init ' 
        #make_tables = (self.path==':memory:')  or  ( not os.path.exists( self.path ) )    # will be creating that file, or are using an in-memory database ?  Also how to combine with read_only?
        self.conn = sqlite3.connect( self.path, timeout=timeout )
        # Note: curs.execute is the regular DB-API way,  conn.execute is a shorthand that gets a temporary cursor
        with self.conn:
            if self.read_only:
                self.conn.execute("PRAGMA query_only = true") # https://www.sqlite.org/pragma.html#pragma_query_only
                # if read-only, we assume you are opening something that was aleady created before
            else:
                self.conn.execute("PRAGMA auto_vacuum = INCREMENTAL")  # TODO: see that this does what I think it does    https://www.sqlite.org/pragma.html#pragma_auto_vacuum
                self.conn.execute("CREATE TABLE IF NOT EXISTS meta (key text unique NOT NULL, value text)")
                self.conn.execute("CREATE TABLE IF NOT EXISTS kv   (key text unique NOT NULL, value text)")


    def _checktype_key(self, val):
        ' checks a value according to the key_type you handed into the constructor '
        if self.key_type is not None  and  not isinstance(val, self.key_type): # None means don't check 
            raise TypeError('Only keys of type %s are allowed, you gave a %s'%(self.key_type.__name__, type(val).__name__))


    def _checktype_value(self, val):
        ' checks a value according to the value_type you handed into the constructor '
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

            CONSIDER: making commit take an integer as well, meaning 'commit every X operations'
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
        ''' For internal use, preferably don't use.   See also _get_meta(), _delete_meta() '''
        if self.read_only:
            raise RuntimeError('Attempted _put_meta() on a store that was opened read-only.  (you can subvert that but may not want to)')
        curs = self.conn.cursor()
        curs.execute('BEGIN')
        curs.execute('INSERT INTO meta (key, value) VALUES (?, ?)  ON CONFLICT (key) DO UPDATE SET value=?', (key,value, value) )
        self.commit()


    def _delete_meta(self, key:str):
        ''' For internal use, preferably don't use.   See also _get_meta(), _delete_meta() '''
        if self.read_only:
            raise RuntimeError('Attempted _put_meta() on a store that was opened read-only.  (you can subvert that but may not want to)')
        curs = self.conn.cursor() # TODO: check that's correct when commit==False
        curs.execute('DELETE FROM meta where key=?', ( key,) )
        self.commit()


    def commit(self):
        ' commit changes - for when you use put() or delete() with commit=False to do things in a larger transaction '
        self.conn.commit()
        self._in_transaction = False


    def rollback(self):
        ' roll back changes '
        # maybe only if _in_transaction?
        self.conn.rollback()
        self._in_transaction = False


    def estimate_waste(self):
        return self.conn.execute('SELECT (freelist_count*page_size) as FreeSizeEstimate  FROM pragma_freelist_count, pragma_page_size').fetchone()[0]


    # def incremental_vacuum(self):
    #     ''' assuming we created with "PRAGMA auto_vacuum = INCREMENTAL" we can do cleanup. Ideally you do with some interval when you remove/update things
    #         CONSIDER our own logic to that?  Maybe purely per interpreter (after X puts/deletes),  and maybe do it on close?
    #     '''
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


    def bytesize(self) -> int:
        ' Returns the approximate amount of the contained data, in bytes  (may be a few dozen kilobytes off) '
        curs = self.conn.cursor()
        curs.execute("select page_size, page_count from pragma_page_count, pragma_page_size")
        page_size, page_count = curs.fetchone()
        curs.close()
        return page_size *page_count
        #return os.stat( self.path ).st_size


    def truncate(self, vacuum=True):
        ''' remove all kv entries.
            If we were still in a transaction, we roll that back first
        '''
        curs = self.conn.cursor() # TODO: check that's correct when commit==False
        if self._in_transaction:
            self.rollback()
        curs.execute('DELETE FROM kv')  # https://www.techonthenet.com/sqlite/truncate.php
        self.commit()
        if vacuum:
            self.vacuum()


    def close(self):
        if self._in_transaction:
            pass # DECIDE 
        self.conn.close()


    #TODO: see if the view's semantics in keys(), values(), and items() are actually correct. 
    #      Note there's a bunch of implied heavy lifting in hnading self to those view classes,
    #         which require that that relies on __iter__ and __getitem__ to be there

    def iterkeys(self):
        """ Returns a generator that yields all keus
            If you wanted a list with all keys, use list( store.keys() )
        """
        curs = self.conn.cursor()
        for row in curs.execute('SELECT key FROM kv'):
            yield row[0]
        curs.close()

    def keys(self):
        """ Returns an iterable of all keys.  (a view with a len, rather than just a generator) """
        return collections.abc.KeysView( self ) # TODO: check that this is enough
        #return list( self.iterkeys() )

    def itervalues(self):
        """ Returns a generator that yields all values. 
            If you wanted a list with all the values, use list( store.values )
        """
        curs = self.conn.cursor()
        for row in curs.execute('SELECT value FROM kv'):
            yield row[0]
        curs.close()

    def values(self):
        """ Returns an iterable of all values.  (a view with a len, rather than just a generator)  """
        return collections.abc.ValuesView( self )
        

    def iteritems(self):
        """ Returns a generator that yields all items """
        curs = self.conn.cursor()
        try: # TODO: figure out whether this is necessary
            for row in curs.execute('SELECT key, value FROM kv'):
                yield row[0], row[1]
        finally:
            curs.close()

    def items(self):
        """ Returns an iteralble of all items.    (a view with a len, rather than just a generator)  """
        return collections.abc.ItemsView( self ) # this relies on __getitem__ which we didn't really want, maybe wrap a class to hide that?


    def __repr__(self):
        return '<LocalKV(%r)>'%( os.path.basename(self.path), )


    def __len__(self):
        return self.conn.execute('SELECT COUNT(*) FROM kv').fetchone()[0]  # TODO: double check


    # Choice not to actually have it behave like a dict - this seems like a leaky abstraction,
    # so we make you write out the .get and .put to make you realize it's different behaviour not like a real dict

    def __iter__(self): # TODO: check
        " Using this object as an iterator yields its keys (equivalent to .iterkeys()) "
        return self.iterkeys()

    def __getitem__(self, key): # this one is here only really to support the ValuesView and Itemsview
        ret = self.get(key)
        if ret is None:
            raise KeyError()
        return ret
        
    #def __setitem__(self, key, value):
    #    self.put(key, value)

    #def __delitem__(self, key):
    #    # TODO: check whether we can ignore it not being there, or must raise KeyError for interface correctness
    #    #if key not in self:
    #    #    raise KeyError(key)
    #    self.conn.execute('DELETE FROM kv WHERE key = ?', (key,)) 

    # ...but we still sneakily have:
    def __contains__(self, key):
        return self.conn.execute('SELECT 1 FROM kv WHERE key = ?', (key,)).fetchone() is not None


    ## Used as a context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type,exc_value, exc_traceback):
        self.close()





# msgpack would be faster than pickle, more interoperable, and safer - but an extra dependency, and does a little less.

# json is more interoperable, but slower and doesn't e.g. deal with date/datetime


try:
    import msgpack

    class MsgpackKV(LocalKV):
        ''' Like localKV, but 
            - typing fixed at str:bytes 
            - put() stores using pickle, get() unpickles

            Will be a bit slower, but lets you more transparently store e.g. nested python structures, like dicts
            ...but only of primitive types, and not e.g. datetime.

            msgpack is used as a somewhat faster alternative to json and pickle (though that barely matters for smaller values)
        
            Note that this does _not_ change how the meta table works.
        '''
        def __init__(self, path, key_type=str, value_type=None, read_only=False):
            ''' value_type is ignored; I need to restructure this
            '''
            super(MsgpackKV, self).__init__( path, key_type=str, value_type=None, read_only=read_only )

        def get(self, key:str):
            " Note that unpickling could fail "
            value = super(MsgpackKV, self).get( key )
            unpacked = msgpack.loads(value)
            return unpacked
            
        def put(self, key:str, value, commit:bool=False):
            " See LocalKV.put().   Unlike that, value is not checked for type, just pickled. Which can fail. "
            packed = msgpack.dumps(value)
            super(MsgpackKV, self).put( key, packed, commit )

        def itervalues(self):
            curs = self.conn.cursor()
            for row in curs.execute('SELECT value FROM kv'):
                yield msgpack.loads( row[0], strict_map_key=False )

        def iteritems(self):
            curs = self.conn.cursor()
            for row in curs.execute('SELECT key, value FROM kv'):
                yield row[0], msgpack.loads( row[1], strict_map_key=False )    
except ImportError:
    # warning?
    pass


# class PickleKV(LocalKV):
#     ''' Like localKV, but 
#         - typing fixed at str:bytes 
#         - put() stores using pickle, get() unpickles
#         Will be a bit slower, but lets you more transpoarently store e.g. nested python structures, like dicts

#         Note that
#          - pickle isn't the most interoperable choice  (json or msgpack would be preferable)
#          - pickle isn't the fastest choice             (msgpack would be preferable)
#          - pickle is chosen mostly in case we want to store a date or datetime (json and msgpack don't like those)

#         Note that this does _not_ change how the meta table works.

#         Currently only intended to be used by datasets, though feel free to 
#     '''
#     def __init__(self, path, protocol_version=3):
#         ''' defaults to pickle protocol 3 to support all of py3.x (though not 2)
#             consider getting/setting meta to check that an existing store actually _should_ be used like this
#         '''
#         super(PickleKV, self).__init__( path, key_type=str, value_type=bytes )
#         self.protocol_version = protocol_version

#     def get(self, key:str):
#         " Note that unpickling could fail "
#         value = super(PickleKV, self).get( key )
#         unpickled = pickle.loads(value)
#         return unpickled
        
#     def put(self, key:str, value):
#         " See LocalKV.put().   Unlike that, value is not checked for type, just pickled. Which can fail. "
#         pickled = pickle.dumps(value, protocol=self.protocol_version)
#         super(PickleKV, self).put( key, pickled )


#     def itervalues(self):
#         curs = self.conn.cursor()
#         for row in curs.execute('SELECT value FROM kv'):
#             yield pickle.loads( row[0] )

#     def iteritems(self):
#         curs = self.conn.cursor()
#         for row in curs.execute('SELECT key, value FROM kv'):
#             yield row[0], pickle.loads( row[1] )






def cached_fetch(store, url:str, force_refetch:bool=False) -> Tuple[bytes, bool]:
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


def open_store(dbname:str, key_type, value_type, inst=LocalKV, read_only=False) -> LocalKV:
    ''' Note that if you give a name without a path separator, e.g.
            docs = open_store('docstore.db')
        then will open the same store every time  (picking a path in a wetsuite directory in your user profile) 
        regardless of the directory the interpreter is currently considered to be in.
        Mostly so that you don't have to think about handing in a reproducable absolute path yourself.
            HINT: It's suggested you use descriptive names so that you don't open existing stores without meaning to.

            CONSIDER: listening to a WETSUITE_BASE_DIR to override our "put in user's homedir" behaviour,
                    this might make more sense e.g. to point it at distributed storage without symlink juggling
        

        If you actually _wanted_ it in the current directory, you will have to give an absolute path,
            e.g. os.path.abspath('mystore.db').
            We make this harder to do accidentally because this is a common mistake around sqlite.


        For notes on key_type and value_type, see LocalKV.__init__()


        inst is currently a hack, this might actually need to become a factory
    '''
    # CONSIDER: sanitize filename?
    if dbname == ':memory:':  # special-case the sqlite value of ':memory:' (pass it through) 
        ret = inst( dbname, key_type=key_type, value_type=value_type, read_only=read_only )

    elif os.sep in dbname:
        ret = inst( dbname, key_type=key_type, value_type=value_type )

    else: # bare name, 
        dirs = wetsuite.helpers.util.wetsuite_dir()
        _docstore_path = os.path.join( dirs['stores_dir'], dbname )
        ret = inst( _docstore_path, key_type=key_type, value_type=value_type, read_only=read_only )
    return ret


def list_stores( skip_table_check=True, get_num_items=False ):
    ''' Look in the directory that open_store() put things in,
          check which ones seem to be stores (does IO to do so).
        Returns a dict with details for each

        skip_table_check - if true, only tests whether it's a sqlite file, not whether it contains the table we expect.
                           because when it's in the stores directory, chances are we put it there, and we can avoid IO and locking.
        
        get_num_items    - does not by default get the number of items, because that can need a bunch of IO, and locking.
    '''
    dirs = wetsuite.helpers.util.wetsuite_dir()
    stores_dir = dirs['stores_dir']
    ret = []
    for basename in os.listdir( stores_dir ):
        abspath = os.path.join( stores_dir, basename )
        if os.path.isfile( abspath ):
            if is_file_a_store( abspath, skip_table_check=skip_table_check ): 
                bytesize = os.stat(abspath).st_size
                kv = LocalKV(abspath, key_type=None, value_type=None, read_only=True)
                itemdict = {
                    'basename':basename, 
                    'path':abspath,
                    'bytesize':bytesize,
                    'bytesize_readable':wetsuite.helpers.format.kmgtp( bytesize ),
                }
                if get_num_items: 
                    itemdict['num_items'] = len( kv )
                
                itemdict['description'] = kv._get_meta('description', True)
                ret.append( itemdict )
                kv.close()
    return ret


def is_file_a_store(path, skip_table_check=False):
    ''' Checks that the path seems to point to one of our stores.
        More specifailly: whether it is an sqlite(3) database, and has a table called 'kv'

        You can skip the latter test. It avoids opening the file, so avoids a possible timeout on someone else having the store open for writing.
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
