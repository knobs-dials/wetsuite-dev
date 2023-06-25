#!/usr/bin/python3
''' A small WSGI-style app (served via the basic HTTP server - TODO: disentangle out app from that)
    that serves spacy's parsing from a permanent backend, to avoid startup time each time.

    Not considered part of regular use, because 
    - it's extra dependencies,
    - it returns the parse in a non-standard way  (cherry-picking things to put in JSON)
    - it's not necessary in batch use and e.g. most notebooks (it's fine to incur it once)
    ...it's nice to have for web interfaces, though, because it can give answers within ~20ms.

    CONSIDER: rewrite to starlette / uvicorn to host most things on a standalone async thing
              and perhaps try parsing in smaller chunks, sending over websockets
'''

def load_models(models_to_load):
    ''' Takes a list of 3-tuples:
        - language
        - preference of where to load it - 'cpu' or 'gpu'
        - model name
        Returns a list of 4-tuples, which are the first three plus a reference to the spacy model object
    '''
    loaded_models = []
    import spacy
    for lang, cg, model_name in models_to_load:
        if cg=='gpu':
            spacy.require_gpu()
        elif cg=='cpu':
            spacy.require_cpu()
        else:
            raise ValueError("Don't understand preference %r"%cg)
        print("loading %s (%s)"%(model_name, cg))
        try:
            ref = spacy.load(model_name)
            # experiments trying to avoid a memory leak
            #for pipename in ('transformer', 'tagger', 'parser', 'ner'):
            #    if ref.has_pipe(pipename):
            #        ref.get_pipe(pipename).model.attrs['flush_cache_chance'] = 1
            loaded_models.append( (lang, cg, model_name, ref) )
        except OSError:
            print("ERROR: %r probably not installed, you may want to do:   python -m spacy download %s"%(model_name,model_name))
    return loaded_models


def pick_model(loaded_models, lang=None, name=None, fallback=True):
    ''' Given preferences (probably in terms of language, possibly model name)
        and returns the model that is loaded that best fits that.

        The code below mostly just wants one of the right language (in my tests 'nl' or 'en'),
           via language detection 
        
        CONSIDER: implement preference if we have multiple for a language?
    '''
    if name is not None:
        for _,_,model_name, ref in loaded_models:
            if name==model_name:
                return model_name, ref

    if lang is not None:
        for model_lang,_,model_name,ref in loaded_models:
            if model_lang==lang:
                return model_name, ref

    if fallback:
        return loaded_models[0][2], loaded_models[0][3]

    return None,None


