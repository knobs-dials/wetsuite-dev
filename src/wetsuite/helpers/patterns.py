'''
    This module contains various pattern extractions.

    It exists in part to point out that while probably useful,
      they deal with things that aren't formalized via EBNF or whatnot,
      so are probably best-effort, and contain copious hardcoding and messines.
    
    So They may miss things.

    Ideally, each function further notes how much can and can't expect from it.


    Contributions are welcome, though in the interest of not immediately making a mess,
    we may want contributions to go to a contrib/ at least at first     
'''
import re, collections
import wetsuite.helpers.strings
from wetsuite.helpers.strings import interpret_ordinal_nl
import wetsuite.helpers.meta



def find_identifier_references( text , ljn=False, ecli=True, celex=True, kamerstukken=True, vindplaatsen=True, nonidentifier=True, euoj=True, eudir=True):
    '''
        There is a good argument to make this more pluggable, rather than one tangle of a function.
    '''
    ret = []
    
    #LJN
    if ljn:
        for rematch in re.finditer( r'\b[A-Z][A-Z][0-9][0-9][0-9][0-9](,[\n\s]+[0-9]+)?\b', text, flags=re.M ):
            match = {}
            match['type']  = 'ljn'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            ret.append( match )
        
    if ecli:
        for rematch in wetsuite.helpers.meta._eclifind_re.finditer( text ):
            match = {}
            match['type']    = 'ecli'
            match['start']   = rematch.start()
            match['end']     = rematch.end()
            match['text']    = rematch.group( 0 )
            match['details'] = wetsuite.helpers.meta.parse_ecli( rematch.group(0) )
            
            ret.append( match )


    if vindplaatsen:
        # https://www.kcbr.nl/beleid-en-regelgeving-ontwikkelen/aanwijzingen-voor-de-regelgeving/hoofdstuk-3-aspecten-van-vormgeving/ss-33-aanhaling-en-verwijzing/aanwijzing-345-vermelding-vindplaatsen-staatsblad-ed
        for rematch in re.finditer( r'\b((Trb|Stb|Stcrt)[.]?[\n\s]+[0-9\u2026.]+(,[\n\s]+[0-9\u2026.]+)?)', text, flags=re.M ):
            match = {}
            match['type']  = 'vindplaats'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            ret.append( match )

    if kamerstukken:
        print(1)
        # I'm not sure about the standard here, and the things I've found seem frequently violated
        for rematch in re.finditer( 
            r'(Kamerstukken|Aanhangsel Handelingen|Handelingen)( I| II)? ([0-9]+/[0-9]+)(@, [0-9]+( [XVI]+)?|@, item [0-9]|@, nr. [0-9]+|@, p. [0-9-]+|@, [A-Z]+)*'
                .replace(' ',r'[\n\s]+') 
                .replace('@',r'[\n\s]*')
            , text , flags=re.M):
            match = {}
            match['type']  = 'kamerstukken'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            ret.append( match )


    if celex:
        for rematch in wetsuite.helpers.meta._re_celex.finditer( text ):
            match = {}
            match['type']  = 'celex'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            match['details'] = wetsuite.helpers.meta.parse_celex( rematch.group(0) )
            ret.append( match )

    _euoj_re = re.compile(r'(OJ|Official Journal)[\s]?(C|CA|CI|CE|L|LI|LA|LM|A|P) [0-9]+([\s]?[A-Z]|/[0-9])*(, p. [0-9](\s*[\u2013-]\s*[0-9]+)*|, [0-9]{1,2}[./][0-9]{1,2}[./][0-9][0-9]{2,4})'.replace(' ','[\s\n]+'),
                          flags=re.M)

    if euoj:
        for rematch in _euoj_re.finditer( text ):
            match = {}
            match['type']  = 'euoj'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            ret.append( match )

    _eudir_re = re.compile(r'(Directive) [0-9]{2,4}/[0-9]+(/EC|EEC|EU)?'.replace(' ',r'[\s\n]+'),
                          flags=re.M)

    if eudir:
        for rematch in _eudir_re.finditer( text ):
            match = {}
            match['type']  = 'eudir'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            ret.append( match )

    if nonidentifier:
        for match in find_nonidentifier_references( text ):
            match['type'] = 'nonidentifier' # not the best name
            match['details'] = list( match['details'].items() )
            ret.append( match )

    ret.sort(key=lambda m: m['start'])

    return ret
    



