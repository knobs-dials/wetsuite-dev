''' helper functions related to spacy natural language parsing.

    TODO: decide whether we want to import spacy globally - if a user hadn't yet it would be a heavy import
          and there may be things you want to control before that, like tensorflow warning suppression.
          ...though chances are you'll import this helper after that, so it might be fine.

    TODO: cleanup
'''

#import time, json, collections




def reload():
    ' quick and dirty way to save some time reloading during development' 
    import wetsuite.helpers.spacy
    from importlib import reload
    reload( wetsuite.helpers.spacy )



def span_as_doc(span):
    ' unused?  Also, what was its purpose again? '
    return span.as_doc()


class ipython_content_visualisation(object):
    ''' Python notebook visualisation to give some visual idea of contents:
        marks out-of-vocabulary tokens red, and highlight the more interesting words (by POS).
    '''    
    def __init__(self, doc, mark_oov=True, highlight_content=True):
        self.doc = doc
        self.mark_oov = mark_oov
        self.highlight_content = highlight_content

    def _repr_html_(self):
        from wetsuite.helpers.escape import attr, nodetext
        ret = []
        for token in list(self.doc):
            style='padding:1px 4px; outline:1px solid #0002'
            if self.highlight_content: 
                if token.pos_ in ( 'PUNCT','SPACE', 'X',   'AUX','DET','CCONJ',): 
                    style+=';opacity:0.3'
                elif token.pos_ in ( 'ADP', 'VERB', ): 
                    style+=';opacity:0.7'
            if self.mark_oov  and  token.is_oov  and  token.pos_ not in ('SPACE',):
                style+=';background-color:#833'
            ret.append(  '<span title="%s" style="%s">%s</span>'%(  attr(token.pos_)+' '+attr(token.tag_),  style,  nodetext(token.text) )  )
            ret.append('<span>%s</span>'%token.whitespace_ )
        return ''.join(ret)




def interesting_words(span, ignore_stop=True, ignore_pos_=['PUNCT','SPACE','X', 'AUX','DET','CCONJ']):
    ''' Takes a spacy span (or something else that iterates as tokens), 
        returns only the more interesting tokens, ignoring stopwords, function words, and such.

        Note that this will return a regular python array, so you can't use this in e.g. .similar() comparisons
        (using a SpanGroup wouldn't change that?)

        Since spacy makes a point to always keep representing the original input,
        we have to choose to 
        - return the indices - more flexible but more work
        - return only the text - 
        - return a new... something.
        e.g. spangroups   (use weakrefs so when the document gets collected, the returned spangroup breaks)
    '''
    #import spacy
    import spacy.tokens.span_group
    import spacy.tokens.span
    
    docref = span.doc

    ret = [] #spacy.tokens.span_group.SpanGroup(docref)

    for tok in span:
        if ignore_stop and tok.is_stop:
            pass
        elif tok.pos_ in ignore_pos_:
            pass
        elif tok.pos_ in ('NOUN','PROPN','NUM'):
            pass
            ret.append( spacy.tokens.span.Span(docref, tok.i,tok.i+1 ) )
            #print( '1 %s/%s'%(tok.text, tok.pos_) )
        elif tok.pos_ in ('ADJ','VERB','ADP', 'ADV'):
            pass
            ret.append( spacy.tokens.span.Span(docref, tok.i,tok.i+1 ) )
            #print( '2 %s/%s'%(tok.text, tok.pos_) )
        else:
            pass
            #print( '? %s/%s'%(tok.text, tok.pos_) )
    return ret








def subjects_in_doc(doc):
    ''' If sentences are annotated, returns the nominal or clausal subjects for each sentence individually,
        as a list of lists (of Tokens), e.g.
          I am a fish. You are a moose  ->   [ [I ], [You] ]

        If no sentences are annotated, it will return
    '''
    if hasattr(doc, 'sents'): # presumably not all docs hve a .sents?  VERIFY
        return list( (subjects_sentence(sent))  for sent in doc.sents )
    else:
        return list( (subjects_sentence(sent))  for sent in doc.sents )


