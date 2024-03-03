These are command lines tools, things that came in handy during debug and data collection.

You should not _need_ any of this, yet may find a use.








## XML helpers 

Separate helpers scripts that were used mainly to figure out the BWB XMLs's relatively free-form document structure,
and some other explanatory and exploratory uses.  

`xml-color` will pretty-print XML files to the console with colors and options to e.g. remove namespaces

`xml-path-statistics` counts how often each path occurs in an XML file

`xml-text` will print only the text content, as a quick but dirty 'give me some text to play with'

They rely on the wetsuite.helpers.etree module, which makes them slightly specialized,
also in that we have a bunch of namespaces that xml-color prints with our own preferred abbreviation.
