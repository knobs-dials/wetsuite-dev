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


# A set of minimal examples

[some minimal examples](notebooks/intro/some_minimal_examples.ipynb)


# Repo
This repository is split into:
- [examples](notebooks/) - python notebooks that demonstrate the use of varied package tools,  datasets,  and related things
  - ...things marked 'extras' are not core functionality, there more for showing our work and potentially useful to other programemrs (and includes some demos of cod e in  [extras/ in src](src/wetsuite/extras/))

- [src](src/wetsuite/) - the part of this project that you would install and use.   
  There are more READMEs here detailing parts




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