def subjects_in_span(span):
    ''' For a given span, returns a list of subjects (there can zero, one, or more)

        If given a Doc that means all sentences's. Sometimes that's what you want,
        yet if you wanted them per sentence, see subjects_in_doc.

        Returns a mapping from each subject to related information, e.g.
          Token(she):    { verb:Token(went) }
          Token(Taking): { verb:Token(relax), object:Token(nap), clause:[Token(Taking), Token(a), Token(nap)] }
        You may only be interested in its keys. What's in the values is undecided and may change. 

        Relevant here are
        * nsubj - nominal subject, a non-clausal constituent in the subject position  of an active verb. 
                  A nonclausal consituent with the SBJ function tag is considered a nsubj.

        TODO: actually implement
    '''
    ret = {}
    for tok in span:
        if hasattr(tok, 'tok.dep_'): # maybe warn otherwise?
            if tok.dep_ == 'nsubj':
                pass
            
    return ret







# CONSIDER: a our own prefer_gpu/prefer_cpu that we listen to if and when a function first loads spacy


################################################################################################################
# The rest will decide to load models themselves: CONSIDER: making that more flexible


# CONSIDER: making the following less hardcoded
_dutch = None
def nl_noun_chunks(text):
    ''' Meant as a quick and dirty way to pre-process text for when experimenting with models,
        as a particularly to remove function words

        To be more than that we might use something like spacy's pattern matching

        # CONSIDER: taking a model name, and/or nlp object.
    '''
    global _dutch
    if _dutch is None:
        import spacy
        spacy.prefer_gpu() # TODO: conditional
        #_dutch = spacy.load('nl_core_news_md')
        _dutch = spacy.load('nl_core_news_lg')
    doc = _dutch(text)
    ret=[]
    for nc in doc.noun_chunks:
        ret.append( nc.text )
    return ret


_english = None
def en_noun_chunks(text):
    global _english
    if _english is None:
        import spacy
        spacy.prefer_gpu() # TODO: conditional
        _english = spacy.load('en_core_web_trf')
    doc = _english(text)
    ret=[]
    for nc in doc.noun_chunks:
        ret.append( nc.text )
    return ret


_langdet_model = None
def detect_language(text: str):
    ''' Note that this depends on the spacy_fastlang library, which depends on the fasttext library.
        
        Returns (lang, score)
        - lang string as used by spacy          (xx if don't know)
        - score is an approximated certainty

        Depends on spacy_fastlang and loads it on first call of this function.  Which will fail if not installed.

        CONSIDER: truncate the text to something reasonable to not use too much memory.   On parameter?
    '''
    # monkey patch done before the import to suppress "`load_model` does not return WordVectorModel or SupervisedModel any more, but a `FastText` object which is very similar."
    try: 
        import fasttext   # we depend on spacy_fastlang and fasttext
        fasttext.FastText.eprint = lambda x: None
    except:
        pass

    import spacy_fastlang, spacy
    global _langdet_model
    if _langdet_model == None:
        #print("Loading spacy_fastlang into pipeline")
        _langdet_model = spacy.blank("xx")
        _langdet_model.add_pipe( "language_detector")
        #lang_model.max_length = 10000000 # we have a trivial pipeline, though  TODO: still check its memory requirements
    #else:
    #    print("Using loaded spacy_fastlang")

    doc = _langdet_model(text)

    return doc._.language,  doc._.language_score



_xx_sent_model = None
def sentence_split(text):
    ''' A language-agnostic sentence splitter based on the xx_sent_ud_sm model. 

        If you hacen't installed it:  python3 -m spacy download xx_sent_ud_sm

        Returns a Doc with mainly just the .sents attribute (in case you wanted to feed it into something else TODO: see if that matters)
    '''
    import spacy
    global _xx_sent_model
    if _xx_sent_model==None:
        _xx_sent_model  = spacy.load("xx_sent_ud_sm")
    doc = _xx_sent_model(text)
    return doc



# _xx_ner_model = None
# def test_xx_ner(text):
#     ''' Trying out the xx_ent_wiki_sm NER model '''
#     import spacy
#     global _xx_ner_model
#     if _xx_ner_model==None:
#         _xx_ner_model  = spacy.load("xx_ent_wiki_sm")
#     doc = _xx_ner_model(text)
#     return doc


