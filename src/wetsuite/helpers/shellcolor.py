'''
Eases production of colors in the terminal, for a few CLI tools.

Tries to only produce color escapes when the terminal supports it: 
whether we detect we aree in a tty, and TERM suggests we are color-capable.
You can override that in manual checks with the arguments on guess_color_support(),
You can override that in the automatic checks (necessary for the convenience function)
by setting the globals default_forceifnoterm and/or default_forceifnotty)


Currently provides some convenience functions for a single foreground color, meant to be used like: ::
    import helpers_shellcolor as sc
    print sc.red('shown as red')
    Without the check and for more control:
    print sc.BRIGHT+sc.BLUE+sc.UNDERLINE+'shown bright blue'+sc.RESET

Tries to only add the control codes when the context seems capable of it.
(TODO: this needs some tuning)
check whether we are in a tty, and whether the TERM suggests we are color-capable.
You can override that in manual checks with the arguments on guess_color_support(),
You can override that in the automatic checks (necessary for the convenience function)
by setting the globals default_forceifnoterm and/or default_forceifnotty


TODO:
consider writing a percent formatter that is aware of the zero width of these escapes,
so that you can put strings in things like %20s without magic weirdness.

rename to, perhaps, helpers_terminal.py ?

see whether tput colors is useful (e.g. detecting more colors)
'''
#def format(s, *args):

import os
import sys
import re
import math



default_forceifnoterm = None
default_forceifnotty  = None


def guess_color_support(forceifnottty=False, forceifnoterm=False, fallback=True): # pragma: no cover     because it's necessarily context-dependent
    ''' Tries to guess whether we can use color code output.

        If we are not on a tty/pty (usually a pipe), return False
        If the TERM mentions we can, returns True, if it mensions we cannot, return False
        If we do not know, return the fallback (by default is True)        
    
        TODO: fix the logic for this, it does not do exactly what was intended.

        User code should probably always prefer supported(),
        and only use guess_color_support if it wants a different test or fallback later.
    '''
    global _guess
    
    if not default_forceifnoterm  and  not forceifnoterm:
        if 'TERM' not in os.environ:
            #print( "probably not a shell" )
            _guess = False
            return _guess

    if not default_forceifnotty   and  not forceifnottty:
        if not sys.stdout.isatty():
            #print( "Not a TTY, probably a pipe" )
            
            # Assumes that this means it's a less pipe,
            #         that setting LESS=R means you want it in all pipes,
            #         that you have set LESS=R only in the shells where that makes sense
            # TODO: fewer assumptions 
            #_guess = False
            #if 'LESS' in os.environ:
            #    if 'R' in os.environ['LESS']:
            #        #print( "Rawness in LESS env setting")
            #        _guess = True
            return _guess
        
    if 'TERM' in os.environ:
        try:
            import subprocess
            p=subprocess.Popen(['tput', 'colors'], stdout=subprocess.PIPE, shell=False)
            out,_=p.communicate()

            if out.strip()=='':
                return False
            elif int(out.strip())>2:
                _guess = True
                return _guess
            else:
                _guess = False
                return _guess
        except:
            raise
        
            TERM = os.environ['TERM']
            if TERM.endswith('-m') or '-m-' in TERM or 'nocolor' in TERM:
                _guess = False
                return _guess
            if TERM.endswith('-c') or '-c-' in TERM or 'color' in TERM:
                _guess = True
                return _guess
            # maybe test for -ansi ?        
            if 'rxvt' in TERM or 'putty' in TERM: # or 'linux' in TERM?
                _guess = True
                return _guess

    _guess = fallback
    return _guess

def supported():
    global _guess
    _guess = None
    if _guess == None:
        guess_color_support()
    return _guess

