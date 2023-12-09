#!/usr/bin/python3
'''
Create wordcloud images; mostly a thin wrapper module around an existing wordcloud module.

The wordcloud module we use likes to wrap all logic and parameters in one big class,
so this (thin) wrapper module exists largely to separate out the counting,
    - to introduce some flexibility in how we count in a wordcloud.
    - and to make those counting functions usable for other things
'''
import collections, re
from typing import List


# The wordcloud module imports matplotlib so we might need to ensure a non-graphical backend
#   TODO: read up, it's probably good to do this conditionally -- and lazily?
import matplotlib
matplotlib.use('Agg')

import wordcloud  #  if not installed, do  pip3 install wordcloud       also this is intentionally after the previous, so:   pylint: disable=C0413
                  # note that it draws in matplotlib, numpy, and PIL
                  # and unlike the linter suggests, it should _NOT_ be above the matplotlib import


# the wordcloud module loads some english stopwords by default.
# The functions added below requires you to be more explicit, 
#   in which case some prepared lists are handy:
stopwords_en = [ # wordcloud.STOPWORDS loads:
    "a", "about", "above", "after", "again", "against", "all", "also", "am", "an", "and", "any", 
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", 
    "both", "but", "by", "can", "can't", "cannot", "com", "could", "couldn't", "did", "didn't", 
    "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "else", "ever", "few", 
    "for", "from", "further", "get", "had", "hadn't", "has", "hasn't", "have", "haven't", 
    "having", "he", "he'd", "he'll", "he's", "hence", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "however", "http", "i", "i'd", "i'll", "i'm", "i've",
    "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "just", "k", "let's", "like",
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "otherwise", "ought", "our", "ours", "ourselves", "out", "over", "own", 
    "r", "same", "shall", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", 
    "since", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "therefore", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", 
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", 
    "why", "why's", "with", "won't", "would", "wouldn't", "www", "you", "you'd", "you'll", 
    "you're", "you've", "your", "yours", "yourself", "yourselves" 
]
' Some English stopwords  '

stopwords_nl = (
    'de','het', 'een', 'en','of', 'die','van', 'op','aan','door','voor','tot','bij', 'kan','wordt',
    'in', 'deze', 'dan', 'is', 'dat'
)
' Some Dutch stopwords  '


def wordcloud_from_freqs(freqs: dict, 
                         width:int=1200, height:int=300, background_color='white', min_font_size=10, **kwargs):
    ''' Takes a {string: count} dict, returns a PIL image object.

        That image will look a bunch cleaner when you have cleaned up the string:count,
        so take a look at using one of the count_ helper functions.
    '''
    wco = wordcloud.WordCloud( width=width,  height=height,
                               background_color=background_color,  min_font_size=min_font_size,
                               **kwargs )
    im = wco.generate_from_frequencies( freqs )
    return im.to_image()



def count_normalized(strings: List[str],  min_count:int=1,  min_word_length=0,  normalize_func=None, stopwords=(), stopwords_i=() ):
    ''' Takes a list of strings, returns a string:count dict, with some extra processing

        Parameters beyond normalize_func are mostly about removing things you would probably call, 
        so you do not have to do that separately.

        Note that if you are using spacy or other POS tagging anyway, 
        filtering e.g. just nouns and such before handing it into this 
        is a lot cleaner and easier (if a little slower).

        CONSIDER: imitating wordcloud collocations= behaviour
        CONSIDER: imitating wordcloud normalize_plurals=True
        CONSIDER: imitating wordcloud include_numbers=False
        CONSIDER: separating out different parts of these behaviours

        @param normalize_func: half the point of this function. Should be a str->str function. 
          - We group things by what is equal after this function is applied, but we report the most common case before it is. 
            For example, to _count_ blind to case, but report just one (the most common case) ::
                count_normalized( "a A A a A A a B b b B b".split(),  normalize_func=lambda s:s.lower() ) 
            would give ::
                {"A":7, "b":5}
          - Could be used for other things.  For example, 
            if you make normalize_func map a word to its lemma, then you unify all inflections, and get reported the most common one.
       
        @param  min_word_length:
          - strings shorter than this are removed.
            This is tested after normalization, so you can remove things in normalization too.

        @param min_count:
          - if integer, or float >1:         
            we remove if final count is < that count,  
          - if float  in 0 to 1.0 range:     
            we remove if the final count is < this fraction times the maximum count we see

        @param stopwords:
           - defaults to not removing anything
           - handing in a list uses yours instead. 
             There is a stopwords_nl and stopwords_en in this module 
             to get you started but you may want to refine your own
        @param stopwords_i: 
           - defaults to not removing anything

        @return: a { string: count } dict
    '''
    stop = set()
    if stopwords is None:
        stop.update(stopwords_en)
        stop.update(stopwords_nl)
    else:
        stop.update(stopwords)
    stop_lower = list(sws.lower()   for sws in stopwords_i)

    # count into { normalized_form: { real_form: count } }
    count = collections.defaultdict(lambda: collections.defaultdict(int))
    for string in strings:
        if string in stop:
            continue
        if string.lower() in stop_lower:
            continue

        norm_string = string
        if normalize_func is not None: 
            norm_string = normalize_func(string)

        if len(norm_string) < min_word_length:
            continue
        count[ norm_string ][ string ] += 1

    # filter counts, choose preferred form
    ret = {}
    # could do this with expression-fu but let's keep it readable
    max_count = 0
    for normform in count:
        for _, varamt in count[normform].items():
            max_count = max(max_count, varamt)

    for normform in count:
        variants_dict = sorted( count[normform].items(), key=lambda x:x[1], reverse=True )
        sum_count = sum( cnt  for _,cnt in variants_dict )
        if isinstance(min_count, int)  or  min_count > 1:
            if sum_count >= min_count:
                ret[ variants_dict[0][0] ] = sum_count
        elif isinstance(min_count, float):
            # TODO: complain if not in 0.0 .. 1.0 range
            if sum_count >= min_count*max_count:
                ret[ variants_dict[0][0] ] = sum_count
        else:
            raise TypeError("Don't know what to do with %s"%type(min_count))
    return ret


