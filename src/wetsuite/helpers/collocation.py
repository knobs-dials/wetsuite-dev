#!/usr/bin/python
''' Quick and dirty version of some collocation code.

    TODO: 
    * add some code that give memory use a limit
    * look at different scoring methods, e.g. NLTK's association.py
'''

from functools import reduce
import operator
from collections import defaultdict


def product(l):
    ' product of all numbers in a list '
    return reduce(operator.mul, l, 1)


class Collocation:
    ''' A basic collocation calculator class. '''
    def __init__(self, connectors=()):
        ''' connectors takes a list of words that, 
              are removed when they appear at the _edge_ of an n-gram (for n > 1),
              but are left if they are inside (so for n >= 3)
        '''
        self.connectors = connectors
        self.uni   = defaultdict(int)
        self.grams = defaultdict(int)
        self.saw_tokens = 0


    def consume_tokens(self, token_list, gramlens=(2,3,4)):
        """ Takes a list of string tokens.
            Counts unigram and n-gram from it, for given values of n. 
        """
        self.saw_tokens += len(token_list)
        for i, val in enumerate(token_list):
            self.add_uni( val )

        for gramlen in gramlens:
            for i in range(len(token_list)-(gramlen-1)):
                gram = tuple(token_list[i:i+gramlen])
                self.add_gram( gram )


    def add_uni(self, s, cnt=1):
        ' Used by consume_tokens, you typically should not need this '
        self.uni[s] += cnt


    def add_gram(self, strtup, cnt=1):
        ' Used by consume_tokens, you typically should not need this '
        if strtup[0] in self.connectors:
            #print("IGNORE %r because of connector at pos 0"%(strtup,))
            return
        if strtup[-1] in self.connectors:
            #print("IGNORE %r because of connector at pos -1"%(strtup,))
            return
        self.grams[strtup] += cnt


    def cleanup_unigrams(self, mincount=2):
        """ Remove unigrams that are rare - by default: that appear just once. You may wish to increase this.
            ideally we remove all n-grams using them too, but it's faster to waste the memory and leave them there.
        """
        new_uni = defaultdict(int)
        for k, v in self.uni.items():
            if v >= mincount:
                new_uni[k] = v
        self.uni = new_uni


    def cleanup_ngrams(self, mincount=2):
        ''' CONSIDER: allow different threshold for each length, e.g. via a list for mincount '''
        new_grams = defaultdict(int)
        for k, v in self.grams.items():
            if v >= mincount:
                new_grams[k] = v
        self.grams = new_grams


    def score_ngrams(self, method='mik2', sort=True):
        ''' Takes the counts we already did, returns a list of items like::
                (string_tuple,              score,   count_combo,  [count, part, ...])
            e.g.::
                (('aangetekende', 'brief'), 1085.12, 16, [17, 17])

            The scoring logic is currently somewhat arbitrary, 
            and needs work before it is meaningful in a _remotely_ linear way.
        '''
        ret = []
        for strtup, tup_count in self.grams.items():
            # if you did a clean-unigrams, we should ignore anything involving the things that removed
            # CONSIDER: unseen unigrams as min(available scores) or tiny percentile or such
            skip_entry = False
            for s in strtup:
                if s not in self.uni:    # TODO: rethink, together with cleanup
                    skip_entry = True
                    break
            if skip_entry:
                continue

            uni_counts = list( self.uni[s]  for s in strtup)
            mul = product( uni_counts )

            # TODO: evaluate decent methods of collocation scoring. The ones I've seen so far seem statistically iffy.
            if method=='mik':
                score = (float(tup_count)) / mul

            elif method=='mik2':
                score = (float(tup_count)**2) / mul
            elif method=='mik3':
                score = (float(tup_count)**3) / mul
            else:
                raise ValueError('%r not a known scoring method'%method)

            score *= 35.**len(strtup)  # fudge factor to get larger-n  n-grams on roughly the same scale.
            # TODO: remove, or think about this more.   More related more to vocab size?

            ret.append(  ( strtup, score, tup_count, uni_counts )  )

        if sort:
            ret.sort(key = lambda x:x[1])

        return ret


    def counts(self):
        ' returns counts of tokens, unigrams, and n>2-grams '
        return {
          'from_tokens':self.saw_tokens,
             'unigrams':len(self.uni),
               'ngrams':len(self.grams),
        }
