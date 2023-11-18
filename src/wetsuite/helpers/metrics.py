'''

'''


def sentence_complexity_spacy( span ):
    ''' Takes an already-parsed spacy sentence 

        Mainly uses the distance of the dependencies involved, which is fairly decent for how simple it is. Consider e.g.
        - long sentences aren't necessarily complex at all (they can just be separate things joined by a comma),
            they mainly become harder to parse if they introduce long-distance references.
        - parenthetical sentences will lengthen references across them
        - lists and flat compounds will drag the complexity down

        Also, this doesn't really need normalization

        Downsides include that spacy seems to assign some dependencies just because it needs to, not necessarily sensibly.
        Also, we should probably count most named entities as a single thing, not the amount of tokens in them
    '''
    dists = []
    #print( "-")
    for tok in span:
        dist = tok.head.i - tok.i
        #print("%s --%s--> %s (dist %d)"%(tok, tok.dep_, tok.head, dist) )
        dists.append( dist ) 
        # no abs, we may want to weigh forward referenes harder than backwards -- but probably check that with each specific dependency type?
    #print( dists, sent )
    abs_dists = list( abs(d)  for d in dists )
    avg_dist = float(sum(abs_dists)) / len(abs_dists)

    #token.is_oov


    # other ideas:
    # - count amount of referents / people
    # - word frequency
    # - collocations

    #https://raw.githubusercontent.com/proycon/tscan/master/docs/tscanhandleiding.pdf

    return avg_dist