def find_nonidentifier_references(text, context_amt=60, debug=False): # TODO: needs a better name
    ''' Attempts to find references like
          "artikel 5.1, tweede lid, aanhef en onder i, van de Woo"
        and parse and resolve as much as it can.
           
        Returns a list of (matched_text, parsed_details_dict)


        This is not a formalized format, and while law ( https://wetten.overheid.nl/BWBR0005730/ )
        suggests the format of these suggests succinctness and has near-templates, 
        that is not what real-world use looks like.

        You can argue for include each real-world variant explicitly, 
        as it lets you put stronger patterns first and fall back on fuzzier,
        it makes it clear what is being matched, and it's easier to see how common each is.
        However, it easily leads to false negatives.

        In fact, for the briefest forms ("81 WWB") you may only be certain if you
        recognize either side (by known law name, or fragments that 
        ...though we should not accept that example unless context makes it clearer (e.g. parentheses help) 
        that this is a reference, rather than just some characters that happen to be next to each other)


        Instead, we start by finding some strong anchors
        (currently 'artikel' as this ,

        and keep accepting bits of string as long as they look like things we know
        # # "artikel 5.1,"   "tweede lid,"   "aanhef en onder i"

        then seeing what text is around it
        because around it should appear at least the law name,
        and proably lid, and more

        This should let the same function find complete ones,
        and report incomplete or hard to resolve ones.
    '''
    ret = []
    artikel_matches = []


    for artikel_mo in re.finditer(r'\b(?:[Aa]rt(?:ikel|[.]|\b)\s*([0-9.:]+[a-z]*))', text):
        artikel_matches.append( artikel_mo )

    # note to self: just the article bit also good for creating an anchor for test cases later, to see what we miss and roughly why

    for artikel_mo in artikel_matches: # these should be unique references
        details = collections.OrderedDict()
        details['artikel'] = artikel_mo.group(1)
        #if debug:
        #    print('------')
        #    print(artikel_mo)

        overallmatch_st, overallmatch_en = artikel_mo.span()

        # based on that anchoring match, define a range to search in
        wider_start = max(0,      overallmatch_st - context_amt)
        wider_end   = min(overallmatch_st + context_amt, len(text))

        # Look for some specific strings around the matched 'artikel', (and record whether they came before or after)
        find_things = { # match before and/or after,   include or exclude,    (uncompiled) regexp

            # these are not used yet, but are meant to set hard borders when seen before/after the anchor match
            'grond':           [ 'B', 'E',  r'\bgrond(?: van)?\b'                                               ],
            'bedoeld':         [ 'B', 'E',  r'\bbedoeld in\b'                                                   ],

            #'komma':          [  '.',  re.compile(r',')                                                        ],

            'hoofdstuk':       [ 'A', 'I',  r'\bhoofdstuk#\b'                                                   ],
            'paragraaf':       [ 'A', 'I',  r'\bparagraaf#\b'                                                   ],
            'aanwijzing':      [ 'A', 'I',  r'\b(?:aanwijzing|aanwijzingen)#\b'                                 ],

            'onderdeel':       [ 'A', 'I',  r'\b(?:onderdeel|onderdelen)\b'                                     ],
            'lid':             [ 'A', 'I',  r'\b(?:lid_(#)|(L)_(?:lid|leden))'                         ],
            'aanhefonder':     [ 'A', 'I',  r'\b((?:\baanhef_en_)?onder_[a-z]+)'                                ], # "en onder d en g"
            'sub':             [ 'A', 'I',  r'\bsub [a-z]\b'                                                    ],

            #'vandh':          [  'E',  r'\bvan (?:het|de)\b'                                                   ],
            ##'dezewet':       [  'I',  r'\bde(?:ze)? wet\b'                                                    ],

            #'hierna':          [ 'A', 'E',  r'\b[(]?hierna[:\s]'                                                    ],
            #'kan':            [ '' re.compile(r'\bkan\b'],
        }

        #re_some_ordinals = '(?:%s)'%( '|'.join( wetsuite.helpers.strings.ordinal_nl_20 ) )
        re_some_ordinals = '(?:%s)'%( '|'.join( wetsuite.helpers.strings.ordinal_nl(i) for i in range(100) ) )

        for k in find_things:
            # make all the above multiline matchers, and treat specific characters as signifiers we should be replacing
            #   the 'replace this character' is cheating somewhat because and can lead to incorrect nesting, 
            #   so take care, but it seems worth it for some more readability
            _,_,res = find_things[k]
            res = res.replace('_',r'[\s\n]+')
            res = res.replace('#',r'([0-9.:]+[a-z]*)')

            if 'L' in res:
                #print('BEF',res)
                rrr = r'(?:O(?:,?_O)*(?:,?_en_O)?)'.replace( '_',r'[\s\n]+' ).replace('O', re_some_ordinals)
                res = res.replace('L', rrr)
                #print('AFT',res)

            compiled = re.compile(  res,  flags=re.I|re.M  )  
            find_things[k][2] = compiled

        ## the main "keep adding things" loop
        range_was_widened = True
        while range_was_widened:
            range_was_widened = False

            if debug:
                import textwrap
                s_art_context = '%s[%s]%s'%( text[wider_start:overallmatch_st], text[overallmatch_st:overallmatch_en].upper(), text[overallmatch_en:wider_end] )
                print( 'SOFAR',  '\n'.join( textwrap.wrap(s_art_context.strip(), width=70, initial_indent='     ', subsequent_indent='     ') ) )

            for rng_st, rng_en, where in (    (wider_start, overallmatch_st, 'before'),    (overallmatch_en, wider_end,   'after'),    ):
                for find_name, (before_andor_after, incl_excl, find_re) in find_things.items():
                    #print('looking for %s %s current match (so around %s..%s)'%(find_re, where, rng_st, rng_en))
                    if 'A' not in before_andor_after and where=='after':
                        continue
                    if 'B' not in before_andor_after and where=='before':
                        continue

                    # TODO: ideally, we use the closest match; right now we assume there will be only one in range (TODO: fix that)
                    for now_mo in find_re.finditer(text, pos=rng_st, endpos=rng_en): # TODO: check whether inclusive or exclusive
                        #now_size = now_mo.end() - now_mo.start()

                        if incl_excl == 'E': # recognizing a string that we want _not_ to include (not all that different from just not seeing something
                            #print( 'NMATCH', find_name )
                            pass
                        elif incl_excl == 'I': 
                            nng = list(s  for s in now_mo.groups()   if s is not None)
                            if len(nng) > 0:
                                details[find_name] = nng[0]
                            if now_mo.end() <= overallmatch_st:             # roughly the same test as where==before
                                howmuch = overallmatch_st - now_mo.end()    
                                overallmatch_st = now_mo.start()            #  extend match  (to exact start of that new bit of match) 
                                wider_start = max(0, wider_start-howmuch)   #  extend search range (by the size, which is sort of arbitrary)
                            else:                                           # we can assume where==after
                                howmuch = now_mo.start() - overallmatch_en  #  
                                overallmatch_en = now_mo.end()              #  extend match
                                wider_end = min(wider_end+howmuch, len(text))  #  extend search range


                            range_was_widened = True
                            
                            if debug:   
                                print( 'MATCHED type=%-20s:   %-25r  %s chars %s '%(
                                    find_name,
                                    now_mo.group(0),
                                    howmuch,
                                    where,
                                ) )
                            #TODO: extract what we need here
                            #changed = True
                            break # break iter
                        else:
                            raise ValueError("Don't know IE %r"%incl_excl)
                    #if changed:
                    #    break # break pattern list
                #if changed:
                #    break # break before/after
        
        s_art_context = '%s[%s]%s'%( text[wider_start:overallmatch_st], text[overallmatch_st:overallmatch_en].upper(), text[overallmatch_en:wider_end] )
        #print( 'SETTLED ON')
        #print( '\n'.join( textwrap.wrap(s_art_context.strip(), width=70, initial_indent='     ', subsequent_indent='     ') ) )
        #print( details )

        if 'lid' in details:
            details['lid_num'] = []
            lidtext = details['lid']
            words = list(  s.strip()  for s in re.split(r'[\s\n]*(?:,| en\b)', lidtext, flags=re.M)   if len(s.strip())>0 )
            for part in words:
                try:
                    details['lid_num'].append( int(part) )
                except ValueError:
                    try:
                        details['lid_num'].append( wetsuite.helpers.strings.interpret_ordinal_nl( part ) )
                    except:
                        pass


        ret.append( {
              'start': overallmatch_st,
                'end': overallmatch_en,
               'text': text[overallmatch_st:overallmatch_en],
      # 'contexttext':text,
            'details': details,
        } )

    return ret
