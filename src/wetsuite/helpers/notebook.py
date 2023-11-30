#!/usr/bin/python3
''' Tools for jupyter/ipython-style notebooks, and detection that you are, or are _not_, using one right now.
'''
import sys

def detect_env():
    ''' Returns a dict with keys that map to booleans:
        - 'interactive'  - whether it's interactive        
                (e.g. regular python REPL, ipython REPL, notebook, or qtconsole)
        - 'notebook'     - whether it's a notebook         
                (also including colab, qtconsole)
        - 'ipython'      - whether IPython is available    
                (note this will also return True if the module just happens to be installed and available)

        (when we see pytest, we fake all False, because that's probably closer -- probably better than noticing the IPython that pytest seems to mock)
    '''
    ret = {}

    if 'pytest' in sys.modules:  # pytest seems to mock IPython, which confuses the below
        ret['ipython']     = False
        ret['interactive'] = False
        ret['notebook']    = False
        return ret

    try: # probably slightly less nasty than by-classname below
        # pylint ignore because it not being available or not is the thing under test and the point
        import google.colab  # pylint:disable=E0401,E0611,C0415,W0611
        ret['ipython']     = True
        ret['interactive'] = True
        ret['notebook']    = True
        ret['colab']       = True
        return ret
    except Exception: # pylint:disable=W0718
        # certainly ImportError, but maybe also more?
        # CONSIDER: Nothing else that can error out here so keep like this for now?
        pass

    try:
        import IPython # pylint:disable=C0415
        ret['ipython']     = True
        ipyshell = IPython.get_ipython().__class__.__name__
        if ipyshell == 'ZMQInteractiveShell':          # jupyter notebook or qtconsole
            ret['interactive'] = True
            ret['notebook']    = True
        elif ipyshell == 'TerminalInteractiveShell':   # interactive ipython shell
            ret['interactive'] = True
            ret['notebook']    = False
        elif ipyshell == 'NoneType':                   # ipython installed, but this is a regular interactive(?) python shell?  Possibly other cases?
            ret['interactive'] = True
            ret['notebook']    = False
        else:
            raise ValueError("we probably want to understand %r"%ipyshell)

    except ImportError: # no IPython, no notebook, but possibly interactive
        ret['ipython']     = False
        ret['notebook']     = False
        if hasattr(sys, 'ps1'): # see https://stackoverflow.com/questions/2356399/tell-if-python-is-in-interactive-mode
            ret['interactive'] = True   # regular python, interactive
        else:
            ret['interactive'] = False  # regular python, not interactive
    return ret



def is_notebook():
    ' returns whether we are running in a notebook (see detect_env) '
    return detect_env()['notebook']


def is_ipython():
    ' returns whether IPython is available (see detect_env)  -  note that depending on what you are testing, you might want to combine this with is_interactive '
    return detect_env()['ipython']


def is_interactive():
    ' returns whether we are using an interactive thing (see detect_env) '
    return detect_env()['interactive']


def is_ipython_interactive():
    ' return whether this seems to be interactive (in the sense of REPL-ish) '
    env = detect_env()
    return env['ipython'] and detect_env()['interactive']


def progress_bar(maxval, description='', display=True): # , **kwargs
    ''' Wrapper that prefers tqdm, falls back to ipywidgets's IntProgress progress bar.
        
        You can set (and get) .value and .description and they should be shown,
        so e.g. usable like::
            prog = progress_bar( 10, 'overall' )
            for i in range(10):
                prog.value += 1
                time.sleep(1)

        Arguments
          - maximum value (required)
          - optional description
          - if display==True (default), it calls display on the IPython widget, so you don't have to
        You should only call this after you know you are in an ipython environment - e.g. with is_ipython() / is_notebook()
    '''
    try:
        import tqdm.autonotebook  # pylint: disable=C0415
        class TqdmWrap:
            ' make it act enough like the ipywidget, in terms of our description '
            def __init__(self, maxval, description):
                self.tq = tqdm.autonotebook.tqdm( total=maxval, desc=description)
                self._value = 0
                self._description = description

            def set_value(self, val):
                ' setter wrapper (will be part of property decorator) '
                self._value = val
                self.tq.update( 1 ) # self._value

            def get_value(self):
                ' getter wrapper (will be part of property decorator) '
                return self._value

            value = property(get_value, set_value)

            def set_description(self, val):
                ' setter wrapper (will be part of property decorator) '
                self._description = val
                self.tq.desc = self._description

            def get_description(self):
                ' getter wrapper (will be part of property decorator) '
                return self._description

            description = property(get_description, set_description)

        return TqdmWrap(maxval, description)

    except ImportError:
        import IPython.display, ipywidgets 
        prog = ipywidgets.IntProgress(max=maxval, description=description)
        if display:
            IPython.display.display(prog)
        return prog

