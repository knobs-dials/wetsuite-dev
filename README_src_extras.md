# Extras 

Code that is not considered core functionality, and may not be guaranteed to work, or supported per se, but which you may find use for nonetheless, particularly in the copy-paste department.


## pdf_text 

Helps extract text that PDFs themselves report having.
Actually a thin layer around [poppler](https://poppler.freedesktop.org/), which you could use directly yourself.

If a PDF actually contains scanned images, you would move on to:

## ocr 

Mostly wraps existing OCR packages (currently just [EasyOCR](https://github.com/JaidedAI/EasyOCR)) 
and tries to you help you extract text.

See [datacollect_ocr.ipynb](../../../notebooks/examples/datacollect_ocr.ipynb) for some basic use examples.


## spacy_server

This loads spacy and provides a basic "give me text, here is its parse" service served via HTTP.

This is mostly about the overhead of loading spacy and its models. 
In batch use incurring it once at the stat is fine,
and something similar goes for notebooks,
but when you're in the shell you might want to parse a sentence and not wait for a minute for a model to load (`spacyserver-client` in [clitools/](../clitools/) is the counterpart to use from there).
You _could_ also have this (in)directly public-facing, though note that this scales poorly, less so if you are using GPU.

Not considered part of regular use, because 
  - it's extra dependencies,
  - it returns the parse in a non-standard way, cherry-picking things some to put in JSON
  ...it's nice to have for web interfaces, though, because it can give answers within ~20ms.