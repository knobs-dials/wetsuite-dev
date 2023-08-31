# Introduction

Wetsuite is a project aimed at applying natural language processing and other analysis to Dutch and EU governmental legal data,
focusing on providing the data and tools and other infrastructure to make it easier for researchers to do so.

...this, so far, is an early repository test to test installs from github, not the primary source of this project 


# Minimal examples as code fragments

## Datasets
Ideally, data we already provide is a basis for you to go on. 
For example:

### Kamervragen

```python
import wetsuite.datasets, random

kv = wetsuite.datasets.load('kamervragen')

# As the text in   kv.description   will point out,  kv.data  is a nested structure, so some informed wrangling is necessary:
vraag_document = random.choice( list(kv.data.values()) )
for number in vraag_document['vraagdata']: 
    vraag_n_text,    _ = vraag_document['vraagdata'][number].get('vraag')
    antwoord_n_text, _ = vraag_document['vraagdata'][number].get('antwoord')

    print(  'Q%-5s  %s'%( number, vraag_n_text   )  )
    print(  'A%-5s  %s'%( number, antwoord_n_text)  )
    print('---')
```

See [dataset_kamervragen (notebook)](notebooks/examples/dataset_kamervragen.ipynb) for example output, and more on that data.



## Working on text

### Extract plain text fragments (from BWB)
Laws are of course structured, with paragraphs and lists, in an artikel, in a hoofdstuk, and much more.

When studying details and structures and references you may need to understand and use all that structure, 
yet broader tasks such as summarizing topics of broad parts can probably be fed text without that structure.

We aim to let you flatten text with some controllable granularity, e.g. per article, per hoofdstuk, or otherwise,
and also give an indication to where it came from within the original data-document.

Consider:

```python
import wetsuite.helpers.net, wetsuite.helpers.etree, wetsuite.helpers.koop_parse,  pprint
example_et = wetsuite.helpers.etree.fromstring(     # intentionally a very short example.
    wetsuite.helpers.net.download( 'https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0007878/1996-02-04_0/xml/BWBR0007878_1996-02-04_0.xml' )
)

alinea_dicts = wetsuite.helpers.koop_parse.alineas_with_selective_path( example_et ) # this gives a detailed inbetween state that can be merged in varied ways
merged       = wetsuite.helpers.koop_parse.merge_alinea_data( alinea_dicts ) # th 
pprint.pprint( merged )

#   Gives something like:
# [
#   ([],                  ['Besluit: ',  'Deze regeling zal met de toelichting in de Staatscourant worden geplaatst. ']),
#   ([('artikel', '1')],  ['De door de ondernemers voor het jaar 1996 vastgestelde tarieven worden goedgekeurd. ']),
#   ([('artikel', 'II')], ['Deze regeling treedt in werking met ingang van de tweede dag na dagtekening'
#                          'van de Staatscourant waarin zij wordt geplaatst en werkt terug tot en met 1 januari 1996. '])
#  ]
```

The above relies on some defaults we don't explain here, also dealing with observed variation in those higher-level layers.
See [datacollect_koop_docstructure_bwb (notebook)](notebooks/examples/datacollect_koop_docstructure_bwb.ipynb) for more such details.

We are still considering the balance between more convenient, controllable, and complete, so this code will likely change.



### Entity extraction (with spaCy)
```python



```
 

### Relation extraction (with spaCy)
```python



```


### Word cloud (kansspelbeschikkingen)
Word clouds are a simple [bag-of-words](https://en.wikipedia.org/wiki/Bag-of-words_model)-style visualisation,
yet sometimes it is enough to give a basic idea of what a document focuses on.

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



### Topic modeling

The widest sense of topic modeling is an iterative, interpreting, 
somewhat creative process (unless it's referring to pre-trained labeling).

That said...

```python



```



## Search
Various goverment systems offer live search, in website and/or data form.

Each has its own limitations, features, and idiosyncracies, and potentially document structure.
The most controlled way is often to learn and use each directly.

We can at least ease that process, with explorations and explanations, and code to ease access.
More effort will be made once we decide the best course of action.

Also, since we have datasets, we provisionally provide a search of such,
as that should at least put a single interface on all data wet put in there.
If there is interest may may later explain how to set up your own.


### Search by keyword (in CVDR)
```python

import pprint, wetsuite.datacollect.koop_repositories, wetsuite.helpers.koop_parse

cvdr = wetsuite.datacollect.koop_repositories.CVDR()
for hit_et in cvdr.search_retrieve_many( 'body any fish', up_to=50 ):
    pprint.pprint(  wetsuite.helpers.koop_parse.cvdr_meta( hit_et, flatten=True )  )
```

See [datacollect_koop_repos (notebook)](notebooks/examples/datacollect_koop_repos.ipynb) for more details.


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
See [datacollect_ocr (notebook)](notebooks/examples/datacollect_ocr.ipynb) 
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


# Repository

This repository is split into:
- `notebooks` groups - which are introduced below
  - [examples](notebooks/examples/) - python notebooks that demonstrate the use of varied package tools,  datasets,  and related things
  - [miscellany](notebooks/miscellany/) - things that are not core wetsuite functionality, but may be useful to people anyway, including examples of code in [extras/](src/wetsuite/extras/)

- [src](src/wetsuite/) - the part of this project that you would install and use.   
  Has its own [README](src/wetsuite/README.md)