# we assume our answer will not change within a shell, so our first guess stays true
_guess = supported()
#_guess = None # none before detection,  True if we guessed yes,  False if we guessed no.




    
# Try to get column width (*nix-mostly)
def tty_size(debug=False):                   # pragma: no cover     because it's necessarily context-dependent
    """ fetches current terminal size

        Has a few methods under *nix, probably largely redundant.
        Under windows there is only one, and counts on ctypes

        returns a dict with keys 'cols' and 'rows'.
        Values are None when we cannot determine them. You probably want fallback logic around this
    """
    ret = { 'cols':None, 'rows':None }

    if not sys.stdin.isatty(): # if we don't have a terminal (e.g. running in a service), don't try to run things that will only fail ioctls
        # There may be better ways to detect this.
        return ret    

    
    try: # ioctl (*nix only)
        import fcntl, termios, struct
        fd=1
        hw = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        ret['cols'] = hw[1]
        ret['rows'] = hw[0]
    except:
        if debug:
            raise
    if ret['rows'] not in (0,None) and ret['cols'] not in (0,None):
        return ret
    
                                                        
    try: # stty (*nix only)        
        import subprocess
        p = subprocess.Popen('stty size', stdout=subprocess.PIPE, shell=True)
        out,_ = p.communicate()
        out.strip()
        out = out.split()
        ret['rows'] = int( out[0], 10 )
        ret['cols'] = int( out[1], 10 )    
    except:
        if debug:
            raise
    if ret['rows'] not in (0,None) and ret['cols'] not in (0,None):
        return ret

    
    try: # tput (*nix only)
        import subprocess
        p = subprocess.Popen('tput cols', stdout=subprocess.PIPE, shell=True)
        out,_ = p.communicate()
        ret['cols'] = int(out.strip(),10)
        p = subprocess.Popen('tput lines', stdout=subprocess.PIPE, shell=True)
        out,_ = p.communicate()
        ret['rows'] = int(out.strip(),10)
    except:
        if debug:
            raise
    if ret['rows'] not in (0,None) and ret['cols'] not in (0,None):
        return ret

    
    try: # piggyback on curses (*nix only, really...)
        import curses
        stdscr = curses.initscr()
        curses.initscr()
        curses.cbreak()
        curses.noecho()
        stdscr.keypad(1)
        try:
            height,width = stdscr.getmaxyx()
            ret['rows'] = height
            ret['cols'] = width
        finally:
            curses.nocbreak()
            stdscr.keypad(0)
            curses.echo()
            curses.endwin()                                                                
    except:
        if debug:
            raise
    if ret['rows'] not in (0,None) and ret['cols'] not in (0,None):
        return ret

    try:
        # from http://code.activestate.com/recipes/440694-determine-size-of-console-window-on-windows/
        from ctypes import windll, create_string_buffer
        # stdin, stdout, stderr handles are -10, -11, -12
        h    = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res  = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            import struct
            bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy = struct.unpack("hhhhHhhhhhh", csbi.raw)
            ret['cols'] = right - left + 1
            ret['rows'] = bottom - top + 1
    except:
        if debug:
            raise
    if ret['rows'] not in (0,None) and ret['cols'] not in (0,None):
        return ret

    # Last because this won't change on resize (most others will)
    #shutil.get_terminal_size  (py3 only) seems to just do the following
    try:
        if 'LINES' in os.environ and 'COLUMNS' in os.environ:
            ret['rows'] = os.environ['LINES']
            ret['cols'] = os.environ['COLUMNS']
    except:
        if debug:
            raise
    if ret['rows'] not in (0,None) and ret['cols'] not in (0,None):
        return ret
                        
    return ret



