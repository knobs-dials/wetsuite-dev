''' This are convenience functions to go from a PDF file to the text it contains.

    If you want clean structured output, 
    then you likely want to put it more work,
    but for a bag-of-words method this may be enough.
'''

def pdf2txt_embedded(bytedata:bytes):
    ''' Takes a PDF and return pageless plain text, 
        whatever the PDF itself says is there, which, WARNING: may be nothing because it's actually an image.

        Is 90% just wetsuite.datacollect.pdf.
    '''
    import wetsuite.datacollect.pdf
    ret = []
    for page_text in wetsuite.datacollect.pdf.page_text( bytedata ):
        #print( page_text)
        ret.append( page_text )
    return '\n\n'.join(ret)
    

def pdf2txt_ocr(bytedata:bytes):
    ''' Takes a PDF and return pageless plain text, entirely with OCR.

        This is 
        - wetsuite.datacollect.pdf.pages_as_images()
        - wetsuite.extras.ocr.easyocr()
        Also:
        - slow (might take a minute or two per document) - consider cacheing the result
        - not clever in any way
        so probably ONLY use this if  
        - extracting text (e.g. wetsuite.datacollect.pdf.page_text) gave you nothing
        - you only care about what words exist, not about any structure
    '''
    ret = []

    import wetsuite.datacollect.pdf
    import wetsuite.extras.ocr
    for page_image in wetsuite.datacollect.pdf.pages_as_images(bytedata):
        fragments = wetsuite.extras.ocr.easyocr( page_image )
        for bbox, text_fragment, cert in fragments:
            ret.append( text_fragment )
    return ' '.join( ret )