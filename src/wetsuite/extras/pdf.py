''' Reads text objects from PDF files 

    If you want clean structured output, 
    then you likely want to put it more work,
    but for a bag-of-words method this may be enough.

    See also pdf_image and ocr

    TODO: consider pymupdf, because it thinks about more details - consider e.g.
    https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-text-in-natural-reading-order


    Render PDF pages as a PIL image.
    Used to feed PDFs that contain scanned images to OCR.
''' 

import warnings, io


# def text_is_mainly_number(s:str):
#     ' meant to help ignore serial numbers and such     TODO: move to helpers.string ' 
#     nonnum = re.sub('[^0-9.]','',s)
#     print([s,nonnum])
#     if float(len(nonnum))/len(s) < 0.05:
#         return True
#     return False


def page_text( filedata:bytes ):
    """ Takes PDF file data, yields a page's worth of its text at a time (is a generator),
        according to the text objects in the PDF stream (which, note, aren't always there).

        Tries to sort the text fragments in reading order,  though this is far from perfect.
    """
    import fitz #pymupdf
    with fitz.open( stream=filedata, filetype="pdf") as document:  # open document
        for page in document:
            yield page.get_text( sort=True )

    # else:
    #     import poppler
    #     pdf_doc = poppler.load_from_data( filedata )
    #     num_pages = pdf_doc.pages # note that poppler counts pages zero-based

    #     for page_num in range(num_pages):
    #         page = pdf_doc.create_page(page_num)
    #         text_list = page.text_list()
    #         page_text = []
    #         for textbox in text_list:
    #             page_text.append( textbox.text )
    #         yield ' '.join( page_text )


def doc_text( filedata:bytes, strip=True ):
    ''' Returns a single string.   Mostly just joins the output of page_text() '''
    ret = '\n\n'.join( page_text( filedata ) )
    if strip:
        ret = ret.strip()
    return ret


def count_pages_with_text( filedata_or_list, char_threshold=200 ):
    """ Counts  the number of pages that have a reasonabl amount of text on them.
        Takes   either PDF file data (as bytes) 
                    or the output of pages_text()
        Returns (chars_per_page, num_pages_with_text, num_pages)

        (The characters per page counts spaces between words, but strips edges; TODO: think about this more)

        Mainly intended to detect PDFs that are partly or fully images-of-text.
    """
    ret = None,None
    if type(filedata_or_list) is bytes:
        it = page_text(filedata_or_list)
    else:
        it = filedata_or_list

    chars_per_page = []
    count_pages = 0
    count_pages_with_text  = 0

    for page in it:
        count_pages += 1
        chars_per_page.append( len(page.strip() ))
        if len(page) >= char_threshold:
            count_pages_with_text += 1 

    return chars_per_page, count_pages_with_text, count_pages


def pdf_text_ocr(bytedata: bytes):
    ''' Takes a PDF and return pageless plain text, entirely with OCR.

        This is currently
        - wetsuite.datacollect.pdf.pages_as_images()
        - wetsuite.extras.ocr.easyocr()
        and is also:
        - slow (might take a minute or two per document) - consider cacheing the result
        - not clever in any way
        so probably ONLY use this if  
        - extracting text objects (e.g. wetsuite.datacollect.pdf.page_text) gave you nothing
        - you only care about what words exist, not about document structure
    '''
    ret = []

    import wetsuite.extras.ocr
    for page_image in pages_as_images(bytedata):
        fragments = wetsuite.extras.ocr.easyocr( page_image )
        for bbox, text_fragment, cert in fragments:
            ret.append( text_fragment )
    return ' '.join( ret )


def pages_as_images( filedata, dpi=150, antialiasing=True ):
    """ Yields one page of the PDF at a time, as a PIL image object.

        A generator because consider what a 300-page PDF would do to RAM use.

        Depends on poppler-utils. CONSIDER: alternatives like pymupdf (page.getpixmap?)
    """
    #pymupdf
    from PIL import Image
    import fitz 

    with fitz.open( stream=filedata, filetype="pdf") as document:
        for page in document:
            page_pixmap = page.get_pixmap(dpi=dpi)
            im = Image.frombytes(mode='RGB', 
                                    size=[page_pixmap.width, page_pixmap.height], 
                                    data=page_pixmap.samples)
            yield im
            
    # else:
    #     import poppler
    #     dpi = int(dpi)
    #     pdf_doc = poppler.load_from_data( filedata )
    #     num_pages = pdf_doc.pages # zero-based
        
    #     pr = poppler.PageRenderer() # I'm not sure the python wrapper can be told to use another pixel format?
        
    #     for page_num in range(num_pages):
    #         page = pdf_doc.create_page(page_num)
            
    #         if antialiasing:
    #             try:
    #                 import poppler.cpp.page_renderer
    #                 pr.set_render_hint( poppler.cpp.page_renderer.render_hint.text_antialiasing, True) 
    #             except Exception as e: # who knows when and why this might break
    #                 warnings.warn('set-antialiasing complained: %s'%str(e))
    #                 pass
    #         poppler_im = pr.render_page( page, xres=dpi, yres=dpi )
    #         pil_im = Image.frombytes( "RGBA",  (poppler_im.width, poppler_im.height), poppler_im.data, "raw", str(poppler_im.format), )
    #         yield pil_im