# Keep in mind that 'bright' is a state that stays enabled, you'ld need a NOCOLOR (or RESET) to no non-bright.
BRIGHT         = '\x1b[1m'
NOCOLOR        = '\x1b[0m'
UNDERLINE      = '\x1b[4m'
#
BLACK          = '\x1b[30m'
BRIGHTBLACK    = '\x1b[1;30m'
RED            = '\x1b[31m'
BRIGHTRED      = '\x1b[1;31m'
GREEN          = '\x1b[32m'
BRIGHTGREEN    = '\x1b[1;32m'
YELLOW         = '\x1b[33m'
ORANGE         = YELLOW
BRIGHTYELLOW   = '\x1b[1;33m'
BLUE           = '\x1b[34m'
BRIGHTBLUE     = '\x1b[1;34m'
MAGENTA        = '\x1b[35m'
BRIGHTMAGENTA  = '\x1b[1;35m'
CYAN           = '\x1b[36m'
BRIGHTCYAN     = '\x1b[1;36m'
GREY           = '\x1b[37m'
GRAY            = GREY
BRIGHTGREY     = '\x1b[1;37m'
BRIGHTGRAY     = BRIGHTGREY
WHITE          = BRIGHTGREY
DEFAULT        = '\x1b[39m'

# TODO: consider them garish background colors
BGBLACK        = '\x1b[40m'
BGRED          = '\x1b[41m'
BGGREEN        = '\x1b[42m'
BGBLUE         = '\x1b[44m'
BGYELLOW       = '\x1b[43m'
BGORANGE       = BGYELLOW
BGMAGENTA      = '\x1b[45m'
BGCYAN         = '\x1b[46m'
#BGWHITE        = '\x1b[47m'
BGBRIGHTGRAY   = '\x1b[1;47m'
BGWHITE        = BGBRIGHTGRAY

# functional stuff
ERASEDISP    = '\x1b[2J' # erase all
#ERASEBEFORE  = '\x1b[1J' # erase from cursor up
#ERASEAFTER   = '\x1b[J'  # erase from cursor down
GOTO00       = '\x1b[;H'
CLEARSCREEN  = ERASEDISP + GOTO00
ERASELINE    = '\x1b[2K'
#ERASELINEBEFORE= '\x1b[1K'
#ERASELINEAFTER = '\x1b[K'

RESET        = NOCOLOR + DEFAULT







# ease-of-use globals
def brightblack(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTBLACK,prepend=prepend)
def darkgray(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTBLACK,prepend=prepend)
def darkgrey(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTBLACK,prepend=prepend)
def black(s, prepend=''):
    return _add_color_if_supported(s,BLACK,prepend=prepend)
def red(s, prepend=''):
    return _add_color_if_supported(s,RED,prepend=prepend)
def brightred(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTRED,prepend=prepend)
def green(s, prepend=''):
    return _add_color_if_supported(s,GREEN,prepend=prepend)
def brightgreen(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTGREEN,prepend=prepend)
def orange(s, prepend=''):
    return _add_color_if_supported(s,ORANGE,prepend=prepend)
def yellow(s, prepend=''):
    return _add_color_if_supported(s,YELLOW,prepend=prepend)
def brightyellow(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTYELLOW,prepend=prepend)
def blue(s, prepend=''):
    return _add_color_if_supported(s,BLUE,prepend=prepend)
def brightblue(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTBLUE,prepend=prepend)
def magenta(s, prepend=''):
    return _add_color_if_supported(s,MAGENTA,prepend=prepend)
def brightmagenta(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTMAGENTA,prepend=prepend)
def cyan(s, prepend=''):
    return _add_color_if_supported(s,CYAN,prepend=prepend)
def brightcyan(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTCYAN,prepend=prepend)
def gray(s, prepend=''):
    return _add_color_if_supported(s,GREY,prepend=prepend)
def grey(s, prepend=''):
    return _add_color_if_supported(s,GREY,prepend=prepend)
def brightgrey(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTGREY,prepend=prepend)
def brightgray(s, prepend=''):
    return _add_color_if_supported(s,BRIGHTGRAY,prepend=prepend)
def white(s, prepend=''):
    return _add_color_if_supported(s,WHITE,prepend=prepend)

def bgblack(s, prepend=''):
    return _add_color_if_supported(s,BGBLACK,prepend=prepend)
