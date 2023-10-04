# datacollect

A collection of scripts and helpers that fetch data from varied sources.


Note that various of these rely on being able to store things into a database (too many objects to handle as files),
and this is not yet genericized, so most scripts are not yet usable without technical knowledge.

The readymade datasets are created using these scripts. 
Consider whether those will suit your needs, even if they will not have the most recent records.


## koop_repositories.py, koop-*

There are over a dozen repositories which share a similar SRU interface for search and retrieval, 
as mentioned in [KOOP's Handleiding SRU 2.0](http://www.google.com/search?q=Handleiding+SRU+site%3Akoopoverheid.nl).

koop_repositories.py helps call into those, assisted by sru.py 

For example uses, see scripts which have a name starting with koop-, and [the example notebook](../../../examples/datacollect_koop_repos.ipynb).


## meta.py

Metadata handling that is not specific to a single resource.

Currently contains parsing of Juriconnect (jci) links.




## XML helpers 

Separate helpers scripts that were used mainly to figure out the BWB XMLs's relatively free-form document structure,
and some other explanatory and exploratory uses.  

`xml-color` will pretty-print XML files to the console with colors and options to e.g. remove namespaces

`xml-path-statistics` counts how often each path occurs in an XML file

`xml-text` will print only the text content, as a quick but dirty 'give me some text to play with'

They rely on the wetsuite.helpers.etree module, which makes them slightly specialized,
also in that we have a bunch of namespaces that xml-color prints with our own preferred abbreviation.










TODO:

* Figure out an interface to easily add datasets:

* register (so that it shows up in list() and can get load()ed)

* fetch example dataset


CONSIDER: 
* separate out raw data 

* parse into form we can reasonably load from disk, so we can 
  for item in dataset_bwb:
      print( item.id, item.text )

* host datasets on github (separate repositories as there's a 5GB limit?)


* having a -example variant part of the code, 
  to allow quick tests before you get serious with more data

* version datasets so that we can have them never change






