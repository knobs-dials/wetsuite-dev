# Introduction

Wetsuite is a project aimed at applying natural language processing and other analysis to Dutch and EU governmental legal data,
focusing on providing the data and tools and other infrastructure to make it easier for researchers to do so.


...this, so far, is an early repository test to test installs from github. 

This repository is split into:
- `notebooks` groups - which are introduced below
  - [examples](notebooks/examples/) - python notebooks that demonstrate the use of varied package tools,  datasets,  and related things
  - [miscellany](notebooks/miscellany/) - things that are not core wetsuite functionality, but may be useful to people anyway, including examples of code in [extras/](src/wetsuite/extras/)

- [src](src/wetsuite/) - the part of this project that you would install and use.   
  Has its own [README](src/wetsuite/README.md)



# Minimal examples as code fragments


## Datasets
Ideally, data we already provide is a basis for you to go on. 
For example:

### Kamervragen

```python
import wetsuite.datasets, random

kv = wetsuite.datasets.load('kamervragen')

# As:
print( kv.description )
# will point out,  kv.data  is a nested python structure, so some informed wrangling is necessary:
vraag_document = random.choice( list(kv.data.values()) )
for number in vraag_document['vraagdata']: 
    vraag_n_text,    _ = vraag_document['vraagdata'][number].get('vraag')
    antwoord_n_text, _ = vraag_document['vraagdata'][number].get('antwoord')

    print(  'Q%-5s  %s'%( number, vraag_n_text   )  )
    print(  'A%-5s  %s'%( number, antwoord_n_text)  )
    print('---')
```

See [dataset_kamervragen](notebooks/examples/dataset_kamervragen.ipynb) for more on that data.



## Working on text

### Extract plain text fragments (from BWB)
```python

# also as an illustration of the Document class


```


### Word cloud (kansspelbeschikkingen)
Word clouds are a simple bag-of-words visualisation, yet sometimes 
it is enough to give a basic idea of what a document focuses on.

```python
import wetsuite.datasets, wetsuite.helpers.spacy, wetsuite.extras.word_cloud

ks = wetsuite.datasets.load('kansspelautoriteit')
# again, most lines are wrangling of structured data
for case_details in ks.data[:5]:
    case_phrases = [] # we try to only get out nouns / noun phrases.  Using all words would go a lot faster  yet would include a lot of empty function words
    for doc_details in case_details['docs']:
        for page in doc_details['pages']:
            for fragment in page['body_text']:
                case_phrases.extend( wetsuite.helpers.spacy.nl_noun_chunks( fragment ) )
    counts = wetsuite.extras.word_cloud.count_normalized( case_phrases, stopwords_i=['de kansspelautoriteit', 'artikel', 'zij','die', 'de'] )
    im = wetsuite.extras.word_cloud.wordcloud_from_freqs( counts )
    display( im )  # display() exists in the context of python notebooks, elsewhere you might e.g. do   im.save( '%s.png'%case_details['name'] ) 
```



### Entity extraction (with spaCy)
```python



```
 

### Relation extraction (with spaCy)
```python



```




### Topic modeling

The widest sense of topic modeling is an iterative, interpreting, 
somewhat creative process (unless it's referring to pre-trained labeling).

That said...

```python



```



## Search
Various goverment systems offer live search, in website and/or data form.

Each has its own limitations, features, and idiosyncracies.

Little effort has been made yet to make the interface for each at least somewhat similar and/or pass through data unparsed.
This will be refined later.

Also, since we have datasets, we provisionally provide a search of such,
and if there is interest may may later explain how to set up your own.


### Search by keyword (in CVDR)
```python

import pprint, wetsuite.datacollect.koop_repositories, wetsuite.helpers.koop_parse

cvdr = wetsuite.datacollect.koop_repositories.CVDR()
for hit_et in cvdr.search_retrieve_many( 'body any fish', up_to=50 ):
    pprint.pprint(  wetsuite.helpers.koop_parse.cvdr_meta( hit_et, flatten=True )  )
```

See [datacollect_koop_repos](notebooks/examples/datacollect_koop_repos.ipynb) for more details.


### Search recent law changes (in BWB)
```python

import pprint, wetsuite.datacollect.koop_repositories, wetsuite.helpers.koop_parse

bwb = wetsuite.datacollect.koop_repositories.BWB()
for hit_et in bwb.search_retrieve_many( 'dcterms.modified >= 2023-03-01', up_to=50 ):
    pprint.pprint( wetsuite.helpers.koop_parse.bwb_searchresult_meta( hit_et ) )
```


## Data collection

Often enough, existing datasets aren't quite enough and you will have 
collect and organize some yourself.


### PDF
PDFs are common enough, so we can extract the text it says it contains. 

```python
import wetsuite.helpers.net

pdfbytes = wetsuite.helpers.net.download('https://open.overheid.nl/documenten/ronl-5439f4bf9849a53e634389ebbb5e4f5740c4f84f/pdf')

text_per_page = wetsuite.datacollect.pdf.page_text( pdfbytes )

# However, it turns out there are many PDFs that (partially or fully) contain _images of text_. To check, you can e.g. 
chars_per_page, num_pages_with_text, num_pages = wetsuite.datacollect.pdf.count_pages_with_text(pdfbytes, char_threshold=150)
print(f'{num_pages_with_text} out of {num_pages} pages contain reasonable amount of text\n  characters per page: {chars_per_page}')
# which will point out that:
#  7 out of 20 pages contain reasonable amount of text
#    characters per page: [1477, 2699, 707, 602, 2365, 2582, 399, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
```

So in this case, we move on to...

### OCR

```python
import wetsuite.extras.pdf_text

all_text = wetsuite.extras.pdf_text.pdf_text_ocr( pdfbytes )
```

Note: `pdf_text_ocr()` will not care as much about clean document structure as you do.

It is good enough for bag-of-words models, but a little messy for structured analysis.
See [datacollect_ocr](notebooks/examples/datacollect_ocr.ipynb) 
to get some more insight on why, and how you might improve that.







# More detailed examples as notebooks

[notebooks/examples](notebooks/examples) has python notebooks that lets us demonstrate code, with annotation, and some easier visualisation.  

They should also ease you working on a copy such notebooks to ease some interactive experimentation -- When you view the notebooks (e.g. here on github) and click the "Open in Colab" link, you will get a copy running in [google colab](https://colab.research.google.com/), which gives you a temporary sandbox in which you can freely play, useful for experimentation and demonstrations without requiring any setup in your own infrastructure - but note, also without long term storage. 

Currently these notebooks focus on some specific wetsuite functionality, datasets, and/or explaining some backing techniques.


Once you care to use this as a library in more serious projects, consider installing the library onto your own infrastructure.


- The `dataset_` notebooks are provided for the datasets we provide, usually brief looks at what they even contain, and what the step 2 might be if your step 1 is `wetsuite.datasets.load()`

- The `methods_` notebooks are what about you could do with your data once you have it

- The `datacollect_` notebooks are provided in acknowledgment that we probably won't have made datasets exactly what you want. You can ask us
 are more advanced, 

 and get you started on 

 for code and examples when you want to collect data yourself. They show examples of things like:
  - storing data we fetched 
  - exploring data we fetched earlier
  - how to extact data from well-structured web pages
  - how to apply OCR
  - Some are actually all the code that generated a dataset.
  