def bgred(s, prepend=''):
    return _add_color_if_supported(s,BGRED,prepend=prepend)
def bggreen(s, prepend=''):
    return _add_color_if_supported(s,BGGREEN,prepend=prepend)
def bgblue(s, prepend=''):
    return _add_color_if_supported(s,BGBLUE,prepend=prepend)
def bgyellow(s, prepend=''):
    return _add_color_if_supported(s,BGYELLOW,prepend=prepend)
def bgorange(s, prepend=''):
    return _add_color_if_supported(s,BGORANGE,prepend=prepend)
def bgmagenta(s, prepend=''):
    return _add_color_if_supported(s,BGMAGENTA,prepend=prepend)
def bgcyan(s, prepend=''):
    return _add_color_if_supported(s,BGCYAN,prepend=prepend)

def default(s, prepend=''):
    return _add_color_if_supported(s,DEFAULT,prepend=prepend)
def reset():                       
    return _add_color_if_supported('',RESET)
def clearscreen():
    if _guess:
        return CLEARSCREEN




# playing around with styles, not sure which is more convenient in the end


# match percent formatting:
pre = re.compile(r'((%)([+\ -]+)?([0-9]*)([.][0-9]*)?([%csdiuxXoeEfFgGpr]))')
# match some escapes (needs work!)
ere = re.compile(r'\x1b[^ABCDEFGHJKSTfmnsulnh]*[ABCDEFGHJKSTfmnsulnh]')


def _strip_escapes_if_not_supported(s, forceaway=False):
    if _guess and not forceaway:
        return s
    else:
        return ere.sub('',s)

def _add_color_if_supported(s, colcode, prepend=''):
    if _guess:
        return prepend+colcode+s+RESET
    else:
        return s



### Experimenting with escape-aware functions. TODO: clean up and document.

def real_len(s):
    ''' Returns 2-tuple:
        - amount of printed characters,
        - amount spent in control codes  (which is calculated as the byte length minus the first part)
    '''
    ret=0
    en=True
    s = str(s) # in case it's not a string
    for c in s:
        if c=='\x1b':
            en=False
            continue
        if not en:
            if c in 'mHJ':
                en=True
                continue
        if en:
            ret+=1
    return ret,len(s)-ret



def closest_from_rgb255(r,g,b, mid=170,full=255, nobright=False):
    ''' Given a r,g,b color (0..255 scale), pick the closest shell color (returns the function)

        The brightness that color is rendered as depends on the terminal,
        see e.g. https://en.wikipedia.org/wiki/ANSI_escape_code#3.2F4_bit

        To get some semblance of control, you can control the brightness the non-bright color is assumed to have. 
        (hint: you can cheat your way to less of the garish bright colors by upping mid, or more by lowering it)

        You can completely avoid the bright colors by specifying nobright=True
    '''
    colors=(
        ('red',         mid,0,0,    red),
        ('green',       0,mid,0,    green),
        ('blue',        0,0,mid,    blue),

        ('cyan',        0,mid,mid,    cyan),
        ('yellow',      mid,mid,0,    yellow),
        ('magenta',     mid,0,mid,    magenta),

        ('bright red',         full,0,0,    brightred),
        ('bright green',       0,full,0,    brightgreen),
        ('bright blue',        0,0,full,    brightblue),
        ('bright cyan',        0,full,full,    brightcyan),
        ('bright yellow',      full,full,0,    brightyellow),
        ('bright magenta',     full,0,full,    brightmagenta),

        ('grey',  mid,mid,mid,            grey),
        ('bright white', full,full,full,  brightgrey),
        ('black', 0,0,0,                  black),
    )
    mindist   = 999
    min_index = None
    for i, (name, mr,mg,mb, func) in enumerate(colors):
        if nobright and name.startswith('bright'):
            continue
        dist = math.sqrt( (r-mr)**2 + (g-mg)**2 + (b-mb)**2 )
        if dist < mindist:
            mindist = dist
            min_index = i
    return colors[min_index][-1]


