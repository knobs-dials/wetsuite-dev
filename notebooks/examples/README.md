
## Minimal examples as code fragments


### Datasets
#### Kamervragen

```python
import wetsuite.datasets, random

kv = wetsuite.datasets.load('kamervragen')
# kv.data is a nested python structure so some wrangling is required:
vraag_document = random.choice( list(kv.data.values()) )
for number in vraag_document['vraagdata']:
    vraag_n_text, _    = vraag_document['vraagdata'][number].get('vraag')
    antwoord_n_text, _ = vraag_document['vraagdata'][number].get('antwoord')

    print(  'Q%-5s  %s'%( number, vraag_n_text   )  )
    print(  'A%-5s  %s'%( number, antwoord_n_text)  )
    print('---')
```


### Search

#### Search by document type

```python
import wetsuite


```

#### Search by keyword (in CVDR)

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


### Working on text

#### Extract plain text fragments (from BWB)

```python

# also as an illustration of the Document class


```

#### Word cloud (kansspelbeschikkingen)

```python
import wetsuite.datasets, random

ksa = wetsuite.datasets.load('kansspelbeschikkingen')

TODO: finish
```





#### Entity extraction (with spaCy)

```python



```
 

#### Relation extraction (with spaCy)

```python



```


#### OCR

```python
import wetsuite.helpers.net
import wetsuite.extras.pdf2txt

pdfbytes = wetsuite.helpers.net.download('https://open.overheid.nl/documenten/ronl-5439f4bf9849a53e634389ebbb5e4f5740c4f84f/pdf')

text = wetsuite.extras.pdf2txt.pdf2txt_ocr( pdfbytes )
```

Note: while `pdf2txt_ocr()` is good enough for bag-of-words models,
it will not care as much about clean document structure as you do.
See [datacollect_ocr](datacollect_ocr.ipynb) 
to get some more insight on why, and how you might improve that.


#### Topic modeling

The widest sense of topic modeling is an iterative, interpreting, 
somewhat creative process (unless it's referring to pre-trained labeling).

That said...

```python



```



## More detailed examples as notebooks

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
  



