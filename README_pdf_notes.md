
# Dealing with PDFs

## PDFs can be messy

While you may think of PDFs as structured text documents, they aren't that.
Somestimes yes, sometimes no.

They mostly just specify how to draw things. PDFs consists of a stream of objects,
that often but not necessarily ''includes'' "by the way, the text we are drawing says this".


Even if we we can get out that text fairly easily, the more general nature of this PDF stream 
still makes things a little messier than you would think. 

There is quite a bit of variation of what documents contain, and how they contain it:
* When it comes from a word processor, it'll have good text.

* If it comes from scanned images or such, it may have no text objects at all,
  in which case your only option is your own OCR.

* Scanned images may also have some OCRed text added afterwards, which is a still a great start but may be imperfect in multiple ways.

* There are also some cases where it seems to show text perfectly, but there are some internals
  that mean it would not copy/exctract text correctly.
  That _also_ means we need to fall back to your own OCR.


Even assuming we can pick out all that text without mistakes, we don't yet know the layout.
* Headers and footers won't be separated.

* Two-column layout may not come out in reading order.


The point is that the quality of text we can extract can generally vary significantly.



## More practically

How much work there is to be done depends on what you're doing,
just how much require of the text.


If you're only detecting the presence of words, 
e.g. to find documents them by contents,
then text objects of any sort will already go a long way,
and a few lines of code are all you need.


One of the first things we can do fairly easily is detect the "PDF has no text at all" case.

...though we should maybe do that per page, because it turns out there are plen  there are plenty of cases where PDFs are different things appended,
and it's a mix of perfectly good text, and later just images of text.

In mixed datasets, you might consider to OCR everything, if only because while that gives you more data to polish, it is at least more uniform.


If you're studying the sentences in there, you may need to take more care.
And that might be simpler on a specific subset of documents, 
for simple reasons reasons like they come from the same template so are easier to clean up.


## What we have already needed

The above argues that we need to give you code 
- to determine when either of these are the case,

- to extract text from PDFs if we can

- to OCR it where we cannot

- to polish the output of OCR, if that is reasonable


Code doing various of those things was written for one of our pilot projects,
and while it is not central to our project, it might be a nice start for someone else,
and might be developed further later.


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

