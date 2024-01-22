'''
    Lookup of AKN 

'''
# https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_doc_pub.html
# https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_niet-tekst.html

import re

import requests

import wetsuite.helpers.net
import wetsuite.helpers.etree
import wetsuite.helpers.localdata


_akn_cache = None

def cached_resolve(akn, store=None):
    ' like resolve(), but stores results in your user dir, so repeated searches are fast'
    global _akn_cache
    if _akn_cache is None:
        _akn_cache = wetsuite.helpers.localdata.LocalKV('akn_cache.db', key_type=str, value_type=str)

    storeval = _akn_cache.get(akn, missing_as_none=True)
    if storeval is not None:
        return storeval
    else:
        ret = resolve( akn )
        _akn_cache.put( akn, ret )
        return ret


def resolve(akn, timeout=10):
    ''' Resolve a Dutch AKN - currently on https://identifier.overheid.nl/
        @param akn: the AKN string 
        @return: the URL it went to.
    '''
    # both to ensure it's an AKN at all (/akn) and to signal this only does Dutch ones
    if not akn.startswith('/akn/nl'): 
        raise ValueError('The AKN should start with /akn/nl')

    #CONSIDER: think about escaping against injection issues
    resp = requests.get(
        'https://identifier.overheid.nl/'+akn.lstrip('/'),
        allow_redirects=True,
        timeout=timeout,
    )

    if 'identifier.overheid.nl' in resp.url: # didn't resolve
        raise ValueError("AKN did not resolve")
        # could get error from '.form .alert__inner'

    return resp.url


# def resolve(akn):
#     ret = []
#     sakn = re.sub('^/akn','', akn)
#     for d in resolvers:
#         ire = d['IRIregexp']
#         print('matching %r against %r'%(sakn, ire))
#         if re.match(ire, sakn):
#             url = d['Resolver']
#             lookup_url = url+akn
#             print('%r matched %r,\n looking up in %r\n at %s'%(
#                 akn, ire, d['Explanation'], lookup_url
#             ))
#             ret.append( wetsuite.helpers.net.download( lookup_url ) )
#     return ret

# from https://repository.overheid.nl/frbr/cga/resolver/performers/1/json/servers.json
resolvers = [
 #{'Explanation': 'Resolver for Swiss Federal legislation',
 # 'IRIregexp': '/ch[-/]',
 # 'Resolver': 'http://akn.web.cs.unibo.it/ch/chresolver.php?q=',
 # 'sort': '1'},
 #{'Explanation': 'Resolver for Legislation.gov.uk',
 # 'IRIregexp': '/uk[-/]',
 # 'Resolver': 'http://akn.web.cs.unibo.it/uk/ukresolver.php?q=',
 # 'sort': '2'},
 {'Explanation': 'Resolver for OfficialGazette',
  'IRIregexp': '/nl/officialGazette[-/]',
  'Resolver': 'https://repository.overheid.nl/sru?queryType=akn&query=',
  'sort': '3'},
 {'Explanation': 'Resolver for BWB',
  'IRIregexp': '/nl/act/(internationaal|land|koninkrijk)[-/]',
  'Resolver': 'https://identifier.overheid.nl/api/juriconnect/resolver?q=',
  'sort': '4'},
 {'Explanation': 'Resolver for CVDR',
  'IRIregexp': '/nl/act/(provincie|gemeente|waterschap|gr|caropl)[-/]',
  'Resolver': 'https://lokaleregelgeving.overheid.nl/akn-resolver?q=',
  'sort': '5'},
 {'Explanation': 'Resolver for BWB Bevoegd gezag',
  'IRIregexp': '/nl/act/mnre\\d{4}[-/]',
  'Resolvers': ['https://identifier.overheid.nl/api/juriconnect/resolver?q=',
                'https://lokaleregelgeving.overheid.nl/akn-resolver?q='],
  'sort': '6'},
 {'Explanation': 'Resolver for CVDR Bevoegd gezag',
  'IRIregexp': '/nl/act/(gm\\d{4}|pv\\d{2}|ws\\d{4})[-/]',
  'Resolver': 'https://lokaleregelgeving.overheid.nl/akn-resolver?q=',
  'sort': '7'},
 {'Explanation': 'Fallback resolver for akn',
  'IRIregexp': '/nl[-/]',
  'Resolver': 'https://repository.overheid.nl/sru?queryType=akn&query=',
  'sort': '8'}
]
