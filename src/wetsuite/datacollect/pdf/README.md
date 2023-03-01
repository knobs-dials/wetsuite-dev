
# Dealing with PDFs

## Necessities

PDFs consists of objects that often but not necessarily includes text objects.


PDFs are not structured text document, they mostly just specify how to _draw_ text.
Assuming we can pick out all that text, we don't yet know the layout, 
so the quality of text we can extract can vary significantly,
with the way it was entered, the way we use these fragments of text,
wither whether we are detecting things like two-column layouting, footnotes, headers, footers, etc.

Also, some PDFs don't have text as text, but in some font-specific coding that only _renders_
correctly but would not exctract correctly as text. That _also_ means we need to fall back to OCR.


In some cases, PDFs contain no text at all - just images of text, and the best we can do is render them to then apply OCR.

We even found some cases where the first pages are perfectly good text - and at some point it switches to images of text.

In mixed datasets, you might consider to OCR everything, if only because it gives more uniform data to polish.


And we'll want some code 
- to determine when either of these are the case,
- to extract text from PDFs if we can
- to OCR it where we cannot/


This code is not central to our project, but was useful to some of the pilot projects, 
and maybe they are a nice start for someone else.



## Dependencies

* easyocr
  * OCR, multi-language. Not blazingly fast, even on GPU, but seems capable.

* poppler
  * extracts text if present
  * render pages as images (regardless of whether there is extractable text)




# Miscellaneous

## Potentials

And you will have to polish it _anyway_ if you want to be able to do things like 
* layouting - regular word-style documents can have text fragments appended based on coordinates, but e.g. multiple columns take more care
* recognize characters OCR got wrong (particularly structural mistakes we could fix automatically)
* recognize too many or too few spaces (e.g. coming from kerning details)
* combine fragments into sentences, 
* separating paragraphs,
* recognizing and separating/removing headers and footers
* recognize hyphenation between sentences
* recognize and extract tables


When the input is OCR, all of that needs to be done from fragments of text and their positions.

It's one of those problems where it's relative easy to get 80% of the way, 
and the last few percents are a pain.

Ideally, we have an easy way to verify, score, and fix OCR output.

This may involve storing
* Page images (rendered PDF, pre-OCR)
* raw output: fragments with positions
* raw output with metadata e.g. 'probably header'
* plain text with layouting like the original 
* text with




## To look at

* pdftotext (part of Xpdf and Poppler)
  * command line tool, extracts text and considers layouting 

* PDFMiner 
  * TODO: look at

* PyPDF2
  * parses object structure and can extract text. Documentation suggests it is currently relatiely basic.

* unpaper
  * prepares image for OCR, e.g. removing shadow corners common in photographs
  * https://github.com/unpaper/unpaper

* https://pypi.org/project/dehyphen/
  * an its use of perpexity? (and flairNLP?) 

* pytesseract
  * TODO: look at

* TICCL (Text-Induced Corpus Clean-up) / PICCL
  * Statistical word corrector based on a corpus
  * TODO: look at
  https://github.com/LanguageMachines/PICCL

* https://github.com/proycon/tscan


## Unsorted

https://www.clarin.eu/resource-families/tools-normalisation

