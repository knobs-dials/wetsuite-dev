'''
Extracting specific patterns of text, 
mostly but not only aimed at references to citations 
  - by identifier 
    - BWB-ID
    - CVDR-ID
    - ECLI
    - CELEX
    - other EU references

  - also to and less-formal references to dutch laws)


It exists in part to point out that while probably useful,
they deal with things that aren't formalized via EBNF or whatnot,
so are probably best-effort, and contain copious hardcoding and messines.

So They may miss things.

Ideally, each function further notes how much can and can't expect from it.

Contributions are welcome, though in the interest of not immediately making a mess,
we may want contributions to go to a contrib/ at least at first     
'''
import re
import collections
import textwrap

import wetsuite.helpers.strings
import wetsuite.helpers.meta



def find_identifier_references( text,
                                ecli=True, celex=True,                     # more identifier-y
                                ljn=False,
                                vindplaatsen=True,
                                kamerstukken=True, euoj=True, eudir=True,  # more textual
                                nonidentifier=True,                        # even more textual
                               ):
    ''' TODO: rename to find_references or something else that's clear

        There is a good argument to make this more pluggable, rather than one tangle of a function.
    '''
    ret = []

    if ljn:
        for rematch in re.finditer( r'\b[A-Z][A-Z][0-9][0-9][0-9][0-9](,[\n\s]+[0-9]+)?\b', text, flags=re.M ):
            match = {}
            match['type']  = 'ljn'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            ret.append( match )


    if ecli:
        for rematch in wetsuite.helpers.meta._RE_ECLIFIND.finditer( text ):
            match = {}
            match['type']    = 'ecli'
            match['start']   = rematch.start()
            match['end']     = rematch.end()
            match['text']    = rematch.group( 0 )
            match['details'] = wetsuite.helpers.meta.parse_ecli( rematch.group(0) )
            try:
                wetsuite.helpers.meta.parse_ecli( match['text'] )
            except ValueError:
                match['invalid'] = True
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
        for rematch in wetsuite.helpers.meta._RE_CELEX.finditer( text ):
            match = {}
            match['type']  = 'celex'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            match['details'] = wetsuite.helpers.meta.parse_celex( rematch.group(0) )
            ret.append( match )

    _RE_EUOJ = re.compile(r'(OJ|Official Journal)[\s]?(C|CA|CI|CE|L|LI|LA|LM|A|P) [0-9]+([\s]?[A-Z]|/[0-9])*(, p. [0-9](\s*[\u2013-]\s*[0-9]+)*|, [0-9]{1,2}[./][0-9]{1,2}[./][0-9][0-9]{2,4})'.replace(' ',r'[\s\n]+'),
                          flags=re.M)

    if euoj:
        for rematch in _RE_EUOJ.finditer( text ):
            match = {}
            match['type']  = 'euoj'
            match['start'] = rematch.start()
            match['end']   = rematch.end()
            match['text']  = rematch.group( 0 )
            ret.append( match )

    _RE_EUDIR = re.compile(r'(Directive) [0-9]{2,4}/[0-9]+(/EC|EEC|EU)?'.replace(' ',r'[\s\n]+'),
                          flags=re.M)

    if eudir:
        for rematch in _RE_EUDIR.finditer( text ):
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


    ret.sort( key=lambda m: m['start'] )

    return ret



