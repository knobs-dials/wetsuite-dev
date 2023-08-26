''' Render PDF pages as a PIL image.
    Used to feed PDFs that contain scanned images to OCR.
'''
import warnings
from PIL import Image

def pages_as_images( filedata, dpi=150, antialiasing=True ):
    """ Yields one page of the PDF at a time, as a PIL image object.

        A generator because consider what a 300-page PDF would do to RAM use.

        Depends on poppler-utils. CONSIDER: alternatives like pymupdf (page.getpixmap?)
    """
    import poppler
    dpi = int(dpi)
    pdf_doc = poppler.load_from_data( filedata )
    num_pages = pdf_doc.pages # zero-based
    
    pr = poppler.PageRenderer() # I'm not sure the python wrapper can be told to use another pixel format?
    
    for page_num in range(num_pages):
        page = pdf_doc.create_page(page_num)
        
        if antialiasing:
            try:
                import poppler.cpp.page_renderer
                pr.set_render_hint( poppler.cpp.page_renderer.render_hint.text_antialiasing, True) 
            except Exception as e: # who knows when and why this might break
                warnings.warn('set-antialiasing complained: %s'%str(e))
                pass
        poppler_im = pr.render_page( page, xres=dpi, yres=dpi )
        pil_im = Image.frombytes( "RGBA",  (poppler_im.width, poppler_im.height), poppler_im.data, "raw", str(poppler_im.format), )
        yield pil_im
