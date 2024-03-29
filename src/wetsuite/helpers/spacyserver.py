''' Functions to help access a running instance of extas/spacy_server.py
'''
import json
import time

import requests

######### Spacy-server-specific

def http_api(q, ip='127.0.0.1', port=8282, want_svg=False, as_text=False, timeout=10):
    """
    Feed through a query (by default just text in q) to spacy_server
    Return the data it gives us as a dict

    Notes:
        - We return our own data-only conception of the information tacked onto the spacy Document.
        There was previously an experiment to serialize/pickle/docbin the spacy object
        so that we might transparently one or more other hosts to do work for us,
        the overheads of deserializing are high - that serialization seems only useful when storing significant work.

        - Is little more than a HTTP POST (because requests larger than ~4K aren't allowed),
        and some JSON wrapping. 

        - want_svg requests spacy_server to sump dependencies SVG in a value (yes, that's cheating encoding-wise).
        Defaults to False because it's large, and there are various uses where you don't want it.
        
        - timeout mostly to avoid the possibility of hanging forever if you don't specify one
    """
    if want_svg:
        want_svg = 'y'
    else:
        want_svg = 'n'
    url = 'http://%s:%s/'%(ip,port)
    res = requests.post(url, data={'q':q, 'want_svg':want_svg}, timeout=timeout)
    if res.status_code == 500:
        raise RuntimeError('Error reaching spacy API: %s'%res.text)
    if as_text:
        ret = res.text
    else:
        ret = json.loads( res.text )
    return ret



