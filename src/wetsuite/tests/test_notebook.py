
def test_count_normalized():
    from wetsuite.helpers.notebook import detect_env, is_interactive, is_ipython, is_notebook

    d = detect_env() 
    # from within pytest it's probably...
    assert d['ipython']     == False
    assert d['interactive'] == False
    assert d['notebook']    == False

    assert not is_ipython()
    assert not is_interactive()
    assert not is_notebook()

