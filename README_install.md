
## Install and use

Requirements: python3, and a bunch of libraries that  _should_ all be included via setup.py


### Quick experiments
The easiest way to experiment, without installation, is probably notebooks on google colab - go to the [from the `notebook/into` directory](notebooks/intro),
open one that interests you, and click the `Open in colab` that it starts with - this will open that notebook in colabl, and there should be a cell that install the latest wetsuite from this repository.


### Local install
For more serious work probably want a workstation/server install.

as of this writing, the shortest is probably a direct-from-github install:
   pip3 install https://github.com/knobs-dials/wetsuite-dev/archive/refs/heads/main.zip
(We will later start submitting to PyPI so that that becomes `pip3 install wetsuite`)


This installs wetsuite, and the various listed dependencies, into the python environment you're calling it from.
Because complex dependencies may clash with other software, 
you may prefer doing that in a sandboxed environment, such as pipenv,
though if you like to work from notebooks, this is more complex to set up.

TODO: write more text until this becomes fairly obvious and copy-pasteable.


### spacy and GPU
Various example code defaults to the CPU variant of spacy so that it functions everywhere.

If you have a GPU then it is eventually worth using it.
This will requires some fiddling at install time.

For plain spacy (see also its documentation) this comes down to figuring out your environment's CUDA version (on linux see `nvcc -V`), then installing with
  pip install spacy[cuda110]
instead of
  pip install spacy


We try to wrap that dependency in our own naming, so do
  pip install wetsuite[spacy-cuda110]
instead of
  pip install wetsuite

TODO: see if/when we can rely on [cuda-autodetect](https://spacy.io/usage) instead.



## broad package overview

### datasets

Lets you load readymade, provided datasets.


This should be a simple way to get started - whenever data we happen to have made
suits your purposes - datasets can always be more detailed...

Getting started should be as simple:
```
mymodel = dataset.load( 'mymodel' ) # downloads to your home directory the first time
print( mymodel.description )        # should explain how to use that data.
```

TODO: have some URL or document provide an up-to-date summary of current datasets


Currently all datasets are considered preliminary, in the sense that 
- they are unpolished, and may contain errors
  - currently they are there more for "here is a bulk of text to throw at a method or training", not to be a complete set of data


- we have not decided our policies on updating datasets (which would be good to do for expectation management)
  - think about having stable datasets, for things like benchmarking
    maybe "any dataset that has a date is fixed, any other may be updated over time" ?

- we have not decided the data format
  - currently we try to not flatten structured data too much, so is often quite nested
    Data is JSON, intended to be loaded into python objects.
  - think about having simpler datasets, a just_text() per dataset, and/or .txt downloads and such,
    because some people just want plain text to feed to programs





### datacollect

If you need a combination of data that isn't served by an existing dataset,
or more up-to-date than is provided, then you may find code and tools to create, update, and polish a dataset yourself.

Ideally you shouldn't need this, and due warning: this is more manual work, 
and note that it can take a while to fetch all data.

You might try asking us to publish dataset updates.




### extras
Contains things that are not considered core functionality,
that we do not necessarily support,
but may nonetheless be interesting to someone.

This includes 
- playthings like wordcloud
- wrappers around external packages (e.g. ocr, pdf) that ought to make them easier to use

