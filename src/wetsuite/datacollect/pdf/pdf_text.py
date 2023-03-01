' Reads text objects from PDF files ' 
import re


def text_is_mainly_number(s):
    ' meant to help ignore serial numbers and such     TODO: move to helpers.string ' 
    nonnum = re.sub('[^0-9.]','',s)
    print([s,nonnum])
    if float(len(nonnum))/len(s) < 0.05:
        return True
    return False



def page_text( filedata ):
    """ Takes PDF file data.  
        Parses it and yields a page's worth of text at a time. 
    """
    import poppler

    pdf_doc = poppler.load_from_data( filedata )
    num_pages = pdf_doc.pages # zero-based

    for page_num in range(num_pages):
        page = pdf_doc.create_page(page_num)
        text_list = page.text_list()
        page_text = []
        for textbox in text_list:
            page_text.append( textbox.text )
        yield ' '.join( page_text )



