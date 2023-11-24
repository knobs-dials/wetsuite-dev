'''
This is intended to store store collections of data on disk,
relatively unobtrusive to use    (better than e.g. lots of files),
and with quick random access     (better than e.g. JSONL).

It currently centers on a key-value store.
See the docstring on the LocalKV class for more details.

This is used e.g. by various data collection, and by distributed datasets.


BASIC USE: ::
    mystore = LocalKV( 'docstore.db' )

Notes:
    - on the path/name argument:
        - just a name ( without os.sep, that is, / or \\ ) will be resolved to a path where wetsuite keeps various stores
      - an absolute path will be passed through             
          ...but this isn't very portable until you do things like   os.path.join( myproject_data_dir, 'docstore.db')
        - a relative path with os.sep will be passed through  
          ...which is only as portable as the cwd is predictable)
        - ':memory:' is in-memory only                        
          See also resolve_path() for more details

    - by default, each write is committed individually, (because SQlite3's driver defaults to autocommit)
      If you want more performant bulk writes, 
      use put() with commit=False, and
      do an explicit commit() afterwards
      ...BUT if a script borks in the middle of something uncommited, you will need to do manual cleanup.
    
    - you _could_ access these SQLite databses yourself, particularly when just reading.
      Our code is mainly there for convenience and checks.     
      Consider: `sqlite3 store.db 'select key,value from kv limit 10 ' | less`
      It only starts getting special once you using MsgpackKV, or the extra parsing and wrapping that wetsuite.datasets adds.

CONSIDER: writing a ExpiringLocalKV that cleans up old entries
CONSIDER: writing variants that do convert specific data, letting you e.g. set/fetch dicts, or anything else you could pickle
'''
import os
import os.path
import random
import collections.abc
from typing import Tuple

import sqlite3
# msgpack should be more interoperable and safer than pickle, and slightly faster - but an extra dependency, and does a little less.
# json is more interoperable, but slower and (also) doesn't e.g. deal with date/datetime
import msgpack

import wetsuite.helpers.util     # to get wetsuite_dir
import wetsuite.helpers.net
import wetsuite.helpers.format


