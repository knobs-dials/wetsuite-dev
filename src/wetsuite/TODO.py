#!/usr/bin/python3
''' Show mentions of "TODO:" and "CONSIDER:" in code.
'''
import os, re, json, sys

# maybe use pygments to do syntax highlighting? (but may be annoying to combine)
import wetsuite.helpers.shellcolor as sc

#import TODO # for self reference
#wetsuite_dir = os.path.dirname( TODO.__file__ ) # should be a little more predictable than '.;


LOOKFOR_AND_COLOR = {
    'TODO:':            sc.brightyellow,
    'FIXME:':           sc.brightcyan,
    'CONSIDER:':        sc.brightmagenta,
    'WARNING':          sc.brightred,
    'probably be moved':sc.brightblue,
}


### TODO: proper argument parsing

show_context_line_amt = 3
# large py-like files are usually data, not code
max_filesize     = 512000
max_cellsize     = 51200

args = sys.argv[1:]

if len(args)==0:
    print("We need paths to work on.   Did you mean:\n %s ."%os.path.basename(sys.argv[0]))

for arg in args:
    arg = os.path.abspath( arg )

    for r, ds, fs in os.walk( arg ):
        # not sure why it's misdetecting that as a constant; pylint: disable=C0103
        for fn in fs:
            ffn = os.path.join( r, fn )
            #if ffn == TODO.__file__:
            #    continue
            seems_like_notebook, seems_like_python = False, False
            if ffn.endswith('.ipynb'):
                seems_like_notebook = True
            elif ffn.endswith('.py'): # TODO: add test
                seems_like_python = True
            else: # read first kilobyte, see if it contains python-like things
                if os.stat(ffn).st_size > max_filesize:
                    pass
                    #print('SKIP, larger than %d bytes: %r'%(max_filesize, ffn))
                else:
                    with open(ffn, 'rb') as rf:
                        first_kb = rf.read(1024)
                        # TODO: better tests for 'does this look like python source?'
                        if b'/python' in first_kb or b'import ' in first_kb:
                            seems_like_python = True
                        if len(first_kb)==0  or  first_kb.count(0x00) >= 1:
                            seems_like_python = False

            ddata = [] # list of  (extramention, onebasedlinenum, linestr)

            if seems_like_notebook:
                with open(ffn, 'rb') as rf:
                    d = json.loads( rf.read() )
                    for cell_number, cell in enumerate(d['cells']):
                        cell_type = cell.get('cell_type')
                        if cell_type == 'markdown':
                            pass
                        elif cell_type == 'code':
                            lines = cell.get('source')
                            line_bytes = sum( len(line)  for line in lines )
                            if line_bytes > max_cellsize:
                                pass
                                #print( 'SKIP cell %s, larger than %d bytes: %r'%(cell_number+1) )
                            else:
                                for linenum, line in enumerate(  ):
                                    # note: line numbering is 0-based internally, +1 whenever we put it in a string to print
                                    ddata.append( ('(cell %s)'%(cell_number+1), linenum, line)  )
                        else:
                            raise ValueError("Don't recognize cell_type=%r"%cell_type)

            elif seems_like_python:
                with open(ffn, 'rb') as rf:
                    for linenum, line in enumerate( rf.readlines() ):
                        line = line.decode('utf8') # doesn't need to be explicit but I was planning for a fallback
                        ddata.append( ('', linenum, line)  ) # note: line logic is 0-based, and we print it +1

            else:
                continue

            # Linedata for ipynb is in cells, split that if necess

            sections = sorted( set( extra  for extra,_,_ in ddata ) )

            for section in sections:

                linedata = list( (linenum,line)   for extra, linenum, line in ddata    if extra==section  )





                ### Take linedata, match in it
                matches_on_lines = []
                for line_i, line_s in linedata:
                    for restr in LOOKFOR_AND_COLOR.keys():
                        if re.search( restr, line_s ):
                            matches_on_lines.append( line_i )
                            break

                if len(matches_on_lines) > 0:
                    print( sc.brightyellow('=================  %s  %s ======================='%(
                        ffn[len(arg):].lstrip(os.sep),
                        section
                    )  ) )

                    # merge and separate line ranges.

                    # first add all line numbers to one big set (note: 1-based)
                    showlines = set()
                    prev = -9
                    ll = len(linedata)
                    for ml in matches_on_lines:
                        from_line = max(0, ml-show_context_line_amt)
                        to_line   = min(ll-1, ml+show_context_line_amt)
                        for showline in range(from_line, to_line+1):
                            showlines.add( showline )

                    # now we want to make a list of ranges,
                    fragments = [] # like  [ [1,2], [7,8,9,10], ]

                    # this bit's less readable
                    cur_range = []
                    def add_cr():
                        global cur_range
                        if len( cur_range ) > 0:
                            # take off empty first and empty last lines. Written out longer than it needs to be for debug reasons.
                            while len(cur_range) > 0:
                                _, first_line = linedata[ cur_range[0] ]
                                if len(first_line.strip())==0:
                                    cur_range.pop(0)
                                else:
                                    break
                            while len(cur_range) > 0:
                                _, last_line = linedata[ cur_range[-1] ]
                                if len(last_line.strip())==0:
                                    cur_range.pop(-1)
                                else:
                                    break
                            fragments.append( cur_range )
                            cur_range=[]

                    for sl in sorted(showlines):
                        if sl > prev+1: # gap?
                            add_cr()
                        else:
                            cur_range.append( sl )
                        prev = sl
                    add_cr()


                    for fragment in fragments:
                        for showline in fragment:
                            line_i0, line_s = linedata[ showline ]
                            line_s = line_s.rstrip('\n')

                            for restr, colorfunc in LOOKFOR_AND_COLOR.items():
                                m = re.search(restr, line_s)
                                if m is not None:
                                    st, en = m.span()
                                    line_s = line_s[:st] + colorfunc(line_s[st:en]) + line_s[en:]

                            line_s = line_s.replace('TODO', sc.brightred('TODO'))
                            line_s = line_s.replace('CONSIDER', sc.brightmagenta('CONSIDER'))
                            print( sc.yellow('|% 4d| '%(line_i0+1))+ line_s )
                        print(sc.yellow('|  '))

                    print('')
                    print('')