def count_case_insensitive(strings: List[str],  min_count=1,  min_word_length=0,  stopwords=()):
    ''' Calls count_normalized()  with  normalize_func=lambda s:s.lower() 
        which means it is case insensitive in counting strings, but it reports the most common capitalisation.

        Explicitly writing a function for such singular use is almost pointless, yet this seems like a common case and saves some typing.
        @param strings:         
        @param min_count:       
        @param min_word_length: 
        @param stopwords:       
        @return: 
    '''
    return count_normalized( strings, min_count=min_count, min_word_length=min_word_length, normalize_func=lambda s:s.lower(), stopwords=stopwords )


def count_from_spacy_document(doc_or_sequence_of_docs, remove_stop=True, restrict_to_tags=('NOUN', 'PROPN', 'ADJ', 'ADV', 'VERB'), 
                              add_ents=True, add_ncs=True,
                              weigh_deps={'nsubj':5, 'obj':3} ):
    ''' Takes a spacy document, returns a string->count dict 
        
        Does a lot of fairly specific things (a bit too specific to smush into one function, really)
        to be smart about removing low-content words, and focusing on terms.
        
        @param restrict_to_tags:  removes if not in this POS list - which defaults to nouns, adjectives, adverbs, and verbs (and removes a lot of fillter words)
        @param remove_stop:       removes according to Token.is_stop

        @param add_ents:          whether to add phrases from Doc.ents
        @param add_ncs:           whether to add phrases from Doc.noun_chunks
 
        @param weigh_deps:        exists to weigh words/ent/ncs stronger when they are/involve the sentence's subject or object

        CONSIDER: make this a filter instead, so we can feed the result to count_normalized()
        CONSIDER: whether half of that can be part of some topic-modeling filtering.  And how filters might work around spacy.
    '''
    counts = collections.defaultdict(int)

    if isinstance(doc_or_sequence_of_docs, collections.Sequence): # that seems slightly more general than type in (tuple, list)
        things = doc_or_sequence_of_docs
    else:
        things = [doc_or_sequence_of_docs]

    # TODO: REVIEW THE BELOW BLOCK, IT WAS CERTAINLY INCORRECT BEFORE
    for thing in things:
        for token in thing:
            if remove_stop and token.is_stop:
                #print( "SKIP %r - is stopword"%token.text)
                continue
            if restrict_to_tags is not None  and  token.pos_ not in restrict_to_tags:
                #print( "SKIP %r - based on tag %s"%(token.text, token.pos_))
                continue
                
            counts[ token.text  ] += 1

            # TODO: take dict of weighs

            # TODO: make the following conditional
            if hasattr(token, 'dep_'):
                if token.dep_ in weigh_deps:
                    counts[ token.text ] += weigh_deps[token.dep_]
                else:
                    counts[ token.text ] += 1

            if add_ents  and  hasattr(thing, 'ents'): # TODO: tests
                for ent in  thing.ents:
                    #print( "ENT %s"%ent.text )
                    counts[ ent.text ] += 2
                # TODO: involve weigh_deps

            if add_ncs  and  hasattr(thing, 'noun_chunks'): # TODO: tests
                for nc in thing.noun_chunks:
                    #print( "NC %s"%nc.text )
                    counts[ nc.text ] += 2
                # TODO: involve weigh_deps

    return counts


def simple_tokenize(text: str):
    ''' split string into words - in a very dumb way but slightly better than just split() 
        @param text: a single string
        @return: a list of words
    '''
    l = re.split(r'[\\s!@#$%^&*":;/,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+', text)
    return list(e.strip("'")   for e in l  if len(e)>0)



# if __name__ == '__main__':
#     # quick and dirty tests from text files handed in
#     import sys
# 
#     for fn in sys.argv[1:]:
#         with open(fn) as f:
#             filedata = f.read()
#             toks = simple_tokenize( filedata )
#             freqs = count_normalized( toks, min_count=2, normalize_func=lambda s:s.lower().strip('([])') )
#             #print( freqs )
#         im = wordcloud_from_freqs(freqs)
#         im.show() # show in GUI
