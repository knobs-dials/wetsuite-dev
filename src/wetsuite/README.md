
## Install and use

Requirements: python3. 
And a bunch of libraries


### Quick experiments
The easiest way to experiment, without wotting about installation, is probably notebooks on google colab - open an interesting example [from the `examples` directory](../../examples) and click on `Open in colab`


### Local install
For more serious work probably want a workstation/server install.

as of this writing, the shortest is probably a direct-from-github install:
   pip3 install https://github.com/scarfboy/wetsuite-dev/archive/refs/heads/main.zip
(we will probably start submitting to PyPI so that that becomes `pip3 install wetsuite`)


This installs wetsuite, and the various listed dependencies, into the python environment you're calling it from.
Because complex dependencies may clash with other software, 
you may prefer doing that in a sandboxed environment, such as pipenv,
though if you like to work from notebooks, this is more complex to set up.

TODO: example


#### spacy and GPU
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


