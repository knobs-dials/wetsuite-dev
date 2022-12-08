#!/usr/bin/python3
''' create wordcloud images.  Uses an existing wordcloud module '''
import collections
from typing import List
import wordcloud #  if not installed, do  pip3 install wordcloud


def wordcloud_from_freqs(freqs: dict, width:int=1800, height:int=800):
    ''' Takes a string->count dict  (probably from one of the helper functions) 
        Returns an image.
    '''
    wco = wordcloud.WordCloud( width = width,  height = height,  background_color = 'white',  min_font_size = 10 )
    im = wco.generate_from_frequencies( freqs )
    return im.to_image()



def count_case_insensitive(strings: List[str]) -> dict:
    ''' Takes a list of strings, returns a { string: count } dict.
        Specifically, it count strings as if they were case-insensitive, but report the most common case of capitalisation 

        For example, count_case_insensitive( 'a A A a A A a B b b B b'.split()) 
        will give {'A':7, 'b':5}

        TODO: merge logic with freqs_simple
    '''
    count = collections.defaultdict(lambda: collections.defaultdict(int)) # { lower form -> { real form -> int } }
    for string in strings:
        count[string.lower()][string] += 1
    ret = {}
    for ls in count:
        variants = sorted( count[ls].items(), key=lambda x:x[1], reverse=True )
        ret[ variants[0][0] ] = sum( cnt  for _,cnt in variants)       
    return ret



def freqs_simple(text:str, stopwords=None) -> dict:
    ''' Takes text, 
        Returns a string->count dict   using fairly simple word splitting, and removing stoplist words and numbers
    '''
    stop = set()
    if stopwords is None:
        stop.update(wordcloud.STOPWORDS) # english stopwords
        stop.update(['de','het','een', 'en','of', 'die','van', 'op','aan','door','voor','tot','bij', 'kan','wordt'])
    else:
        stop.update(stopwords)

    wco = wordcloud.WordCloud( stopwords = stop, normalize_plurals=True, collocations=True, include_numbers=False, min_word_length=2 )
    return wco.process_text(text)


def freqs_from_spacy_document(doc_or_sequence_of_docs, remove_stop=True, restrict_to_tags=('NOUN', 'ADJ', 'ADV', 'VERB'), weigh_deps={'nsubj':5, 'obj':3} ) -> dict:
    ''' Returns a string->count dict   trying to be smarter about selecting useful words 
    
        CONSIDER: whether half of that can be part of some topic-modeling filtering. And how filters might work around spacy.
    '''
    counts = collections.defaultdict(int)

    if isinstance(doc_or_sequence_of_docs, collections.Sequence):
        things = doc_or_sequence_of_docs
    else:
        things = [doc_or_sequence_of_docs]

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
        if hasattr(token, 'dep_'):
            if token.dep_ in weigh_deps:
                counts[ token.text ] += weigh_deps[token.dep_]
            else:
                counts[ token.text ] += 1
        
        if hasattr(thing, 'ents'): # TODO: tests
            for ent in  thing.ents:
                #print( "ENT %s"%ent.text )
                counts[ ent.text ] += 2

        if hasattr(thing, 'noun_chunks'): # TODO: tests
            for nc in thing.noun_chunks:
                #print( "NC %s"%nc.text )
                counts[ nc.text ] += 2

    return counts

        
if __name__ == '__main__':
    import sys
    # quick and dirty tests from filenames or stdin - no language processing beyond stoplists
    if len(sys.argv) > 1:
        for fn in sys.argv[1:]:
            with open(fn) as f:
                freqs = freqs_simple( f.read() )
            im = wordcloud_from_freqs(freqs)
            im.show()
    else:
        text = sys.stdin.read()
        freqs = freqs_simple( text )
        im = wordcloud_from_freqs(freqs)
        im.show()