def find_nonidentifier_references(text, context_amt=60, debug=False):    # TODO: needs a better name
    ''' Attempts to find references like ::
            "artikel 5.1, tweede lid, aanhef en onder i, van de Woo"
        and parse and resolve as much as it can.

        @return: a list of (matched_text, parsed_details_dict)
           

        This is not a formalized format, 
        and while the law ( https://wetten.overheid.nl/BWBR0005730/ ) that suggests the format of these
        suggests succinctness and has near-templates, that is not what real-world use looks like.

        
        One reasonable approach might be 
          including each real-world variant explicitly, 
          as it lets you put stronger patterns first and fall back on fuzzier,
          it makes it clear what is being matched, and it's easier to see how common each is.
        However, it easily leads to false negatives -- missing real things.

        
        Instead, we 
        - start by finding some strong anchors
        - keep accepting bits of adjacent string as long as they look like things we know
          "artikel 5.1,"   "tweede lid,"   "aanhef en onder i"
        - then seeing what text is around it, which should be at least the law name
        

        Neither will deal with the briefest forms, e.g. "(81 WWB)"
        which is arguably only reasonable to recognize when you recognize either side
        (by known law name, which is harder for abbreviations in that it probably leads to false positives)
        ...and in that example, we might want to 
        - see if character context makes it reasonable - the parthentheses make it more reasonable than
          if you found the six characters '81 WWB' in any context 
        - check whether the estimated law (Wet werk en bijstand - BWBR0015703) has an article 81
        - check, in some semantic way, whether Wet werk en bijstand makes any sense in context of the text

        ...also so that we can return some estimation of 
        - how sure we are this is a reference,
        - how complete a reference is, and/or
        - how easy to resolve a reference is.

        
    '''
    ret = []
    artikel_matches = []

    for artikel_mo in re.finditer(r'\b(?:[Aa]rt(?:ikel|[.]|\b)\s*([0-9.:]+[a-z]*))', text):
        artikel_matches.append( artikel_mo )

    # note to self: just the article bit also good for creating an anchor for test cases later,
    #               to see what we miss and roughly why

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
            'grond':           [ 'B', 'E',  r'\bgrond(?: van)?\b'                                ],
            'bedoeld':         [ 'B', 'E',  r'\bbedoeld in\b'                                    ],

            #'komma':          [  '.',  re.compile(r',')                                         ],

            'hoofdstuk':       [ 'A', 'I',  r'\bhoofdstuk#\b'                                    ],
            'paragraaf':       [ 'A', 'I',  r'\bparagraaf#\b'                                    ],
            'aanwijzing':      [ 'A', 'I',  r'\b(?:aanwijzing|aanwijzingen)#\b'                  ],

            'onderdeel':       [ 'A', 'I',  r'\b(?:onderdeel|onderdelen)\b'                      ],
            'lid':             [ 'A', 'I',  r'\b(?:lid_(#)|(L)_(?:lid|leden))'                   ],
            'aanhefonder':     [ 'A', 'I',  r'\b((?:\baanhef_en_)?onder_[a-z]+)'                 ], # "en onder d en g"
            'sub':             [ 'A', 'I',  r'\bsub [a-z]\b'                                     ],

            #'vandh':          [  'E',  r'\bvan (?:het|de)\b'                                    ],
            ##'dezewet':       [  'I',  r'\bde(?:ze)? wet\b'                                     ],

            #'hierna':          [ 'A', 'E',  r'\b[(]?hierna[:\s]'                                ],
        }

        #re_some_ordinals = '(?:%s)'%( '|'.join( wetsuite.helpers.strings.ordinal_nl_20 ) )
        re_some_ordinals = '(?:%s)'%( '|'.join( wetsuite.helpers.strings.ordinal_nl(i) for i in range(100) ) )

        for k,(_,_,res) in find_things.items():
            # make all the above multiline matchers, and treat specific characters as signifiers we should be replacing
            #   the 'replace this character' is cheating somewhat because and can lead to incorrect nesting,
            #   so take care, but it seems worth it for some more readability
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
                    for now_mo in re.compile(find_re).finditer(text, pos=rng_st, endpos=rng_en): # TODO: check whether inclusive or exclusive
                        #now_size = now_mo.end() - now_mo.start()

                        if incl_excl == 'E': # recognizing a string that we want _not_ to include (not all that different from just not seeing something)
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
        #print( '\n'.join( textwrap.wrap(s_art_context.strip(),
        #               width=70, initial_indent='     ', subsequent_indent='     ') ) )
        #print( details )

        if 'lid' in details:
            details['lid_num'] = []
            lidtext = details['lid']
            words = list(  s.strip()
                           for s in re.split(r'[\s\n]*(?:,| en\b)', lidtext, flags=re.M)
                           if len(s.strip())>0  )
            for part in words:
                try:
                    details['lid_num'].append( int(part) )
                except ValueError:
                    try:
                        details['lid_num'].append( wetsuite.helpers.strings.interpret_ordinal_nl( part ) )
                    except ValueError:
                        pass


        ret.append( {
              'start': overallmatch_st,
                'end': overallmatch_en,
               'text': text[overallmatch_st:overallmatch_en],
      # 'contexttext':text,
            'details': details,
        } )

    return ret




