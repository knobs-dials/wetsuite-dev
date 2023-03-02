## broad package overview

### datasets

This should be a simple way to get started with readymade datasets we happen to have made,
which ought to be as simple as:
```
mymodel = dataset.load( 'mymodel' ) # downloads to your home directory the first time
print( mymodel.description )
```


Currently all datasets are considered preliminary, in the sense that they are 
- unpolished and may contain errors
- we have not decided our policies on updating datasets
  - think about having stable datasets, for things like benchmarking
    maybe "any dataset that has a date is fixed, any other may be updated over time" ?

- we have not decided the data format
  - currently we try to not flatten structured data too much, so is often quite nested
    Data is JSON, intended to be loaded into python objects.
  - think about having simpler datasets, a just_text() per dataset, and/or .txt downloads and such,
    because some people just want plain text to feed to programs

- option: store the approximate timeframe a dataset represents


TODO: 
- have some URL or document provide an up-to-date summary of current datasets

- figure out conventions / expectations about provided datasets
    - but no guarantees, particularly while we are deciding what should go into each dataset
  - datasets without a date may be updated over time (but no guarantees how often)
  - we will try to include some -small variants

- figure out hosting of datasets

- figure out whether a dataset should contain code.
  More convenient, but not good security practice. It's probably better to keep that in this repo.

---

Varied datasets are currently there to be a bulk of text e.g. to refine training - and not to be a complete set of data

As such, many have been simplified somewhat . Look in the datacollect directory 


Some datasets aren't linguistic at all, and were made in part because of the types of combination - it's useful to have varied data accessible in one place so you can more easily combine it.


---

There are some pieces of data that are not linguistic yet are useful for specific tasks. 

For example, `gemeente`, which is some metadata per municipality, was useful just for the names, to search beleidsregels per municipality. 
It may also be useful for relations to Provices and Waterschappen, though that could be more structured.
It may also be interesting to link towards CBS areas.




### datacollect
Code mainly used to create aforementioned datasets. 

If you need a combination of data that isn't served by an existing dataset,
or a more up to date set, then you may find code and tools to create, update, and polish a dataset yourself.

Due warning: this is more manual work, 
and does not work out of the box due to requiring a database to cache fetched data.

You might try asking us to publish dataset updates.


### pdf
Deals with extracting text from PDFs, so mostly an extension of datacollect.


### extras
Contains things that are not considered core functionality,
that we do not necessarily support,
but may nonetheless be interesting to someone.

This includes playthings (e.g. wordcloud),
things that are thin wrappers around external packages (e.g. ocr).






## TODO

Currently tested on linux. TODO: windows test

### LONGTERM TODO

