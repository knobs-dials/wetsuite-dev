''' wrapper for OCR package, currently just EasyOCR.  

    CONSIDER: add tesseract.  
    CONSIDER: ...and then unify the data format we hand around (particularly because of the helper functions)
    TODO: add those helper functions
'''
import sys, re, numpy

from PIL import ImageDraw
import numpy


_eocr_reader = None  # keep in memory to save time when you call it repeatedly

def easyocr(image, pythontypes=True, use_gpu=True):
    ''' Takes PIL image.
       
        Returns EasyOCR's results, which is a list of:
          [[topleft, topright, botright, botleft], text, confidence] 

        Depends on easyocr being installed

        if pythontypes==false, easyocr gives you numpy.int64 in bbox and numpy.float64 for cert,
        if pythontypes==true (default), we make that python int and float

        Will load easyocr's model on the first call, so try to do many calls from a single process 
        to reduce that overhead to just once.

        TODO: pass through kwargs to readtext()
        CONSIDER: fall back to CPU if GPU init fails
    '''
    import easyocr   # https://www.jaided.ai/easyocr/documentation/  https://www.jaided.ai/easyocr/

    global _eocr_reader
    if _eocr_reader is None:
        where = 'CPU'
        if use_gpu:
            where = 'GPU'
        print("first use of ocr() - loading EasyOCR model (into %s)"%where, file=sys.stderr)
        _eocr_reader = easyocr.Reader( ['nl','en'], gpu=use_gpu) 
        #_ocr_reader = easyocr.Reader( ['nl','en'], gpu=False)

    if image.getbands() != 'L': # grayscale
        image = image.convert('L')

    ary = numpy.asarray( image )
    result = _eocr_reader.readtext( ary )   # note: you can hand this a filename, numpy array, or byte stream (PNG or JPG?)

    if pythontypes:
        ret = []
        for bbox, text, cert in result:
            #bbox looks like [[675, 143], [860, 143], [860, 175], [675, 175]]
            # python types from numpy.int64 resp numpy.float64
            #TODO: move that to the easyocr() call
            bbox = list( (int(a),int(b))  for a,b in bbox)
            cert = float(cert)
            ret.append( ( bbox, text, cert) )
        result = ret

    return result


def easyocr_text(results):
    ''' take bounding boxed results and, right now, returns only the text as-is.
        We plan to be smarter than this, given time.

        (there is some smarter code in kansspelautoriteit fetching script)
    '''
    ret = []
    for (topleft, topright, botright, botleft), text, confidence in results:
        ret.append(text)
    return ret
    #return ' '.join(ret)


def easyocr_draw_eval(image, ocr_results):
    ''' Given a PIL image, and the results from ocr(), 
          draws the bounding boxes, with color indicating the confidence, on top of that image and 

        Returns the given PIL image with that drawn on it.

        Made as inspection of how much OCR picks up.
    '''
    image = image.convert('RGB')
    draw = ImageDraw.ImageDraw(image,'RGBA')
    for bbox, text, conf in ocr_results:
        topleft, topright, botright, botleft = bbox
        xy=[tuple(topleft), tuple(botright)]
        draw.rectangle( xy, 
                        outline=10, 
                        fill=( int((1-conf)*255), int(conf*255), 0, 125) 
                      )
    return image
    

#def tesseract():
# #https://github.com/sirfz/tesserocr




# 
# functions that help deal with Easy OCR-detected fragments,
# when they are grouped into pages, then a collection of fragments
# 
# ...and potentially also other OCR and PDF-extracted text streams, once I get to it.
#
# Note: Y origin is on top
#


def bbox_height(bbox):
    topleft, topright, botright, botleft = bbox
    return abs( botright[1] - topleft[1] )

def bbox_width(bbox):
    topleft, topright, botright, botleft = bbox
    return abs( botright[0] - topleft[0] )


def bbox_xy_extent(bbox):
    ' returns min(x), max(x), min(y), max(y) for a single bounding box '
    xs, ys = [], []
    for x,y in bbox:
        xs.append(x)
        ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)

def bbox_min_x(bbox):
    ' redundant with bbox_xy_extent, but sometimes clearer in code '
    topleft, topright, botright, botleft = bbox
    return min( list( x   for x,y in (topleft, topright, botright, botleft) ) )

def bbox_max_x(bbox):
    ' redundant with bbox_xy_extent, but sometimes clearer in code '
    topleft, topright, botright, botleft = bbox
    return max( list( x   for x,y in (topleft, topright, botright, botleft) ) )

def bbox_min_y(bbox):
    ' redundant with bbox_xy_extent, but sometimes clearer in code '
    topleft, topright, botright, botleft = bbox
    return min( list( y   for x,y in (topleft, topright, botright, botleft) ) )

def bbox_max_y(bbox):
    ' redundant with bbox_xy_extent, but sometimes clearer in code '
    topleft, topright, botright, botleft = bbox
    return max( list( y   for x,y in (topleft, topright, botright, botleft) ) )


def page_allxy(page_ocr_fragments):
    ' Returns ( all x list, all y list)  Meant for e.g. statistics use. '
    xs, ys = [], []
    for bbox, text, cert in page_ocr_fragments:
        topleft, topright, botright, botleft = bbox
        for x,y in (topleft, topright, botright, botleft):
            xs.append(x)
            ys.append(y)
    return xs, ys

