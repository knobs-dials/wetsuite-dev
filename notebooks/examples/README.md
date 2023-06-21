## Examples

These are python notebooks, which are a relatively visual environment, and you can work on a copy of a notebook to ease some interactive experimentation. 
It also lets us demonstrate code, with annotation.  

Currently these notebooks focus on some specific wetsuite functionality, datasets, and/or explaining some backing techniques.


When you view the notebooks (e.g. here on github) and click the "Open in Colab" link, you will get a copy running in [google colab](https://colab.research.google.com/), which gives you a temporary sandbox in which you can freely play, useful for experimentation and demonstrations without requiring any setup in your own infrastructure - but note, also without long term storage. 

Once you care to use this as a library in more serious projects, consider installing the library onto your own infrastructure.



## Minimal examples


### Search by document type

```python
import wetsuite


```


### Search by keyword (in CVDR)

```python
import wetsuite

result = wetsuite.search(category='cvdr', keywords=['...'], source='Amsterdam')
        # alternative: wetsuite.search(query='IN: cvdr ')

print(result)

for id in result[:10]:
    doc = wetsuite.fetch_document_by(id)
    doc.save('local/path')
    
```


### Extract plain text fragments (from BWB)

```python

# also as an illustration of the Document class



```


### Word cloud (kansspelbeschikkingen)

```python



```



### Kamervragen

```python



```



### Entity extraction (with spaCy)

```python



```
 

### Relation extraction (with spaCy)

```python



```


### OCR


```python



```


### Topic modeling

```python



```

