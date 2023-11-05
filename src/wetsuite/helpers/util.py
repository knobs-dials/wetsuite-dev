''' Functions that I find myself reusing, largely in notebooks, 
    mostly to the end of inspecting data

'''
import os, difflib, hashlib


def wetsuite_dir():
    ''' Figure out where we can store data.
    
        Returns a dict with keys mentioning directories:
          wetsuite_dir: a directory in the user profile we can store things
          datasets_dir: a directory inside wetsuite_dir first that datasets.load() will put dataset files in 
          stores_dir:   a directory inside wetsuite_dir that localdata will put sqlite files in   

        Keep in mind:
        - When windows users have their user profile on the network, we try to pick a directory more likely to be shared by your other logins
        - ...BUT keep in mind network mounts tend not to implement proper locking, 
           so around certain things (e.g. our localdata.LocalKV) you invite corruption when multiple workstations write at the same time, 
           ...so don't do that. If you need distributed work, use an actually networked store, or be okay with read-only access.
    '''
    # CONSIDER: listen to an environment variable to override that base directory,
    #         to allow people to direct where to store this (might be useful e.g. on clustered filesystems)
    #         (an explicit argument wouldn't make sense when internals will call this)

    # CONSIDER: If we wanted to expose this to users, this function deserves to be in a more suitable location - maybe helpers/util?
    #         it's also used by localdata

    ret = {}

    # Note: expanduser("~") would do most of the work, as it works on win+linx+osx. 
    #   These additional tests are mainly for the case of AD-managed workstations, to try to direct it to store it in a shared area
    #   HOMESHARE is picked up (and preferred over USERPROFILE) because in this context, USERPROFILE might be a local, non-synced directory
    #     (even if most of its contents are junctions to places that _are_)
    # Yes, we do assume this will stay constant over time.
    userprofile = os.environ.get('USERPROFILE') # we assume these are only filled when it's actually windows - we could test that too via os.name or platform.system()
    homeshare   = os.environ.get('HOMESHARE')
    chose_dir = None
    if homeshare is not None:
        r_via_hs = os.path.join(homeshare, 'AppData', 'Roaming')
        if os.path.exists( r_via_hs ):
            chose_dir = os.path.join( r_via_hs, '.wetsuite' )
    elif userprofile is not None:
        r_via_up = os.path.join(userprofile, 'AppData', 'Roaming')
        if os.path.exists( r_via_up ):
            chose_dir = os.path.join( r_via_up, '.wetsuite' )

    if chose_dir is None:  # probably linux or osx, or weird windows
        home_dir = os.path.expanduser("~")
        ret['wetsuite_dir'] = os.path.join( home_dir, '.wetsuite' )
    else:
        ret['wetsuite_dir'] = chose_dir
    
    # TODO:     more filesystem checking, so we can give clearer errors
    if not os.path.exists( ret['wetsuite_dir'] ):
        os.makedirs( ret['wetsuite_dir'] )
    if not os.access(ret['wetsuite_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory, %r"%ret['wetsuite_dir'])

    ret['datasets_dir'] = os.path.join( ret['wetsuite_dir'], 'datasets' )
    if not os.path.exists( ret['datasets_dir'] ):
        os.makedirs( ret['datasets_dir'] )
    if not os.access(ret['datasets_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory of datasets, %r"%ret['datasets_dir'])

    ret['stores_dir'] = os.path.join( ret['wetsuite_dir'], 'stores' )
    if not os.path.exists( ret['stores_dir' ] ):
        os.makedirs( ret['stores_dir'] )
    if not os.access(ret['stores_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory of datasets, %r"%ret['stores_dir'])
    
    return ret




def unified_diff( before:str, after:str, strip_header=True, context_n=999 ) -> str:
    """ Returns an unified-diff-like indication of how two pieces of text differ, 
        as a single string and with initial header cut off, 

        Not meant for actual patching, just for quick debug printing of changes.

        context_n defaults to something high enough that it'll probably print everything
    """
    lines = list( difflib.unified_diff( before.splitlines(), after.splitlines(), fromfile='before', tofile='after', n=context_n ) )
    if strip_header:
        lines = lines[4:]
    return '\n'.join( lines )


def hash_color(string, on=None):
    ''' Give a CSS color for a string - consistently the same each time based on a hash
        Usable e.g. to make tables with categorical values more skimmable.

        To that end, this 
          takes a string, and
          returns (css_str,r,g,b), where r,g,b are 255-scale r,g,b values for a string
    '''
    dig = hash_hex( string.encode('utf8') )
    r, g, b = dig[0:3]
    if on=='dark':
        r = min(255,max(0, r/2+128 ))
        g = min(255,max(0, g/2+128 ))
        b = min(255,max(0, b/2+128 ))
    elif on=='light':
        r = min(255,max(0, r/2 ))
        g = min(255,max(0, g/2 ))
        b = min(255,max(0, b/2 ))
    r, g, b = int(r), int(g), int(b)
    css = '#%02x%02x%02x'%(r,g,b)
    return css,(r,g,b)


def hash_hex(data: bytes):
    ''' Given some byte data, calculate SHA1 hash.  Returns that hash as a hex string. 
    
        Deals with unicode by UTF8-encoding it, which isn't _always_ what you want.
    '''
    if type(data) is bytes:
        pass
    elif type(data) is str: # assume you are using this in a "I just want a consistent hash value for the same input", not necessarily according to any standard
        data = data.encode('u8')
    else:
        raise TypeError('hash_hex() only accepts byte/str data')
    s1h = hashlib.sha1()
    s1h.update( data )
    return s1h.hexdigest()