def page_extent( page_ocr_fragments, percentile_x=(1,99), percentile_y=(1,99) ):
    ''' Estimates the bounds that contain most of the page contents.
        Takes a list of (bbox, text, cert) - the page's.
        considers all bbox x and y coordinates
        Returns a 4-tuple: (page_min_x, page_min_y, page_max_x, page_max_y)
    '''
    xs, ys = page_allxy(page_ocr_fragments)
    #print( xs, numpy.percentile(xs, percentile_x[0]), numpy.percentile(xs, percentile_x[1]))
    #print( ys,  numpy.percentile(ys, percentile_y[0]), numpy.percentile(ys, percentile_y[1]))
    return numpy.percentile(xs, percentile_x[0]), numpy.percentile(xs, percentile_x[1]), numpy.percentile(ys, percentile_y[0]), numpy.percentile(ys, percentile_y[1])
    #return min(xs), min(ys), max(xs), max(ys)


def doc_extent( list_of_page_ocr_fragments ):
    ''' Calls like page_extent(), but considering all page at once,
        mostly to not do weird things on a last half-filled page (though usually there's a footer to protect that)

        Returns a 4-tuple: (page_min_x, page_min_y, page_max_x, page_max_y)

        TODO: think about how percentile logic interacts - it may be more robust to use 0,100 to page_extent calls and do percentiles here.
    '''
    xs, ys = [], []
    #print( list_of_page_ocr_fragments )
    for page_ocr_fragments in list_of_page_ocr_fragments:
        minx, miny, maxx, maxy = page_extent( page_ocr_fragments )
        xs.append(minx)
        xs.append(maxx)
        ys.append(miny)
        ys.append(maxy)
    return min(xs), max(xs), min(ys), max(ys)


def page_fragment_filter( page_ocr_fragments,  textre=None,  q_min_x=None, q_min_y=None, q_max_x=None, q_max_y=None, pages=None, extent=None, verbose=False ):
    ''' Searches for specific text patterns on specific parts of pages.

        Works on all pages at once. This is sometimes overkill, but for some uses this is easier.
        ...in particularly the main one it was written for, trying to find the size of the header and footer to be able to ignore them.

        minx, miny, maxx, maxy restrict where on the page we search. This can be 
        - floats (relative to height and width of text 
          ...present within the page, by default 
          ...or the document, if you hand in the document extent via extent (can make more sense to deal with first and last pages being half filled)
        - otherwise assumed to be ints, absolute units (which are likely to be pixels and depend on the DPI),

        pages is a list of (zero-based) page numbers to include.  None includes all.
    '''
    if extent is not None: # when first and last pages can be odd, it may be useful to pass in the documentation extent
        page_min_x, page_min_y, page_max_x, page_max_y = extent
    else:
        page_min_x, page_min_y, page_max_x, page_max_y = page_extent( page_ocr_fragments )

    if type(q_min_x) is float: # assume it was a fraction
        q_min_x = q_min_x * (1.15*page_max_x) # times a fudge factor because we assume there is right margin that typically has no detected text, and we want this to be a fraction to be of the page, not of the use of the page
    if type(q_max_x) is float:
        q_max_x = q_max_x * (1.15*page_max_x)
    if type(q_min_y) is float:
        q_min_y = q_min_y * page_max_y
    if type(q_max_y) is float:
        q_max_y = q_max_y * page_max_y

    #print( 'minx:%s maxx:%s miny:%s maxy:%s'%(q_min_x, q_max_x, q_min_y, q_max_y ) )

    matches = []
    for frag_i, (bbox, text, cert) in enumerate(page_ocr_fragments):

        if textre is not None: # up here to quieten the 'out of requested bounds' debug
            if re.search( textre, text ):
                if verbose:
                    print( "Text %r MATCHES %r"%(text, textre) )
            else:
                #print( "Text %r NO match to %r"%(textre, text) )
                continue

        frag_min_x, frag_max_x, frag_min_y, frag_max_y = bbox_xy_extent(bbox)

        if q_min_x is not None and frag_min_x < q_min_x:
            if verbose:
                print( "%r min_x %d (%20s) (%20s) is under requested min_x %d"%(text, frag_min_x, bbox, text[:20], q_min_x) )
            continue

        if q_max_x is not None and frag_min_x > q_max_x:
            if verbose:
                print( "%r max_x %d (%20s) (%20s) is over requested max_x %d"%(text, frag_min_x, bbox, text[:20], q_max_x) )
            continue

        if q_min_y is not None and frag_min_y < q_min_y:
            if verbose:
                print( "%r min_y %d (%20s) (%20s) is under requested min_y %d"%(text, frag_min_y, bbox, text[:20], q_min_y) )
            continue

        if q_max_y is not None and frag_min_y > q_max_y:
            if verbose:
                print( "%r max_y %d (%20s) (%20s) is over requested max_y %d"%(text, frag_min_y, bbox, text[:20], q_max_y) )
            continue

        matches.append( (bbox, text, cert) )
    return matches