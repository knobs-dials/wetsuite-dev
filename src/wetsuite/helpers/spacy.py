

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

