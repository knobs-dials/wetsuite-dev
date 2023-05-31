


# CONSIDER: a our own prefer_gpu/prefer_cpu that we listen to if and when a function first loads spacy

_dutch = None
def nl_noun_chunks(text):
    ''' Meant as a quick and dirty way to pre-process text for when experimenting with models,
        as a particularly to remove function words

        To be more than that we might use something like spacy's pattern matching
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

