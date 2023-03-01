#!/usr/bin/python3
'''
    Some helpers for ipython-style notebooks - and one function to help detect you are _not_ in one.
'''
import sys

def detect_env():
    ''' Returns a dict with keys:
        - ipython      - whether IPython is available
        - interactive  - whether it's interactive (e.g. notebook, qtconsole, or regular python REPL)
        - notebook     - whether it's a notebook (note: we count qtconsole)
    '''
    ret = {}

    if "pytest" in sys.modules: # pytest seems to mock IPython, which confuses the below
        ret['ipython']     = False 
        ret['interactive'] = False
        ret['notebook']    = False
        return ret
    
    try:
        import IPython
        ret['ipython']     = True
        ipyshell = IPython.get_ipython().__class__.__name__
        if ipyshell == 'ZMQInteractiveShell':          # jupyter notebook or qtconsole
            ret['interactive'] = True
            ret['notebook']    = True
        elif ipyshell == 'TerminalInteractiveShell':   # interactive ipython shell
            ret['interactive'] = True
            ret['notebook']    = False
        else:
            pass
            raise ValueError("we probably want to understand %r"%ipyshell)
    except ImportError:
        if hasattr(sys, 'ps1'): # see https://stackoverflow.com/questions/2356399/tell-if-python-is-in-interactive-mode
            ret['interactive'] = True   # regular python, interactive
        else:
            ret['interactive'] = False  # regular python, not interactive
        ret['ipython']     = False
        ret['notebook']     = False
    return ret


def is_ipython():
    " returns whether we're using IPython (see detect_env) "
    return detect_env()['ipython']


def is_notebook():
    " returns whether we're running in a notebook (see detect_env) "
    return detect_env()['notebook']


def is_interactive():
    " returns whether we're using an interactive thing (see detect_env) "
    return detect_env()['interactive']


def progress_bar(max, description='', display=True, **kwargs):
    ''' Slightly shorter code for using ipywidgets's IntProgress progress bar,
        usable like 
          prog = progress_bar( 10, 'overall' )
          for i in range(10):
              prog.value += 1
              time.sleep(1)

        Arguments
        - you probably just care about the max (required)
        - and probably a description (optional)
        - if display==True (default), it calls display on it so you don't have to
        - anything else is passed through to IntProgress

        You should only call this after you know you are in an ipython environment - e.g. with is_ipython() / is_notebook()
        
        CONSIDER: prefer tqdm if installed, fall back quietly to ipywidgets.IntProgress?
        But then we'd also need to absract out IntProgress's .value= versus tqdm's .update()
    '''
    import IPython.display, ipywidgets 
    prog = ipywidgets .IntProgress(max=max, description=description, **kwargs)
    if display:
        IPython.display.display(prog)
    return prog



if is_notebook():
    # for debug: make the process easier to recognize for people wondering what's taking so much CPU.  Should probably be in a function, though.
    try:
        import setproctitle
        setproctitle.setproctitle( 'wetsuite-notebook' )
    except ImportError:
        pass


#if __name__ == '__main__':
#    print( detect_env() ) # should be three Falses