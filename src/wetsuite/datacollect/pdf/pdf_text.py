' Reads text objects from PDF files ' 
import re


def text_is_mainly_number(s:str):
    ' meant to help ignore serial numbers and such     TODO: move to helpers.string ' 
    nonnum = re.sub('[^0-9.]','',s)
    print([s,nonnum])
    if float(len(nonnum))/len(s) < 0.05:
        return True
    return False



def page_text( filedata:bytes ):
    """ Takes PDF file data.  
        Parses it and yields a page's worth of text at a time (is a generator). 
    """
    import poppler

    pdf_doc = poppler.load_from_data( filedata )
    num_pages = pdf_doc.pages # note that poppler counts pages zero-based

    for page_num in range(num_pages):
        page = pdf_doc.create_page(page_num)
        text_list = page.text_list()
        page_text = []
        for textbox in text_list:
            page_text.append( textbox.text )
        yield ' '.join( page_text )


def count_pages_with_text( filedata_or_list, char_threshold=150 ):
    """ Takes either PDF file data (as bytes) or the output of pages_text()
          counts the number of pages that have a reasonabl amount of text on them.
        Returns (chars_per_page, num_pages_with_text, num_pages)

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
        chars_per_page.append(len(page))
        if len(page) >= char_threshold:
            count_pages_with_text += 1 
    return chars_per_page, count_pages_with_text, count_pages
    


