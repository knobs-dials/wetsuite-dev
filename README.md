NOTE: this is an early repository test to test installs from github, not the primary source of this project.


# Introduction

Wetsuite aims to be a toolset to make it easier for researchers to apply natural language processing and other analysis to legal text,
specifically to Dutch and also EU governmental documents.

It is intended for those not scared of getting in some technical work, yet unsure of where to start.

Other parts of the project provides educational materials to be a gentler introduction to the topic.

This part is focused on providing, data, tools, and other infrastructure, and as such is the more technical part.

The the gentler intruduction on varied topics lies in the notebooks, and arguably it is also the larger contribution in getting people started.
The code as a library, with [some API documentation here](https://wetsuite.knobs-dials.com/apidocs/), is more for the programmers ready to dive in


# What to expect from this project

Core
- Datasets to work on, 
- helper functions to ease some common tasks
- notebooks that 
  - introduce data sources
  - demonstrate our added helpers
  - demonstrate some common methods
  - give some examples of "if you had this question, this is how you might go about solving it"

Plans and extras
- our own searchable index of the data in the datasets, and/or a demonstration how to set up your own
- basic web versions of some common tools, e.g. extracting references
- a better trained Named Entity Recognition for more 


# For the programmers


## What's in the repository

### More detailed examples as notebooks

[notebooks/](notebooks/) has python notebooks that lets us demonstrate code, with annotation, and some easier visualisation.  

* [notebooks/intro](notebooks/intro) should be a gentler introduction, including demonstrations of how to use datasets
  - including some introductory fragments in [some minimal examples](notebooks/intro/wetsuite_minimal_examples.ipynb)
 
* [notebooks/intermediate](notebooks/intermediate) dives a little deeper, e.g. explaining some of the tools to get things done with code on your own

* [notebooks/extras](notebooks/extras) are not core funcionality, and instead are experiments, some cases of showing our work 
  (e.g. some polishing  tuning necessary to create datasets), but not centrally important



# Experiment or install?

### Experiment with notebooks
Notebooks stored here are fairly easy to copy to then play around with,
so that you can do some interactive experimentation without having to worry you're editing our code.

See also [some more technical notes on that, in notebook form](notebooks/intro/technical_notebooks.ipynb).

If you want to avoid installation onto your own PCs at first, consider doing such an experiment on [google colab](https://colab.research.google.com/)
(particularly the intro notebooks have a "Open in Colab" link to ease this).
<!--The easiest way to experiment, without installation, is probably notebooks on google colab - go to the [from the `notebook/into` directory](notebooks/intro),
open one that interests you, and click the `Open in colab` that it starts with - this will open that notebook in colabl, and there should be a cell that install the latest wetsuite from this repository.-->

Once you care to use this as a library in more serious projects, consider installing the library onto your own infrastructure.

<!--
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
-->



### Local install

Requirements: python3, and a bunch of libraries that  _should_ all be included via setup.py



For more serious work probably want a workstation/server install.

as of this writing, the shortest is probably a direct-from-github install:
   pip3 install https://github.com/knobs-dials/wetsuite-dev/archive/refs/heads/main.zip
(We will later start submitting to PyPI so that that becomes `pip3 install wetsuite`)


This installs wetsuite, and the various listed dependencies, into the python environment you're calling it from.
Because complex dependencies may clash with other software, 
you may prefer doing that in a sandboxed environment, such as pipenv,
though if you like to work from notebooks, this is more complex to set up.

TODO: write more text until this becomes fairly obvious and copy-pasteable.


#### Sid enotes: spacy and GPU
Various example code defaults to the CPU variant of spacy so that it functions everywhere.

If you have more than a handful of documents, and a GPU, 
then it becomes interesting to use the GPU for the parts that can use it.


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
