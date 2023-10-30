# Introduction

Wetsuite is a project aimed at easing the application of natural language processing, 
and other analysis, to Dutch and also EU governmental legal data, 
currently largely focused on providing the data and tools and other infrastructure to make it easier for researchers to do so.

NOTE: this is an early repository test to test installs from github, not the primary source of this project.


# What to expect from this project

Core
- Datasets to work on, 
- helper functions to ease some common tasks
- notebooks that introduce data sources, demonstrate our added helpers, demonstrate some common methods 

Plans and extras
- our own searchable index of the data in the datasets, and/or a demonstration how to set up your own
- basic web versions of some common tools, e.g. extracting references
- a better trained Named Entity Recognition for more 



# Repo
This repository is split into:
- [examples](notebooks/) - python notebooks that demonstrate the use of varied package tools,  datasets,  and related things
  - ...things marked 'extras' are not core functionality, there more for showing our work and potentially useful to other programemrs (and includes some demos of cod e in  [extras/ in src](src/wetsuite/extras/))

- [src](src/wetsuite/) - the part of this project that you would install and use.   
  There are more READMEs here detailing parts



# Minimal examples as code fragments

## Datasets
Ideally, data we already provide is a basis for you to go on. 
For example:

### Kamervragen

```python
import wetsuite.datasets, random

kv = wetsuite.datasets.load('kamervragen')

# As  print( kv.description )   will point out,  kv.data  contains a nested structure, so some informed wrangling is necessary:
vraag_document = random.choice( list(kv.data.values()) )
for number in vraag_document['vraagdata']: 
    vraag_n_text,    _ = vraag_document['vraagdata'][number].get('vraag')
    antwoord_n_text, _ = vraag_document['vraagdata'][number].get('antwoord')

    print(  'Q%-5s  %s'%( number, vraag_n_text   )  )
    print(  'A%-5s  %s'%( number, antwoord_n_text)  )
    print('---')
```

See [dataset_kamervragen (notebook)](notebooks/using_dataset_kamervragen.ipynb) for example output, and more on that data.



## Working on text

### Extract plain text fragments (from BWB)
For some broader tasks, where complete but structureless, flat text is enough, there is a dataset. 

Instead, this secion is about wanting more control than that: Laws are of course structured, with paragraphs and lists, 
in an artikel, in a hoofdstuk, and more, and when you want to portion the text by those, or summarize sections, 
or actively use references to such parts, then you need a to understand and use all that structure, 
and probably want more assistance than "Here is the XML (or HTML), good luck".

We aim to let you flatten text with a granularity that you can control, e.g. per article, per hoofdstuk, or otherwise.

And also give an indication to where it came from within the document it came from, 
for the more advanced use of "use the intermediate form to then go interrogate the fully detailed original data".

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

The above relies on some defaults we don't explain in this introduction, also dealing with observed variation in those higher-level layers.
See [datacollect_koop_docstructure_bwb (notebook)](notebooks/extras/extras_datacollect_koop_docstructure_bwb.ipynb) for more explanation
and how to dive in deeper into the details.

We are still considering the balance between more convenient, controllable, and complete, so this code will likely change.



### Entity extraction (with spaCy)
# TODO: 
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
    case_phrases = []  # we try to only get out nouns and noun phrases.  Using all words would go a lot faster  yet would include a lot of empty function words
    for doc_details in case_details['docs']:
        for page in doc_details['pages']:
            for fragment in page['body_text']:
                case_phrases.extend( wetsuite.helpers.spacy.nl_noun_chunks( fragment ) )
    counts = wetsuite.extras.word_cloud.count_normalized( case_phrases, stopwords_i=['de kansspelautoriteit', 'artikel', 'zij','die', 'de'] )
    im = wetsuite.extras.word_cloud.wordcloud_from_freqs( counts )
    display( im )  # display() exists in the context of python notebooks, elsewhere you might e.g.   im.save( '%s.png'%case_details['name'] ) 
```



### Topic modeling

The widest sense of topic modeling is an iterative, interpreting, 
somewhat creative process (unless it's referring to pre-trained labeling).

That said...

```python



```



## Search
Various goverment systems offer live search, in website and/or data form.

Each has its own features, limitations, and idiosyncracies, and potentially their own document structure to deal with.
The most controlled way is often to learn and use each one individually.

We can at least ease that process, with explorations and explanations, and code to ease access.

More effort will be made once we decide the best course of action.

Also, since we have datasets, we provisionally provide a search of those,
as that should at least put a single interface on all data wet put in there.
If there is interest may may later explain how to set up your own.


### Search by keyword (in CVDR)
```python

import pprint, wetsuite.datacollect.koop_repositories, wetsuite.helpers.koop_parse

cvdr = wetsuite.datacollect.koop_repositories.CVDR() # object informed about that backend, and has a search function
for hit_et in cvdr.search_retrieve_many( 'body any visserij', up_to=50 ):
    pprint.pprint(  wetsuite.helpers.koop_parse.cvdr_meta( hit_et, flatten=True )  )
```

See [datacollect_koop_repos (notebook)](notebooks/extras/extras_datacollect_koop_sru_repos.ipynb) for more details.


### Search recent law changes (in BWB)
```python

import pprint, wetsuite.datacollect.koop_repositories, wetsuite.helpers.koop_parse

bwb = wetsuite.datacollect.koop_repositories.BWB()
for hit_et in bwb.search_retrieve_many( 'dcterms.modified >= 2023-03-01', up_to=50 ):
    pprint.pprint( wetsuite.helpers.koop_parse.bwb_searchresult_meta( hit_et ) )
```


## Data collection

Often enough, existing datasets aren't quite enough,
and you will have collect and organize your own.


### PDF
One aspect is that the government is only required to try to give the most machine-readable version they have,
and sometimes the best version is PDFs.

Can we extract the text it says it contains?  You can ask the PDF about the text it says it contains, and often that works:

```python
import wetsuite.helpers.net
import wetsuite.extras.pdf

pdfbytes = wetsuite.helpers.net.download('https://open.overheid.nl/documenten/ronl-5439f4bf9849a53e634389ebbb5e4f5740c4f84f/pdf')
text_per_page = wetsuite.extras.pdf.page_text( pdfbytes )
pprint.pprint(text_per_page)
```

However, it turns out there are many PDFs that (partially or fully) contain _images of text_. To check, you can e.g. 

```python

chars_per_page, num_pages_with_text, num_pages = wetsuite.extras.pdf.count_pages_with_text(pdfbytes, char_threshold=150)
print(f'{num_pages_with_text} out of {num_pages} pages contain reasonable amount of text\n  characters per page: {chars_per_page}')
# which will point out that:
#  7 out of 20 pages contain reasonable amount of text
#    characters per page: [1477, 2699, 707, 602, 2365, 2582, 399, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
```

So in this case, we move on to...

### OCR

```python
import wetsuite.extras.ocr

all_text = wetsuite.extras.oct.easyocr_text( pdfbytes )
```

Notes: 
* this is a shorthand that creates renders the page to an image; you can do that yourself as well
* `easyocr_text()` will _not_ care as much about clean document structure as you do.
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