def _format_segment(s):
    """ Helper for cformat()  (NOW REDUNDANT?)
        e.g. '  \x1b[33mfork\x1b[0m\x1b[39m'   ->   ['  ', '\x1b[33m', 'fork', '\x1b[0m', '\x1b[39m']
        The numbers are the bytestring length and the print length
    """
    bslen, esclen = len(s), 0
    ret=[]
    while True:
        if len(s) == 0: # we're done
            break
        esc = s.find('\x1b')
        if esc == -1:   # we're done
            ret.append(s)
            break
        else:
            if esc > 0:
                ret.append( s[:esc] )
            end = s.find('m',esc+1)
            esclen+=(end-esc+1)
            ret.append( s[esc:end+1] )
            s=s[end+1:]
    return ret, bslen, bslen-esclen



def _percent_parse(s, add=[]):
    """ Will rewrite any format strings with a width to have more width by the amount specified.
        The add array must have as many items as there are format strings.
        
        TODO: deal with %r sensibly?
    """
    ret=[]
    # Rewrite any percent
    addi=0
    while True:
        if len(s)==0:
            break
        ip = s.find('%')
        if ip == -1:
            ret.append( s )
            break
        if ip>0:
            ret.append( s[:ip] )
            s=s[ip:]
        m  = pre.match( s )
        ml = m.groups()

        addnow=0
        if addi>=len(add):
            raise ValueError('Not enough values to add')
        else:
            addnow=add[addi]

        rps = ['%']
        if ml[2] is not None:
            rps.append( ml[2] )
        if ml[3] not in (None,''):
            rps.append( str( int(ml[3])+addnow ) )   
        if ml[4] is not None:
            rps.append( ml[4] )
        rps.append( ml[5] )
        ret.append( ''.join(rps) )

        s = s[ len(ml[0]): ]
        addi+=1

    return ''.join(ret)




def truncate_real_len(s,len, append=RESET):
    ''' Truncate a string after so-many real characters.
        Written for "truncate colored text according to the terminal width" functionality.

        @param append: By default, it appends a reset to default colors,
        so that it doesn't leave things as the last-used color.
        To avoid that, say append=''
    '''
    ret = 0
    en=True
    realchars = 0
    for i,c in enumerate(s):
        if c=='\x1b':
            en=False
            continue
        if not en:
            if c in 'mHJ':
                en=True
                continue
        if en:
            realchars += 1
            if realchars > len:
                ret=i
                #print( "Truncating at bytestrpos %d, realcharlen %d"%(i,realchars) )
                break
    ret = s[:ret] #mwehehe
    ret += append
    return ret


def cformat(fs, seq, fsinstead=False):
    """ EXPERIMENT:
        A percent formatter that is aware that color escapes have zero display width,
        so you can feed it strings with color escapes and avoid some magic reindenting weirdness.
        
        cformat(arg1,arg2) acts like arg1%arg2

        e.g. cformat('%20s', (WHITE+'fork'+RESET,) ) == '                \x1b[1;37mfork\x1b[0m\x1b[39m'
        instead of  '\x1b[1;37mfork\x1b[0m\x1b[39m'

        Assumption is that escapes have zero width, which is true for colors but not for weirder things.
    """
    if type(seq) not in (tuple,list): # assumes that means it's a bare string
        seq=tuple([seq])

    add=[]
    for part in seq:
        prlen, cclen = real_len(part)
        add.append(cclen)

    newfs = _percent_parse(fs, add)
    #print 'fs    ',fs
    #print 'add   ',add
    #print 'newfs ',newfs
    if fsinstead:
        return newfs
    else:
        return newfs%seq
     


