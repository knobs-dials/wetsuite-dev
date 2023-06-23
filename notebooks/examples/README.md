
# Minimal examples as code fragments


## Datasets
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

See the [dataset_kamervragen](dataset_kamervragen.ipynb) notebook for more on that data.


## Search

Various goverment systems offer live search, in website and/or data form.

While we try to ease searching these from code, each has its own limitations,
and its own idiosyncracies, which we cannot solve for you.

That said, since we do have and offer data, we do experiment with our own
search of such, and may explain how to build your own.

### Search by keyword (in CVDR)

```python
import wetsuite

TODO: finish

result = wetsuite.datasearch.search(category='cvdr', keywords=['...'], source='Amsterdam')
        # alternative: wetsuite.search(query='IN: cvdr ')

print(result)

for id in result[:10]:
    doc = wetsuite.dataseach.fetch_document_by(id)
    doc.save('local/path')

```

### Search by document type

```python
import wetsuite


```



## Working on text

### Extract plain text fragments (from BWB)

```python

# also as an illustration of the Document class


```

### Word cloud (kansspelbeschikkingen)

World clouds are a _very_ similar bag-of-words visualisation, 
yet sometimes it turns out something as simple as this gives
you an idea of what a document focuses on.

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
See [datacollect_ocr](datacollect_ocr.ipynb) 
to get some more insight on why, and how you might improve that.


### Topic modeling

The widest sense of topic modeling is an iterative, interpreting, 
somewhat creative process (unless it's referring to pre-trained labeling).

That said...

```python



```



# More detailed examples as notebooks

These are python notebooks, which are a relatively visual environment, and you can work on a copy of a notebook to ease some interactive experimentation. 
It also lets us demonstrate code, with annotation.  

Currently these notebooks focus on some specific wetsuite functionality, datasets, and/or explaining some backing techniques.


When you view the notebooks (e.g. here on github) and click the "Open in Colab" link, you will get a copy running in [google colab](https://colab.research.google.com/), which gives you a temporary sandbox in which you can freely play, useful for experimentation and demonstrations without requiring any setup in your own infrastructure - but note, also without long term storage. 

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
  



