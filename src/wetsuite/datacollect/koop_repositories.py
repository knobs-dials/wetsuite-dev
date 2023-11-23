#!/usr/bin/python3
'''
An interface to the repositories managed by KOOP (specifically via its SRU API)

Mostly
  - classes that instantiate a usable SRU interface on specific repositories and/or subsets of them
  - helper functions for dealing with specific repository content

Right now, only BWB and CVDR have been used seriously, the rest still needs testing.

See also sru.py
'''

import wetsuite.datacollect.sru


class BWB(wetsuite.datacollect.sru.SRUBase):
    ''' SRU endpoint for the Basis Wetten Bestand repository

        See a description in https://www.overheid.nl/sites/default/files/wetten/Gebruikersdocumentatie%20BWB%20-%20Zoeken%20binnen%20het%20basiswettenbestand%20v1.3.1.pdf
    '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,
                                                  base_url='http://zoekservice.overheid.nl/sru/Search',
                                                  x_connection='BWB',
                                                  verbose=verbose)


class CVDR(wetsuite.datacollect.sru.SRUBase):
    ''' SRU endpoint for the CVDR (Centrale Voorziening Decentrale Regelgeving) repository

        https://www.hetwaterschapshuis.nl/centrale-voorziening-decentrale-regelgeving

        https://www.koopoverheid.nl/voor-overheden/gemeenten-provincies-en-waterschappen/cvdr/handleiding-cvdr
    '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,
                                                  base_url='http://zoekservice.overheid.nl/sru/Search',
                                                  x_connection='cvdr',
                                                  verbose=verbose
                                                  #, extra_query='c.product-area==cvdr' this doesn't work, and x_connection seems to be enough in this case (?)
        )





## Tested for basic function
# ...usually because we have a script that fetches data from it, but we haven't done anything with that data yet so have not dug deeper

class OfficielePublicaties(wetsuite.datacollect.sru.SRUBase):
    " SRU endpoint for the OfficielePublicaties repository "
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,
                                                  base_url='http://repository.overheid.nl/sru',
                                                  x_connection='officielepublicaties',
                                                  extra_query='c.product-area==officielepublicaties',
                                                  verbose=verbose)


class SamenwerkendeCatalogi(wetsuite.datacollect.sru.SRUBase):
    " SRU endpoint for the Samenwerkende Catalogi repository "
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,
                                                  base_url='http://repository.overheid.nl/sru',
                                                  x_connection='samenwerkendecatalogi',
                                                  extra_query='c.product-area==samenwerkendecatalogi',
                                                  verbose=verbose)


class LokaleBekendmakingen(wetsuite.datacollect.sru.SRUBase):
    " SRU endpoint for bekendmakingen repository "
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, 
                                                  base_url='http://repository.overheid.nl/sru',
                                                  x_connection='lokalebekendmakingen', 
                                                  extra_query='c.product-area==lokalebekendmakingen', 
                                                  verbose=verbose)


class StatenGeneraalDigitaal(wetsuite.datacollect.sru.SRUBase):
    ''' SRU endpoint for Staten-Generaal Digitaal repository '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, 
                                                  base_url='https://repository.overheid.nl/sru',
                                                  x_connection='sgd',
                                                  extra_query='c.product-area==sgd',
                                                  verbose=verbose)



## Untested

class Belastingrecht(wetsuite.datacollect.sru.SRUBase):
    ''' test: SRU endpoint for Basis Wetten Bestand, restricted to a specific rechtsgebied (via silent insertion into query)
    '''
    def __init__(self):
        wetsuite.datacollect.sru.SRUBase.__init__(self, 
                                                  base_url='http://zoekservice.overheid.nl/sru',
                                                  x_connection='BWB', 
                                                  extra_query='overheidbwb.rechtsgebied == belastingrecht')


class TuchtRecht(wetsuite.datacollect.sru.SRUBase):
    ''' SRU endpoint for the TuchtRecht repository
   
        https://tuchtrecht.overheid.nl/
    '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, 
                                                  base_url='http://repository.overheid.nl/sru/Search',
                                                  x_connection='tuchtrecht', 
                                                  extra_query='c.product-area==tuchtrecht',
                                                  verbose=verbose)




# Does not seem to do what I think - though I may be misunderstanding it.
class WetgevingsKalender(wetsuite.datacollect.sru.SRUBase):
    ''' SRU endpoint for wetgevingskalender, see e.g. https://wetgevingskalender.overheid.nl/ 
    
        Note: Broken/untested
    '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,
                                                  base_url='http://repository.overheid.nl/sru',
                                                  x_connection='wgk',
                                                  #extra_query='c.product-area any wgk',
                                                  verbose=verbose)


# broken in that the documents URLs it links to will 404 - this seems to be because PLOOI beta led to a half-retraction and redesign?
class PLOOI(wetsuite.datacollect.sru.SRUBase):
    ''' SRU endpoint for the Platform Open Overheidsinformatie repository 

        https://www.open-overheid.nl/plooi/

        https://www.koopoverheid.nl/voor-overheden/rijksoverheid/plooi-platform-open-overheidsinformatie

        Note: Broken/untested
    '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, 
                                                  base_url='http://zoekservice.overheid.nl/sru/Search', 
                                                  x_connection='plooi', 
                                                  verbose=verbose)
        #wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru', x_connection='plooi', verbose=verbose)


class PUCOpenData(wetsuite.datacollect.sru.SRUBase):
    ''' Publicatieplatform UitvoeringsContent
        https://puc.overheid.nl/

        Note: Broken/untested
    '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,
                                                  base_url='http://repository.overheid.nl/sru',
                                                  x_connection='pod', #extra_query='c.product-area==pod',
                                                  verbose=verbose)
        #wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://zoekservice.overheid.nl/sru/Search', x_connection='pod', extra_query='c.product-area==pod', verbose=verbose)


class EuropeseRichtlijnen(wetsuite.datacollect.sru.SRUBase):
    ''' Note: Broken/untested
    '''
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,
                                                  base_url='http://repository.overheid.nl/sru',
                                                  x_connection='eur',
                                                  extra_query='c.product-area any eur',
                                                  verbose=verbose)
