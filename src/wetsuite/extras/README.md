# Extras 

Code that is not considered core functionality, and may not be supported, but which you may find use for nonetheless.


## spacy_server

This loads spacy and provides a basi "give me text, here is its parse" service served via HTTP.

This is mostly about the overhead of loading spacy and its models. 
In batch use incurring it once at the stat is fine,
and something similar goes for notebooks,
but when you're in the shell you might want to parse a sentence and not wait for a minute for a model to load (`spacyserver-client` in [clitools/](../clitools/) is the counterpart to use from there).
You _could_ also have this (in)directly public-facing, though note that this scales poorly, less so if you are using GPU.

Not considered part of regular use, because 
  - it's extra dependencies,
  - it returns the parse in a non-standard way, cherry-picking things some to put in JSON
  ...it's nice to have for web interfaces, though, because it can give answers within ~20ms.