def color_degree(s, v, fromv=0, tov=0, colors=[BRIGHTBLACK, GRAY, WHITE, YELLOW, RED]):
    # hacky
    v = float(v)
    tov = float(tov)
    #fromvv = float(fromv)
    vrange = tov-fromv

    tov -= 1./(len(colors)-1)

    frac = (v-fromv)/(vrange)

    frac *= float(len(colors)+1) / float(len(colors)) # make the last color play too. hackish.
    colori = int(frac*(len(colors)-1))
    colori=max(0,min(colori,len(colors)-1))
    return _add_color_if_supported(s,colors[colori])


def true_colf(s, r,g,b):
    ' true-color escape from 0..255 r,g,b '
    r = min(255,max(0, int(r) ))
    g = min(255,max(0, int(g) ))
    b = min(255,max(0, int(b) ))
    RGBCOL = '\x1b[38;2;%s;%s;%sm'%(r,g,b)
    return _add_color_if_supported(s,RGBCOL)


def redgreen(s, frac):
    ' turns a fraction in 0..1 to red..green '
    r = min(255,max(0, int( (255-(255*frac)) ) ))
    g = min(255,max(0, int( (255*frac)) ))
    b = 0
    RGBCOL = '\x1b[38;2;%s;%s;%sm'%(r,g,b)
    return _add_color_if_supported(s,RGBCOL)


def blend(s, frac, rgb1, rgb2):
    r = int(  min(255,max(0,  255*( (1-frac)*rgb1[0] + frac*rgb2[0] ) ))  )
    g = int(  min(255,max(0,  255*( (1-frac)*rgb1[1] + frac*rgb2[1] ) ))  )
    b = int(  min(255,max(0,  255*( (1-frac)*rgb1[2] + frac*rgb2[2] ) ))  )
    #print(r,g,b)
    RGBCOL = '\x1b[38;2;%s;%s;%sm'%(r,g,b)
    return _add_color_if_supported(s,RGBCOL)


def hash_color(s, rgb=False, append=RESET, prepend='', hash_instead=None, on=None):
    ''' return string wrapped in a (non-black basic shell) color (and RESET after) based on the string

        If you want to color an entire string based on just a part of it, hand the part into hash_instead
     
        If rgb==False, uses the basic set of ~8 colors and brightness.
        If rgb==True,  uses true color  (recommended if you can)

        if on == 'dark' suggests we're drawing on dark background, so stays away from very dark rgb values
        if on == 'light', we stay away from very light rgb values
        by default we don't care, which might be good for area fills

        TODO: variant that gives just the escapes, so we can avoid calling this a lot
    '''
    import hashlib
    m = hashlib.sha256()
    if hash_instead:
        m.update(hash_instead.encode('utf8'))
    else:
        m.update(s.encode('utf8'))
    dig = m.digest()
    
    if type(dig[0]) is not int: # quick and dirty way of dealing with py2/3 difference
        dig = list( ord(ch)  for ch in dig)
    
    if rgb:
        if on=='dark':
            r = min(255, max(0, 40+0.8*dig[0]))
            g = min(255, max(0, 40+0.8*dig[1]))
            b = min(255, max(0, 40+0.8*dig[2]))
        elif on=='light':
            r = min(255, max(0, 0.8*dig[0]))
            g = min(255, max(0, 0.8*dig[1]))
            b = min(255, max(0, 0.8*dig[2]))
        else:
            r = dig[0]
            g = dig[1]
            b = dig[2]
            
        return prepend+true_colf(s, r,g,b)
    else:
        choosefrom = [ BRIGHTBLACK,RED, BRIGHTRED, GREEN, BRIGHTGREEN,
                       YELLOW, BRIGHTYELLOW, BLUE, BRIGHTBLUE, MAGENTA,
                       BRIGHTMAGENTA, CYAN, BRIGHTCYAN, GREY, WHITE     ]
        choice = choosefrom[ sum(ch for ch in dig)%len(choosefrom) ]
        return prepend+'%s%s%s'%(choice,s,append)

