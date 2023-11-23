import pytest
from wetsuite.datacollect import sru

def test_bunch():
    bwb  = sru.SRUBase(
        base_url='http://zoekservice.overheid.nl/sru/Search',
        x_connection='BWB',
        verbose=True
    )

    bwb.explain()
    bwb.explain(readable=False)

    bwb.explain_parsed()

    with pytest.raises(ValueError, match=r'.*filled.*'):
        bwb.num_records()

    bwb.search_retrieve('dcterms.modified>=2023-11-01',
        start_record=1,
        maximum_records=5)
    assert bwb.num_records() >= 0

    bwb.search_retrieve_many('dcterms.modified>=2023-11-01',
        at_a_time=5,
        start_record=1,
        up_to=5)


def test_extra():
    bwb  = sru.SRUBase(
        base_url='http://zoekservice.overheid.nl/sru/Search',
        x_connection='BWB',
        extra_query='c.product-area==cvdr',
    )

    # that extra_query does not exist in this repo, so:
    with pytest.raises(RuntimeError, match=r'.*Unsupported index.*'):
        bwb.search_retrieve('dcterms.modified>=2023-11-01',1,10)


def _TEMP_DISABLE_test_callback():
    bwb  = sru.SRUBase(
        base_url='http://zoekservice.overheid.nl/sru/Search',
        x_connection='BWB',
    )

    def print_rec(record):
        print( record )

    bwb.search_retrieve(
        'dcterms.modified>=2023-11-01',
        start_record=1,
        maximum_records=5,
        callback=print_rec)

    bwb.search_retrieve_many(
        'dcterms.modified>=2023-11-01',
        at_a_time=1,
        start_record=5, 
        callback=print_rec)

