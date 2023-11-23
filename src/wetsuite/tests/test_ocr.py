import pytest
#import warnings

import wetsuite.extras.ocr

from PIL import Image, ImageDraw



def test_import():
    import wetsuite.extras.ocr
    #wetsuite.extras.ocr.easyocr()


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_image():
    image = Image.new("RGB", (200, 200))
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "Hello from" )
    draw.text((10, 25), "Pillow" )

    bbox_results = wetsuite.extras.ocr.easyocr( image )
    # detected some text
    assert len( bbox_results ) > 0
    assert len( wetsuite.extras.ocr.easyocr_text( bbox_results ) ) > 0

    # test that it doesn't fail
    wetsuite.extras.ocr.easyocr_draw_eval(image, bbox_results)


# TODO: page_extent, doc_extent, page_fragment_filter, probably on a real pdf
