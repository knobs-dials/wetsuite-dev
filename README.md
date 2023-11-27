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
  - try some introductory fragments in [some minimal examples](notebooks/intro/wetsuite_minimal_examples.ipynb)
  - ...things marked 'extras' are not core functionality, there more for showing our work and potentially useful to other programemrs (and includes some demos of cod e in  [extras/ in src](src/wetsuite/extras/))

- [src](src/wetsuite/) - the part of this project that you would install and use.   
  There are more READMEs here detailing parts


# More detailed examples as notebooks

[notebooks/](notebooks/) has python notebooks that lets us demonstrate code, with annotation, and some easier visualisation.  

* [notebooks/intro](notebooks/intro) should be a gentler introduction, including demonstrations of how to use datasets

* [notebooks/intermediate](notebooks/intermediate) dives a little deeper, e.g. explaining some of the tools to get things done with code on your own

* [notebooks/extras](notebooks/extras) are experiments, and some cases of showing our work (e.g. some polishing  tuning necessary to create datasets), but not centrally important


One idea behind notebooks are that you can easily create a copy to play around with, so that you can do some interactive experimentation without having to worry you're editing our code.
See also [some more technical notes on that, in notebook form](notebooks/intro/technical_notebooks.ipynb).


And, if you put a copy on [google colab](https://colab.research.google.com/) (particularly the intro notebooks have a "Open in Colab" link to ease this),
you don't even need to install anything on one of your own computers before you can freely play with these.


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



