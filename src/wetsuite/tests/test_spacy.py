import pytest

import wetsuite.helpers.spacy
import wetsuite.helpers.metrics

import spacy 
import spacy.tokens.doc
import spacy.tokens.span


def load_nl():
    download_if_necessary("nl_core_news_sm")

def get_model():
    return spacy.blank('nl') # 


def get_simpledoc():
    nlp = get_model()
    doc = spacy.tokens.doc.Doc( vocab=nlp.vocab, words=["Smeer", "de", "zonnebrand"] )
    # this is some rather poor and incomplete mocking
    doc[0].pos_ = 'VERB'
    doc[1].pos_ = 'DET'
    doc[2].pos_ = 'NOUN'
    return doc

def test_parse():
    nlp = get_model()
    for _ in nlp('I like cheese'):
        pass


def test_simpledoc():
    for _ in get_simpledoc():
        pass


def test_reload():
    wetsuite.helpers.spacy.reload()


def test_span_as_doc():
    doc = get_simpledoc()
    assert isinstance( doc, spacy.tokens.doc.Doc )

    span = doc[2:3]
    assert isinstance( span, spacy.tokens.span.Span )
    asdoc = wetsuite.helpers.spacy.span_as_doc(span)

    assert isinstance( asdoc, spacy.tokens.doc.Doc )


def test_ipython_content_visualisation():
    ' for now just test that it does not bork out '
    doc = get_simpledoc()
    wetsuite.helpers.spacy.ipython_content_visualisation(doc)._repr_html_()



# def test_interesting_words():
#     ' for now just test that it does not bork out.   We can mock this one up a bit. '
#     wordlist = wetsuite.helpers.spacy.interesting_words( get_simpledoc() )
#     assert wordlist[0] == 'Smeer'
#     assert wordlist[1] == 'zonnebrand'


# most of the rest needs a real model

# https://stackoverflow.com/questions/56728218/how-to-mock-spacy-models-doc-objects-for-unit-tests

# def test_subjects_in_doc():
#     ' for now just test that it does not bork out '
#     doc = get_simpledoc()
#     wetsuite.helpers.spacy.subjects_in_doc(doc)


# def test_subjects_in_doc():
#     subjects_in_doc

# def test_subjects_in_span():
#     subjects_in_span

# def test_nl_noun_chunks():
#     nl_noun_chunks


# def test_detect_language():
#     detect_language

# def test_sentence_split():
#     test_sentence_split
