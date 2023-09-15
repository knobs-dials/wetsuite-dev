#!/usr/bin/python
''' Quick and dirty version of some collocation code.

    TODO: 
    * add some code that give memory use a limit
    * look at different scoring methods, e.g. NLTK's association.py
'''

from functools import reduce  
import operator, re
from collections import defaultdict


def product(l):
    ' product of all numbers in a list '
    return reduce(operator.mul, l, 1)


class Collocation:
    ''' A basic collocation calculator class. '''
    def __init__(self, connectors=[]):
        ''' connectors takes a list of words that, 
              are removed from the _edge_ of an n-gram (for n>1),
              but are left if they are inside (so for n>=3)
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
        for i in range(len(token_list)):
            self.add_uni( token_list[i] )

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
        self.grams[strtup] += 1


    def cleanup_unigrams(self, mincount=2):
        """ Remove unigrams that are rare - by default: that appear just once. You may wish to increase this.
            ideally we remove all n-grams using them too, but it's CPU-cheaper to leave the entries in memory. Hm.
        """
        new_uni = defaultdict(int)
        for k, v in self.uni.items():
            if v>=mincount:
                new_uni[k] = v
        self.uni = new_uni


    def cleanup_grams(self, mincount=2):
        ''' CONSIDER: allow a list for mincount as well
        '''
        new_grams = defaultdict(int)
        for k, v in self.grams.items():
            if v>=mincount:
                new_grams[k] = v
        self.grams = new_grams


    def score_grams(self, method='mik2', sort=True):
        ''' score n-grams we have counted 
        
            The scoring logic is currently somewhat arbitrary, and needs work.
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
            mul = product(uni_counts) 
            
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
        return {
    'from_tokens':self.saw_tokens,
            'uni':len(self.uni),
          'grams':len(self.grams),
        }
        




if __name__ == '__main__':
    ''' when run as a script, it will take arguments it expects to be plain text files.    You probably want moderately large files ''' 
    import time, sys

    def simple_tokenize(s):
        ' simple split into words ' 
        l = re.split('[\s!@#$%^&*()"\':;/.,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+', s)
        return list(e   for e in l  if len(e)>0)


    for filename in sys.argv[1:]:
        coll = Collocation( 
            connectors='de een het  dat die   van voor met in op bij om   en of   is   aan  ook   je ik we'.split() 
        )

        print( "Reading in data")
        sents = open( filename ).readlines()#[:150000]
        print( '  number of sentences: %d'%len(sents) )

        print( "Counting")
        for sent in sents:
            coll.consume_text( simple_tokenize(sent.rstrip()) )

        print( "Cleanup")
        print( coll.counts() )
        coll.cleanup_unigrams(mincount=3)
        coll.cleanup_grams(mincount=8)
        print( coll.counts() )

        print( "Scoring")
        scores = coll.score_grams( method='mik2', sort=True )
        for strtup, score,  tup_count, uni_counts in scores[-5000:]:
            print(' %9.3f   %50s    %20s %20s=%d'%(score, ' '.join(strtup),   tup_count, uni_counts, product(uni_counts)) )