def simple_tokenize(text: str):
    ' quick and dirty splitter into words. Mainly used by abbrev_find() '
    l = re.split('[\\s!@#$%^&*":;/,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+', text)
    return list(e.strip("'")   for e in l  if len(e)>0)


def abbrev_find(text: str):
    ''' Works on plain a string - TODO: accept spacy objects as well

        Looks for patterns like
          -  "Word Combination (WC)"
          -  "Wet Oven Overheid (Woo)"
          -  "With Periods (W.P.)"
          -  "(EA) Explained After"    (probably rare) 

          -  "BT (Bracketed terms)"
          -  "(Bracketed terms) BT"    (probably rare) 

        CONSIDER: 
          - how permissive to be with capitalization. Maybe make that a parameter?
          - allow and ignore words like 'of', 'the'
          - rewrite to deal with cases like
            - Autoriteit Consument en Markt (ACM)
            - De Regeling werving, reclame en verslavingspreventie kansspelen (hierna: Rwrvk)
            - Nationale Postcode Loterij N.V. (hierna: NPL)
            - Edelmetaal Waarborg Nederland B.V. (EWN)
            - College voor Toetsen en Examens (CvTE)
            - (and maybe:)
            - Pensioen- en Uitkeringsraad (PUR)
            - Nederlandse Loodsencorporatie (NLC)
            - Nederlandse Emissieautoriteit (NEa)
            - Kamer voor de Binnenvisserij (Kabivi)
            - (and maybe not:)
            - College van toezicht collectieve beheersorganisaties auteurs- en naburige rechten (College van Toezicht Auteursrechten (CvTA))
            - Keurmerkinstituut jeugdzorg (KMI)
          - listening to 'hierna: ', e.g.
            - "Wet Bevordering Integriteitbeoordelingen door het Openbaar Bestuur (hierna: Wet BIBOB)"
            - "Drank- en horecawet (hierna: DHW)"
            - "Algemene wet bestuursrecht (hierna: Awb)"
            - "het Verdrag betreffende de werking van de Europese Unie (hierna: VWEU)"
            - "de Subsidieregeling OPZuid 2021-2027 (hierna: Subsidieregeling OPZuid)"
            - "de Wet werk en bijstand (hierna: WWB)"
            - "de Wet werk en inkomen naar arbeidsvermogen (hierna: WIA)"
            - "de Wet maatschappelijke ondersteuning (hierna: Wmo)"

            These seem to be more structured, in particular when you use (de|het) as a delimiter
            This seems overly specific, but works well to extract a bunch of these

          
        @return: a list of ('ww', ['word', 'word']) tuples, 
        pretty much as-is so it (intentionally) contains duplicates

        Will both over- and under-accept, so if you want clean results, consider e.g. reporting only things present in multiple documents. 
        see e.g. merge_results()
    '''
    matches = []

    toks       = simple_tokenize( text )
    toks_lower = list( tok.lower()  for tok in toks )

    ### Patterns where the abbreviation is bracketed
    # look for bracketed letters, check against context
    for tok_offset, tok in enumerate(toks):
        match = re.match(r'[(]([A-Za-z][.]?){2,}[)]', tok) # does this look like a bracketed abbreviation?
        if match:   # (we over-accept some things, because we'll be checking them against contxt anyway.   We could probably require that more than one capital should be involved)
            abbrev = match.group().strip('()')
            letters_lower = abbrev.replace('.','').lower()

            match_before = []
            for check_offset, l in enumerate(letters_lower):
                check_at_pos = tok_offset - len(letters_lower) + check_offset
                if check_at_pos < 0:
                    break
                if toks_lower[check_at_pos].startswith( letters_lower[check_offset] ):
                    match_before.append( toks[check_at_pos] )
                else:
                    match_before = []
                    break
            if len(match_before) == len(letters_lower):
                matches.append( (abbrev,match_before) )

            match_after = []
            for check_offset, l in enumerate( letters_lower ):
                check_at_pos = tok_offset+1+check_offset
                if check_at_pos >= len(toks):
                    break
                if toks_lower[check_at_pos].startswith( letters_lower[check_offset] ):
                    match_after.append( toks[check_at_pos] )
                else:
                    match_after = []
                    break

            if len(match_after) == len(letters_lower):
                matches.append( (abbrev,match_after)  )

    ### Patterns where the explanation is bracketed
    # Look for the expanded form based on the brackets, make that into an abbreviation
    # this is a little more awkward given the above tokenization.  We could consider putting brackets into separate tokens.  TODO: check how spacy tokenizes brackets
    for start_offset, tok in enumerate(toks):
        expansion = []
        if tok.startswith('(') and not tok.endswith(')'): # start of bracketed explanation (or parenthetical or other)
            end_offset = start_offset
            while end_offset < len(toks):
                expansion.append( toks[end_offset] )
                if toks[end_offset].endswith(')'):
                    break
                end_offset += 1

        if len(expansion) > 1: # really >0, but >1 helps at end of the list
            expansion = list( w.strip('()')  for w in expansion if len(w.lstrip('()'))>0) # our tokenization leaves brackets on words (rather than being seprate tokens)
            expected_abbrev_noperiods = ''.join(w[0]        for w   in expansion)
            expected_abbrev_periods   = ''.join('%s.'%let   for let in expected_abbrev_noperiods)
            if start_offset >= 1        and  toks_lower[start_offset-1] in (expected_abbrev_noperiods.lower(), expected_abbrev_periods.lower()):
                matches.append( (toks[start_offset-1], expansion ))   # (add the actual abbreviated form used)
            if end_offset < len(toks)-1 and  toks_lower[end_offset+1] in (expected_abbrev_noperiods.lower(), expected_abbrev_periods.lower()):
                matches.append( (toks[end_offset+1], expansion ))

    return matches




def abbrev_count_results(l, remove_dots=True):
    ''' In case you have a lot of data, you can get reduced yet cleaner results 
        by reporting how many distinct documents report the same specific explanation 
        (note: NOT how often we saw this explanation).

        Takes a list of document results, 
        where each such result is what find_abbrevs() returned, i.e. a list of items like ::
            ('ww', ['word', 'word'])
        
        Returns something like: ::
          { 'ww' : {['word','word']: 3,  ['word','wordle']: 1 } }
        where that 3 would be how mant documents had this explanation.

        CONSIDER: 
          - case insensitive mode where it counts lowercase, but report whatever the most common capitalisation is
    '''
    ret = {}
    for doc_result in l:
        for ab, words in doc_result:
            words = tuple(words)
            if remove_dots:
                ab = ab.replace('.','')
                if ab not in ret:
                    ret[ab] = {}
                if words not in ret[ab]:
                    ret[ab][words] = set()
                ret[ab][words].add( id(doc_result) )

    counted = {} # could do this with syntax-fu, but this is probably more more readable
    for abbrev, word_idlist in ret.items():
        counted[abbrev] = {}
        for word, idlist in word_idlist.items():
            counted[abbrev][word] = len(idlist)

    return counted