def parse(nlp, query_string, nlp_lock=None, want_svg=True, want_sims=False):
    ''' Takes a spacy nlp object, and python string.
            
        Runs that model on that string 
        
        Extracts some useful stuff to return in a dict, 
        (only JSON-serializable objects, so that we can send it over a HTTP API)
        
        Should probably be split up into more parts

        CONSIDER: allow parameter to split on series of newlines, and nlp.pipe() it? 
                  (but: arguably the wrong place to do that splitting)
        CONSIDER: add doc.to_bytes and doc.from_bytes 
        '''

    import spacy
    from spacy import displacy
    start_time = time.time()

    ret = {}
    ret['query_string'] = query_string
    ret['query_string_length'] = len(query_string)

    if nlp_lock is not None:
        with nlp_lock:
            doc = nlp( query_string )
    else:
        doc = nlp( query_string )

    parse_took = time.time() - start_time
    ret['parse_msec'] = '%d'%(1000.*parse_took)

    ret['tokens'] = []
    for i, token in enumerate(doc):
        ret['tokens'].append( {
            'i':i,
            'text':token.text,
            'lemma':token.lemma_,
            'pos':token.pos_,
            'tag':token.tag_,
            'dep_type':token.dep_,
            'dep_from_i':token.head.i,
            'is_stop':token.is_stop,
            'is_oov':token.is_oov,
            'norm':'%.3f'%float(token.vector_norm),
            #'vector':list(round(ve,3)  for ve in token.vector.tolist()), ## vector stuff is messy - more reading is required
        } )

    start_rest = time.time()
    ret['sentences'] = []
    sent_i = 0
    for sent in doc.sents:
        # TODO: decide what exactly to do with 
        # spaces, 
        # and consistency between sentence_ranges and sents_svgs,
        # and duplication, and off-by-one mistakes I probably made,
        # and the easiest way for people to use this.
        ss, se = sent.start, sent.end

        if doc[ss].pos_ in ('SPACE',):
            ss += 1

        if ss != se: # net effect: swallow SPACE-only sentence (paragraphs))
            sent_entry = {'i':sent_i}
            sent_entry['range'] = [ss,se]

            # sentence complexity based on avg distance of dependencies
            dists = []
            for pos in range(ss, se):
                tok = doc[pos]
                dist = tok.head.i - tok.i
                dists.append( dist )
            abs_dists = list( abs(d)  for d in dists )
            avg_dist = float(sum(abs_dists)) / len(abs_dists)
            sent_entry['complexity'] = round( avg_dist, 2 )

            if want_svg:
                svg_text = displacy.render(
                        doc[ss:se],
                        style   = "dep",
                        options = {
                            'compact':True, 'bg':'#ffffff00', 
                            'distance':85, 'word_spacing':42, 'arrow_stroke':1,
                        }
                    )
                # hack to get 100%-width behaviour
                #svg_w = re.search('width="([0-9]+)', svg_text).groups()[0]
                #svg_h = re.search('height="([0-9]+)', svg_text).groups()[0]
                #svg_text = re.sub('<svg ', '<svg viewbox="0 0 %s %s" '%(svg_w, svg_h), svg_text)

                # hackiness to make the depname a link to its explanation on universaldependencies.org
                #  (except it's stanford, not udep, I think, so this is hackish even if it is useful?)
                if 1: # somewhat slower, but hey
                    import lxml.etree as ET
                    ET.register_namespace('svg',   "http://www.w3.org/2000/svg")
                    ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
                    tree = ET.fromstring(svg_text)
                    tree.set('xmlns', 'http://www.w3.org/2000/svg')

                    for tspan in tree.getiterator(tag='{http://www.w3.org/2000/svg}tspan'):
                        cl = tspan.get('class')
                        if 'displacy-tag' in cl:
                            tspan.set('class', cl+' '+tspan.text)

                    for g in tree.getiterator(tag='{http://www.w3.org/2000/svg}g'):
                        if g.get('class') == 'displacy-arrow':
                            h = g[2]
                            a = ET.Element('{http://www.w3.org/2000/svg}a')
                            depname = g[1][0].text
                            changes = { # these seem to come from stanford, not UD, so maybe make a linkable form from its PDF summary instead?
                                  'auxpass':'aux:pass',
                                'nsubjpass':'nsubj:pass',
                                # these don't have 1:1 between stanford and UD
                                     'pobj':'obj', # arguably don't link these two?
                                     'dobj':'obj',
                                      'neg':'',
                                    'acomp':'',
                                     'attr':'',
                                   'dative':'',
                                     'prep':'',
                                     'poss':'', # could be det:poss or nmod:poss
                                     'pcomp':'', # ?
                                # not sure about these
                                    'relcl':'acl:relcl', 
                                      'prt':'compound:prt',
                                 'npadvmod':'advmod',      
                                # doesn't seem to exist in either stanford or UD?
                                     'oprd':'',
                            }
                            if depname in changes:
                                depname = changes[depname]
                            if depname != '':
                                a.set('href',
                                      'https://universaldependencies.org/u/dep/%s.html'%(depname.replace(':','-')) )
                                a.set('target',
                                      '_blank')
                                a.append( g[1] )
                                g.replace( g[1], a )
                                g.append(h) # I have no idea why it disappears if I don't.
                            # else change nothing

                    svg_text = ET.tostring(tree, encoding='utf8', xml_declaration=False).decode('u8')

                sent_entry['svg']   = svg_text

            ret['sentences'].append( sent_entry )
            sent_i += 1


    ret['ents'] = []
    if hasattr(doc, 'ents'): # not sure this test is necessary
        for ent in doc.ents:
            ret['ents'].append( {
                'text':ent.text,
                'tok_start':ent.start,
                'tok_end':ent.end,
                'label':ent.label_,
                #TODO: whether it contains subject or object?
                #'explain':spacy.explain( ent.label_ ),
            } )

    ret['noun_chunks'] = []
    for noun_chunk in doc.noun_chunks:
        ret['noun_chunks'].append( {
            'text':noun_chunk.text,
            'tok_start':noun_chunk.start,
            'tok_end':noun_chunk.end,
            'head_tok_i':noun_chunk.root.i,
            'head_tok_dep':noun_chunk.root.dep_,
            #TODO: whether it contains subject or object?
        } )

    #if want_sims:
    #    start = time.time()
    #    sims = helpers_spacy.similar_chunks(doc, 1,1,1)
    #    took = time.time() - start
    #    ret['sims_msec'] = round(1000.*took, 1)
    #    ret['sims'] = sims

    ret['post_parse_augment_msec'] = '%d'%(1000.*(time.time()-start_rest))

    ret['overall_msec'] = '%d'%(1000.*(time.time()-start_time))
    #ret['docdir'] = dir(doc)
    return ret
