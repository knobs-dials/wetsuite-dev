import os
import pytest
import wetsuite.extras.pdf


def contains_all_of( haystack, needles ):
    for needle in needles:
        if needle not in haystack:
            return False
    return True


def read_eggs():
    import test_pdf
    eggs_filename = os.path.join( 
        os.path.dirname( test_pdf.__file__ ), 
        'eggs.pdf' )

    with open(eggs_filename, 'rb') as f:
        eggs_data = f.read() 

    return eggs_data


def test_page_text():
    pages_text = list( wetsuite.extras.pdf.page_text( read_eggs() ) )

    # pymupdf: ['I am Sam\nDr. Seuss\n1960\nI do not like green eggs and ham.\n1\n']
    # poppler: ['I am Sam Dr. Seuss 1960 I do not like green eggs and ham. 1']
    # we mainly care that it's extracting at all, so be looser:
    assert contains_all_of( pages_text[0], [ "I am Sam", "Dr. Seuss", "I do not like green eggs and ham." ] ) 


def test_page_image_renders_at_all():
    for page_im in wetsuite.extras.pdf.pages_as_images( read_eggs() ):
        # should be around 1241 x 1754
        assert page_im.size[0] > 500

    
    