class LocalKV:
    '''
    A key-value store backed by a local filesystem.
    This is currently a fairly thin wrapper around SQLite - this may change.

    SQLite will still just store the type it gets, and this won't do conversions for you,
    it only enforces the values that go in are of the type you said you would put in.
    This will makes things more consistent, but is not a strict guarantee.
    
    You could change both key and value types - e.g. the cached_fetch function expects a str:bytes store

    Given: ::
        db = LocalKv('path/to/dbfile')
    Basic use is: ::
        db.put('foo', 'bar')
        db.get('foo')

    
    Notes:
      - It is a good idea to open the store with the same typing each  or you will still confuse yourself.
        CONSIDER: storing typing in the file in the meta table
      - doing it via functions is a little more typing yet also exposes some sqlite things 
        (using transactions, vacuum) for when you know how to use them.
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
            so you proably want think to think about repeating the same path in absolute sense
            ...see also the module docstring, and resolve_path()'s docstring

            read_only is only enforced in this wrapper to give slightly more useful errors. (we also give SQLite a PRAGMA)
        '''
        self.path = path
        self.path = resolve_path(self.path)   # tries to centralize the absolute/relative path handling code logic

        self.read_only = read_only
        self._open()
        # here in part to remind us that we _could_ be using converters  https://docs.python.org/3/library/sqlite3.html#sqlite3-converters
        if key_type not in (str, bytes, int, None):
            raise TypeError("We are currently a little overly paranoid about what to allow as key types (%r not allowed)"%key_type.__name__)
        if value_type not in (str, bytes, int, float, None):
            raise TypeError("We are currently a little overly paranoid about what to allow as value types (%r not allowed)"%value_type.__name__)

        self.key_type = key_type
        self.value_type = value_type
        self._in_transaction = False


    def _open(self, timeout=2.0):
        ''' Open the path previously set by init.
            This function could probably be merged into init, it was separated mostly with the idea that we could keep it closed when not using it. 
        '''
        #make_tables = (self.path==':memory:')  or  ( not os.path.exists( self.path ) )
        #    will be creating that file, or are using an in-memory database ?  Also how to combine with read_only?
        self.conn = sqlite3.connect( self.path, timeout=timeout )
        # Note: curs.execute is the regular DB-API way,  conn.execute is a shorthand that gets a temporary cursor
        with self.conn:
            if self.read_only:
                self.conn.execute("PRAGMA query_only = true")   # https://www.sqlite.org/pragma.html#pragma_query_only
                # if read-only, we assume you are opening something that was aleady created before, so we don't do...
            else:
                # TODO: see that this pragma does what I think it does    https://www.sqlite.org/pragma.html#pragma_auto_vacuum
                self.conn.execute("PRAGMA auto_vacuum = INCREMENTAL")

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

            Note that you should not expect the file to shrink until you do a vacuum()  (which will need to rewrite the file).
        '''
        if self.read_only:
            raise RuntimeError('Attempted delete() on a store that was opened read-only.  (you can subvert that but may not want to)')
        
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
        curs.close()
        if row is None:
            if missing_as_none:
                return None
            else:
                raise KeyError("Key %r not found"%key)
        else:
            return row[0]


    def _put_meta(self, key:str, value:str):
        ''' For internal use, preferably don't use.   See also _get_meta(), _delete_meta().   Note this does an implicit commit() '''
        if self.read_only:
            raise RuntimeError('Attempted _put_meta() on a store that was opened read-only.  (you can subvert that but may not want to)')
        curs = self.conn.cursor()
        curs.execute('BEGIN')
        curs.execute('INSERT INTO meta (key, value) VALUES (?, ?)  ON CONFLICT (key) DO UPDATE SET value=?', (key,value, value) )
        self.commit()
        curs.close()


    def _delete_meta(self, key:str):
        ''' For internal use, preferably don't use.   See also _get_meta(), _delete_meta().   Note this does an implicit commit() '''
        if self.read_only:
            raise RuntimeError('Attempted _put_meta() on a store that was opened read-only.  (you can subvert that but may not want to)')
        curs = self.conn.cursor() # TODO: check that's correct when commit==False
        curs.execute('DELETE FROM meta where key=?', ( key,) )
        self.commit()
        curs.close()


    def commit(self):
        ' commit changes - for when you use put() or delete() with commit=False to do things in a larger transaction '
        self.conn.commit()
        self._in_transaction = False


    def rollback(self):
        ' roll back changes '
        # maybe only if _in_transaction?
        self.conn.rollback()
        self._in_transaction = False


    def close(self):
        ' Closes file if still open. Note that if there was a transaction still open, it will be rolled back, not committed. '
        if self._in_transaction:
            self.rollback()
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
        return self.get(key) # which would itself raise KeyError if applicable

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



    ### Convenience functions, not core functionality

    def estimate_waste(self):
        ' Estimate how many bytes might be cleaned by a .vacuum() '
        return self.conn.execute('SELECT (freelist_count*page_size) as FreeSizeEstimate  FROM pragma_freelist_count, pragma_page_size').fetchone()[0]


    # def incremental_vacuum(self):
    #     ''' assuming we created with "PRAGMA auto_vacuum = INCREMENTAL" we can do cleanup.
    #         deally you do with some interval when you remove/update things
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
        ''' Returns the approximate amount of the contained data, in bytes  
            (may be a few dozen kilobytes off, or more, because it counts in pages) 
        '''
        #if self.path == ':memory:'
        curs = self.conn.cursor()
        curs.execute("select page_size, page_count from pragma_page_count, pragma_page_size")
        page_size, page_count = curs.fetchone()
        curs.close()
        return   page_size * page_count
        #else:
        #    return os.stat( self.path ).st_size


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


    def random_choice(self):
        ''' Returns a single (key, value) item from the store, selected randomly.
        
            Convenience function, because doing this properly yourself takes two or three lines 
            (you can't random.choice/random.sample a view,  
            so to do it properly you basically have to materialize all keys - and not accidentally all values)
            BUT assume this is slower than working on the keys yourself.
        '''
        all_keys = list( self.keys() )
        chosen_key = random.choice( all_keys )
        return chosen_key, self.get(chosen_key)


    def random_sample(self, amount):
        ''' Returns an amount of [(key, value), ...] list from the store, selected randomly.
        
            Convenience function, because doing this properly yourself takes two or three lines 
            (you can't random.choice/random.sample a view,  
            so to do it properly you basically have to materialize all keys - and not accidentally all values)
            BUT assume this is slower than working on the keys yourself.
        '''
        all_keys = list( self.keys() )
        chosen_keys = random.sample( all_keys, amount )
        return list( (chosen_key, self.get(chosen_key))  for chosen_key in chosen_keys)