#class PB:
#    def __init__(self, seq, descr=None):
#        progress_bar( len(seq) )
    





class etree_visualize_selection:
    ''' Produces a colorized representation of selection within an XML document.
        (works only within IPython/jupyter style notebooks,  via a HTML representation.) 
    '''
    def __init__(self, tree, xpath_or_elements, reindent:bool=True, mark_text:bool=True, mark_tail:bool=False, mark_subtree:bool=False):
        ''' Produces a colorized representation of selection within an XML document.
            (works only within IPython/jupyter style notebooks. works via a HTML representation.) 

            Given 
              - a parsed tree    (or a bytes object, will be parsed, but you probably shouldn't do that)
              - either 
                - a sequence of elements from a tree  (that you probably selected yourself)
                - or a string, interpreted as xpath
            ...and optionally:
              - reindent     display reindented copy of the tree (defaults True, this is debug function)
              - mark_text:    mark initial text content of each matched element)
              - mark_tail:    mark tail-text after each matched element)
              - mark_subtree: mark entire tree under each matched element. Useful 

            Mostly used in the tutorials
        '''
        import wetsuite.helpers.etree
        if isinstance(tree, bytes):
            tree = wetsuite.helpers.etree.fromstring( tree )

        if reindent:
            tree = wetsuite.helpers.etree.indent( tree )
        self.tree  = tree
        self.xpath_or_elements = xpath_or_elements
        self.mark_text = mark_text
        self.mark_tail = mark_tail
        self.mark_subtree = mark_subtree


    def _repr_html_(self):
        from wetsuite.helpers.escape import attr#, nodetext
        from lxml.etree import _Comment, _ProcessingInstruction # pylint:disable=E0611
        ret = ['<pre>']

        if isinstance( self.xpath_or_elements, str):
            selection = self.tree.xpath( self.xpath_or_elements )
        else:
            selection = list( self.xpath_or_elements )

        def conditional_highlight(element):
            if element in selection:
                return '<span style="background-color:red; color:white">%s</span>'%(element.tag)
            return '%s'%(element.tag)

        def serialize(element):
            if isinstance(element, _Comment) or isinstance(element, _ProcessingInstruction):
                return

            ret.append('&lt;%s'%(conditional_highlight(element),))
            for ak, av in element.items(): # attributes
                ret.append(' %s="%s"'%(ak, attr(av)))
            ret.append('&gt;')

            if element.text:
                #if self.mark_text and element in selection:
                if (self.mark_text and len(element.text.strip())>0) and element in selection:
                    ret.append('<span style="background-color:#faa; color:black">%s</span>'%element.text)
                else:
                    ret.append(element.text)

            if self.mark_subtree and element in selection:
                ret.append('<span style="background-color:#caa; color:black">')

            for child in element:
                serialize(child)

            if self.mark_subtree and element in selection:
                ret.append('</span>')
            ret.append("&lt;/%s&gt;"% conditional_highlight(element))

            if element.tail:
                #if (self.mark_tail  and len(element.tail.strip())>0)  and  element in selection:
                if self.mark_tail  and  element in selection:
                    ret.append('<span style="background-color:#fab; color:black">%s</span>'%element.tail)
                else:
                    ret.append(element.tail)

        serialize(self.tree)
        ret.append('</pre>')
        return ''.join(ret)



if is_notebook():
    # for debug: make the process easier to recognize for people wondering what's taking so much CPU. 
    # Should probably be in a function, or otherwise conditional, NOT happen globally on import
    try:
        import setproctitle
        setproctitle.setproctitle( 'wetsuite-notebook' )
    except ImportError:
        pass