if __name__ == '__main__':
    try: # make it clearer in top and nvidia-smi what the process is - if you happen to have this package
        import setproctitle, os, sys
        setproctitle.setproctitle( os.path.basename(sys.argv[0]) )
    except ImportError:
        pass

    import os, sys, threading, json, time, argparse

    from wsgiref.simple_server import make_server
    import paste, paste.request
    import torch
    torch.set_num_threads(1)   # experiments trying to avoid a memory leak
    #import spacy
    import cupy_backends # for underlying exception

    import wetsuite.helpers.spacy
    import wetsuite.helpers.spacyserver
    # note that detect_language implies a dependency on spacy_fastlang


    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model",           action="store",       dest="model",          default="en_core_web_sm",  help="Which model to use.")
    parser.add_argument("-i", "--bind-ip",         action="store",       dest="bind_ip",        default="0.0.0.0",         help="What IP to bind on. Default is all interfaces (0.0.0.0), you might prefer 127.0.0.1")
    parser.add_argument("-p", "--bind-port",       action="store",       dest='bind_port',      default="8282",            help="What port to bind on. Default is 8282.")
    #parser.add_argument("-g", "--prefer-gpu",      action="store_true",  dest="prefer_gpu",     default=False,             help="Whether to try running on GPU (falls back to CPU if it can't).")
    #parser.add_argument("-G", "--require-gpu",     action="store_true",  dest="require_gpu",    default=False,             help="Whether to run on GPU (fails if it can't).")
    #parser.add_argument('-v', "--verbose",         action="count",                              default=0,                 help="debug verbosity (repeat for debug)")
    args = parser.parse_args()
    
    serve_ip = args.bind_ip
    port     = int( args.bind_port )

    models_to_load = [
        ['en','cpu','en_core_web_lg' ], # gpu
        ['nl','cpu','nl_core_news_lg'], # gpu
        #['fr','cpu','fr_core_news_md'],
        #['de','cpu','de_core_news_md'],
    ]
    loaded_models = load_models( models_to_load )

    nlp_lock = threading.Lock() # in case we rewrite for async (CONSIDER: removing until we do)
    
    ## Serve via HTTP
    def application(environ, start_response):
        ' Mostly just calls wetsuite.helpers.spacy.parse, which calls nlp() and returns a json-usable dict.   Single-purpose, ignores path. '
        output, response_headers = [], []

        reqvars  =  paste.request.parse_formvars(environ, include_get_vars=True)
        q        =  reqvars.get('q', None)
        want_svg = (reqvars.get('want_svg', 'n') == 'y')
        #print("want svg: %s"%want_svg)
        
        # if reqvars.get('as_object', 'n') == 'y':
        #     with nlp_lock:
        #         doc = nlp( q )
        #     #start = time.time()
        #     output = [ doc.to_bytes() ]
        #     #print("as_object took %.2fms"%( 1000.*(time.time() - start) ) )
        #     #print("as_object size: %d"%len(output[0]))
        #     status='200 OK'
        #     response_headers.append( ('Content-type',   'application/octet-stream') )
        # elif reqvars.get('as_docbin', 'n') == 'y':
        #     with nlp_lock:
        #         doc = nlp( q )
        #     #start = time.time()
        #     doc_bin = spacy.tokens.DocBin()
        #     doc_bin.add(doc)
        #     output = [ doc_bin.to_bytes() ]
        #     #print("as_docbin took %.2fms"%( 1000.*(time.time() - start) ) )
        #     #print("as_docbin size: %d"%len(output[0]))
        #     status='200 OK'
        #     response_headers.append( ('Content-type',   'application/octet-stream') )
        # elif reqvars.get('as_pickle', 'n') == 'y':
        #     with nlp_lock:
        #         doc = nlp( q )
        #     #start = time.time()
        #     output = [ pickle.dumps(doc) ]
        #     #print("pickle took %.2fms"%( 1000.*(time.time() - start) ) )
        #     #print("pickle size: %d"%len(output[0]))
        #     status='200 OK'
        #     response_headers.append( ('Content-type',   'application/octet-stream') )
        # else:

        # Currently the output is a JSON object
        ret = {} 
        if q in (None,''):
            q = 'You gave us no input.'

        start = time.time()
        #doc = wetsuite.helpers.spacy.sentence_split(q)
        #for sent_span in doc.sents:
        #    sent_text = sent_span.text.strip()
        #    start = time.time()
        lang, score = wetsuite.helpers.spacy.detect_language( q )        # seems to take on the order of 20ms per 100 words
        #    took = time.time() - start
        #    #print("SENTENCE / %3s in %.2fms / %s"%(lang, 1000.*took, sent_text))
        ret['lang_detect_msec'] = '%d'%(1000*(time.time() - start)) 
        
        model_name, nlp = pick_model( loaded_models, lang ) 
        #print("Using %s: %s for this input"%(lang, model_name))

        try:
            # spacyserver.parse() puts the interesting parts of the nlp object in JSON.
            #   this is non-standard and is only understood by some of our own browser code  (also is faster than trying to save/parse as docbin or pickle)
            dic = wetsuite.helpers.spacyserver.parse(nlp=nlp, query_string=q, nlp_lock=nlp_lock, want_svg=want_svg)
            ret.update( dic )
            ret['status'] = 'ok'
        except cupy_backends.cuda.libs.cublas.CUBLASError as e: # seems to inherit directly from builtins.RuntimeError
            ret['status'] = 'error'
            ret['error']  = str(e)
        except RuntimeError as e:   # Probably "CUDA out of memory" (with details)
            ret['status'] = 'error'
            ret['error']  = str(e)

        ret['model'] = model_name
        ret['lang']  = lang

        output = [ json.dumps( ret ).encode('utf8') ]
        
        status='200 OK'
        response_headers.append( ('Content-type',   'application/json') )
        response_headers.append( ('Content-Length', str(sum(len(e) for e in output))) )
        start_response(status, response_headers)
        return output

    server = make_server(serve_ip, port, application)
    print( "  serving" )
    server.serve_forever()

