#!/usr/bin/python3
''' create wordcloud images.  Uses an existing wordcloud module '''
import collections
from typing import List
import wordcloud #  if not installed, do  pip3 install wordcloud


def wordcloud_from_freqs(freqs: dict, width:int=1800, height:int=800):
    ''' Takes a {string: count} dict  (probably from one of the helper functions) assumed to be filtered nicely already.
        Returns an image.
    '''
    wco = wordcloud.WordCloud( width=width,  height=height,  background_color='white',  min_font_size=10 )
    im = wco.generate_from_frequencies( freqs )
    return im.to_image()


stopwords_en = wordcloud.STOPWORDS
stopwords_nl = ('de','het','een', 'en','of', 'die','van', 'op','aan','door','voor','tot','bij', 'kan','wordt')



def count_normalized(strings: List[str], min_count:int=1, min_word_length=2, normalize_func=None, stopwords=None) -> dict:
    ''' Takes a list of strings, returns a { string: count } dict.

        By default, this counts strings as if they were case-insensitive, but report the most common case of capitalisation,
        which is due to the default normalize_func.

        For example, count_case_insensitive( 'a A A a A A a B b b B b'.split()) 
        will give {'A':7, 'b':5}

        
         normalize_func: should be a str->str function.   If you hand in None (default), it defaults to apply str.lower()

        min_word_length: strings shorter than this are not counted.
                         This is tested after normalization, so you can remove things in normalization too.

              min_count: if the final count is < min_count, it does not show up in the results 
                         CONSIDER: top-n, or float as percentile or such
        
              stopwords: defaults to some English and Dutch stopwords, handing in a list uses yours instead 
                         hand in an empty list or tuple to not use stopwords
                         CONSIDER: have case insensitive and case sensitive stopwords
                         Note that if you're using spacy or other POS tagging, 
                         filtering e.g. just nouns and such before handing it into this is a lot cleaner and easier, if a little slower.

            CONSIDER: imitating wordcloud's collocations= behaviour
            CONSIDER: imitating wordcloud's normalize_plurals=True
            CONSIDER: imitating wordcloud's include_numbers=False
    '''
    if normalize_func is None: 
        normalize_func = lambda s:s.lower()
    # else assume it's a useful function

    stop = set()
    if stopwords is None:
        stop.update(stopwords_en)
        stop.update(stopwords_nl)
    else:
        stop.update(stopwords)

    count = collections.defaultdict(lambda: collections.defaultdict(int)) # { lower_form: { real_form: count } }
    for string in strings:
        if string in stop:
            continue
        norm_string = normalize_func(string)
        if len(norm_string) < min_word_length:
            continue
        count[ norm_string ][ string ] += 1
    ret = {}
    for ls in count:
        variants = sorted( count[ls].items(), key=lambda x:x[1], reverse=True )
        sum_count = sum( cnt  for _,cnt in variants)
        if sum_count >= min_count:
            ret[ variants[0][0] ] = sum_count
    return ret



def freqs_from_spacy_document(doc_or_sequence_of_docs, remove_stop=True, restrict_to_tags=('NOUN', 'PROPN', 'ADJ', 'ADV', 'VERB'), weigh_deps={'nsubj':5, 'obj':3} ) -> dict:
    ''' Returns a string->count dict   
        Tries to to be smarter about selecting useful words 

        CONSIDER: make this a filter instead, so we can feed the result to count_normalized()

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
    # quick and dirty tests from text files

    import sys, re

    def simple_tokenize(text: str):  # quick and dirty tokenizer
        ' split string into words '
        l = re.split('[\\s!@#$%^&*":;/,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+', text)
        return list(e.strip("'")   for e in l  if len(e)>0)

    for fn in sys.argv[1:]:
        with open(fn) as f:
            filedata = f.read()
            toks = simple_tokenize( filedata )
            freqs = count_normalized( toks, min_count=2, normalize_func=lambda s:s.lower().strip('([])') )
            #print( freqs )
        im = wordcloud_from_freqs(freqs)
        im.show()



