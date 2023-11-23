''' basic pattern matching to extract abbreviations '''
import re, pprint


def simple_tokenize(text: str):  # quick and dirty tokenizer
    ' split string into words '
    l = re.split('[\\s!@#$%^&*":;/,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+', text)
    return list(e.strip("'")   for e in l  if len(e)>0)


def find_abbrevs(text: str):
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




def count_results(l, remove_dots=True):
    ''' In case you have a lot of data, you can get reduced yet cleaner results 
        by reporting how many distinct documents report the same specific explanation 
        (note: NOT how often we saw this explanation).

        Takes a list of document results, 
        where each such result is what find_abbrevs() returned, i.e. a list of ('ww', ['word', 'word'])
        
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



if __name__ == '__main__':
    pprint.pprint( find_abbrevs( find_abbrevs.__doc__ ) )
