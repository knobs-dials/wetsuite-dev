import wetsuite.helpers.abbreviations

def test_form1():
    assert wetsuite.helpers.abbreviations.find_abbrevs( "A Bree Veation (ABV)" ) == [('ABV', ['A', 'Bree', 'Veation'])]  

def test_form2():
    assert wetsuite.helpers.abbreviations.find_abbrevs( "(ABV) A Bree Veation" ) == [('ABV', ['A', 'Bree', 'Veation'])] 

def test_form3():
    assert wetsuite.helpers.abbreviations.find_abbrevs( "ABV (A Bree Veation)" ) == [('ABV', ['A', 'Bree', 'Veation'])]  

def test_form4():
    assert wetsuite.helpers.abbreviations.find_abbrevs( "(A Bree Veation) ABV" ) == [('ABV', ['A', 'Bree', 'Veation'])] 

def test_count():
    parts = [
        wetsuite.helpers.abbreviations.find_abbrevs( "A Bree Veation (ABV) and (ABV) A Bree Veation" ),
        wetsuite.helpers.abbreviations.find_abbrevs( "ABV (A Bree Veation) and (A Bree Veation) ABV" ) 
    ]
    counts = wetsuite.helpers.abbreviations.count_results( parts )  # counts how many documents contain it
    assert counts == {'ABV': {('A', 'Bree', 'Veation'): 2}}
