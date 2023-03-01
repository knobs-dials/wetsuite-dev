#!/usr/bin/python3
'''
    Show mentions of "TODO:" and "CONSIDER:" in code.

'''
import os, re

# maybe use pygments to do syntax highlighting? (but may be annoying to combine)
import wetsuite.helpers.shellcolor as sc  

import TODO # for self reference
wetsuite_dir = os.path.dirname( TODO.__file__ ) # should be a little more predictable than '.;

context_lines = 3
max_bytes     = 51200

wetsuite_dir = os.path.abspath(wetsuite_dir)

lookfor_and_color = {
    'TODO:':            sc.brightyellow,
    'CONSIDER:':        sc.brightmagenta,
    'WARNING':          sc.brightred,
    'probably be moved':sc.brightblue,
}

for r, ds, fs in os.walk( wetsuite_dir ):
    for fn in fs:
        ffn = os.path.join( r, fn )
        if ffn == TODO.__file__:
            continue
        seems_like_python = False
        if ffn.endswith('.py'): # TODO: add test 
            seems_like_python = True
        else:
            if os.stat(ffn).st_size < max_bytes:
                with open(ffn, 'rb') as rf:
                    first_kb = rf.read(1024)
                    if b'/python' in first_kb or b'import ' in first_kb:
                        seems_like_python = True 
                    if len(first_kb)==0  or  first_kb.count(0x00) >= 1:
                        seems_like_python = False

        if seems_like_python:
            #print( ffn )
            with open(ffn, 'rb') as rf:
                linedata = [] # list of  (onebasedlinenum, linestr)
                for linenum, line in enumerate( rf.readlines() ):
                    line = line.decode('utf8') # doesn't need to be explicit but I was planning for a fallback
                    linedata.append( (linenum+1, line)  )
                #import pprint
                #pprint.pprint( linedata)

                matches_on_lines = []
                for line_i, line_s in linedata:
                    for restr in lookfor_and_color.keys():
                        if re.search( restr, line_s ):
                            matches_on_lines.append( line_i )
                            break
                #print( matches_on_lines)
    

                if len(matches_on_lines) > 0:
                    print( sc.brightyellow('=================  %s  ======================='%( ffn[len(wetsuite_dir):]).lstrip(os.sep)  ) ) # relative to root?

                    ## Spend some time merging ranges 
                    showlines = set() # in a lazy way

                    prev = -9
                    ll = len(linedata)
                    for ml in matches_on_lines:
                        from_line = max(0, ml-context_lines)
                        to_line   = min(ll, ml+context_lines)
                        for showline in range(from_line, to_line+1):
                            showlines.add( showline )

                    fragments, cr = [], []
                    def add_cr():
                        global cr
                        if len( cr ) > 0:
                            # take off empty first/last lines
                            while len( linedata[cr[0]][1].strip()) == 0:
                                cr.pop(0)
                            while len( linedata[cr[-1]][1].strip()) == 0:
                                cr.pop(-1)
                            fragments.append( cr )
                            cr=[]

                    for sl in sorted(showlines):
                        if sl > prev+1:
                            add_cr()
                        else:
                            cr.append( sl )
                        prev = sl
                    add_cr()


                    for fragment in fragments:
                        #print(  sc.yellow('|  ')+ sc.cyan('  -------  lines %s  -------'%( '..'.join( '%d'%v  for v in sorted( set([min(fragment), max(fragment)]) ) ) )  ) )
                        for showline in fragment:
                            line_i, line_s = linedata[ showline ]
                            line_s = line_s.rstrip('\n')

                            for restr, colorfunc in lookfor_and_color.items(): 
                                m = re.search(restr, line_s)
                                if m is not None:
                                    st, en = m.span()
                                    line_s = line_s[:st] + colorfunc(line_s[st:en]) + line_s[en:]

                            line_s = line_s.replace('TODO', sc.brightred('TODO'))
                            line_s = line_s.replace('CONSIDER', sc.brightmagenta('CONSIDER'))
                            #print( repr(line_s) ) 
                            print( sc.yellow('|% 4d| '%line_i)+ line_s )
                        print(sc.yellow('|  '))
                        #print(sc.yellow('|  '))

                    print('')
                    print('')

                