class MsgpackKV(LocalKV):
    ''' Like localKV, but 
        - typing fixed at str:bytes 
        - put() stores using pickle, get() unpickles

        Will be a bit slower because it's doing that on the fly, but lets you more transparently store things like nested python dicts
        ...but only of primitive types, and not e.g. datetime.

        msgpack is used as a somewhat faster alternative to json and pickle (though that barely matters for smaller values)
    
        Note that this does _not_ change how the meta table works.
    '''
    def __init__(self, path, key_type=str, value_type=None, read_only=False):
        ''' value_type is ignored; I need to restructure this
        '''
        super().__init__( path, key_type=str, value_type=None, read_only=read_only )

        # this is meant to be able to detect/signal incorrect interpretation, not fully used yet
        if self._get_meta('valtype', missing_as_none=True) is None:
            self._put_meta('valtype','msgpack')


    def get(self, key:str):
        ''' Note that unpickling could fail 
            TODO: clarify the missing missing_as_none
        '''
        value = super().get( key )
        unpacked = msgpack.loads(value)
        return unpacked


    def put(self, key:str, value, commit:bool=True):
        " See LocalKV.put().   Unlike that, value is not checked for type, just pickled. Which can fail. "
        packed = msgpack.dumps(value)
        super().put( key, packed, commit )


    def itervalues(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT value FROM kv'):
            yield msgpack.loads( row[0], strict_map_key=False )


    def iteritems(self):
        curs = self.conn.cursor()
        for row in curs.execute('SELECT key, value FROM kv'):
            yield row[0], msgpack.loads( row[1], strict_map_key=False )



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
        @return: (data, came_from_cache)

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
        raise TypeError('cached_fetch() expects a str:bytes store (or for you to disable checks with None,None),  not a %r:%r'%(
            store.key_type.__name__,
            store.value_type.__name__
        ))
    # yes, the following could be a few lines shorter, but this is arguably a little more readable
    if force_refetch is False:
        try:
            ret = store.get(url)
            #print("CACHED")
            return ret, True
        except KeyError:
            data = wetsuite.helpers.net.download( url )
            #print("FETCHED")
            store.put( url, data )
            return data, False
    else: # force_refetch is True
        data = wetsuite.helpers.net.download( url )
        #print("FORCE-FETCHED")
        store.put( url, data )
        return data, False



def resolve_path( name:str ):
    ''' Note: the KV classes call this internally. 
        This is here less for you to use directly, more explain why.

        For context, handing a pathless base name to underlying sqlite would just put it in the current directory
        which isn't always where you think, so is likely to sprinkle databases all over the place.
        This is common point of confusion/mistake around sqlite (and files in general),
        so we make it harder to do accidentally, so that this doesn't become your problem.

        Using this function makes it a little more controlled where things go:     
            - Given a **bare name**, e.g. 'extracted.db', this returns an absolute path 
                within a "this is where wetsuite keeps its stores directory" within your user profile,
                e.g. /home/myuser/.wetsuite/stores/extracted.db or C:\\Users\\myuser\\AppData\\Roaming\\.wetsuite\\stores\\extracted.db
                Most of the point is that handing in the same name will lead to opening the same store, regardless of details.

            - hand in **`:memory:`** if you wanted a memory-only store, not backed by disk

            - given an absolute path, it will use that
                so if you actually _wanted_ it in the current directory, instead of this function 
                consider something like  `os.path.abspath('mystore.db')`

            - given a relative path, it will pass that through -- which will open it relative to the current directory

        Notes:
            - should be idempotent, so shouldn't hurt to call this more than once on the same path 
                (in that it _should_ always produce a path with os.sep (...or :memory: ...), 
                which it would pass through the second time)

            - When you rely on the 'base name means it goes to a wetsuite directory', 
                it is suggested that you use descriptive names (e.g. 'rechtspraaknl_extracted.db', not 'extracted.db') 
                so that you don't open existing stores without meaning to.

            - us figuring out a place in your use profile for you
            This _is_ double-edged, though, in that we will get fair questions like
              - "I can't tell why my user profile is full" and 
              - "I can't find my files"   (sorry, they're not so useful to access directly)

        CONSIDER: 
            - listening to a WETSUITE_BASE_DIR to override our "put in user's homedir" behaviour,
            this might make more sense e.g. to point it at distributed storage without 
            e.g. you having to do symlink juggling
    '''
    # deal with pathlib arguments by flattening it to a string
    import pathlib
    if isinstance(name, pathlib.Path):
        name = str(name)

    if name == ':memory:':  # special-case the sqlite value of ':memory:' (pass it through)
        return name
    elif os.sep in name:    # assume it's an absolute path, or a relative one you _want_ resolved relative to cwd
        return name
    else:                     # bare name, do our "put in homedir" logic
        dirs = wetsuite.helpers.util.wetsuite_dir()
        return os.path.join( dirs['stores_dir'], name )


# def open_store(dbname:str, key_type, value_type, inst=LocalKV, read_only=False) -> LocalKV:
#     ''' For notes on key_type and value_type, see LocalKV.__init__()

#         dbname can be
#         - :memory:
#         - an absolute path (you decide where to put it)
#         - a relative path with os.sep in it (resolved relative to cwd)
#         - a bare name without os.sep in it (we place it somewhere in your home dir)

#         inst is currently a hack, this might actually need to become a factory
#     '''
#     # CONSIDER: sanitize filename?
#     if dbname == ':memory:':  # special-case the sqlite value of ':memory:' (pass it through)
#         ret = inst( dbname, key_type=key_type, value_type=value_type, read_only=read_only )

#     elif os.sep in dbname:
#         ret = inst( dbname, key_type=key_type, value_type=value_type )

#     else: # bare name,
#         _docstore_path = store_in_profile(dbname)
#         ret = inst( _docstore_path, key_type=key_type, value_type=value_type, read_only=read_only )
#     return ret


def list_stores( skip_table_check:bool=True, get_num_items:bool=False ):
    ''' Look in the directory that (everything that uses) resolve_path() puts things in,
        check which ones seem to be stores (does IO to do so).

        @return: a dict with details for each store

        @param skip_table_check: if true, only tests whether it's a sqlite file, not whether it contains the table we expect.
        because when it's in the stores directory, chances are we put it there, and we can avoid IO and locking.
        
        @param get_num_items: does not by default get the number of items, because that can need a bunch of IO, and locking.
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

                try:
                    itemdict['valtype'] = kv._get_meta('valtype')
                except KeyError:
                    pass

                itemdict['description'] = kv._get_meta('description', True)
                ret.append( itemdict )
                kv.close()
    return ret


def is_file_a_store(path, skip_table_check:bool=False):
    ''' Checks that the path seems to point to one of our stores.
        More specifailly: whether it is an sqlite(3) database, and has a table called 'kv'

        You can skip the latter test. It avoids opening the file, so avoids a possible timeout on someone else having the store open for writing.
    '''
    if not os.path.isfile(path):
        return False

    is_sqlite3 = None
    with open(path, 'rb') as f:
        is_sqlite3 =   f.read(15) == b'SQLite format 3' # check file magic
    if not is_sqlite3:
        return False

    if skip_table_check:
        return True # good enough for us, then

    has_kv_table = None
    conn = sqlite3.connect( path )
    curs = conn.cursor()
    curs.execute("SELECT name  FROM sqlite_master  WHERE type='table'")
    for tablename, in curs.fetchall():
        if tablename=='kv':
            has_kv_table = True
    conn.close()
    return has_kv_table
