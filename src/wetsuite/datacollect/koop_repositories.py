#!/usr/bin/python3
''' An interface to the SRU API to the repositories managed by KOOP:
    - classes that instantiate a usable SRU interface on specific repositories and/or subsets of them
    - helper functions for dealing with specific repository content

    Right now, only BWB and CVDR have been used seriously, the rest still needs testing.

    See also sru.py
'''

import re, urllib

import wetsuite.datacollect.sru
import wetsuite.datacollect.meta
import wetsuite.helpers.etree


class BWB(wetsuite.datacollect.sru.SRUBase):
    """ SRU endpoint for the Basis Wetten Bestand repository

        See a description in https://www.overheid.nl/sites/default/files/wetten/Gebruikersdocumentatie%20BWB%20-%20Zoeken%20binnen%20het%20basiswettenbestand%20v1.3.1.pdf
    """
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://zoekservice.overheid.nl/sru/Search', 
                                                        x_connection='BWB', verbose=verbose)


class CVDR(wetsuite.datacollect.sru.SRUBase):
    """ SRU endpoint for the CVDR (Centrale Voorziening Decentrale Regelgeving) repository

        https://www.hetwaterschapshuis.nl/centrale-voorziening-decentrale-regelgeving

        https://www.koopoverheid.nl/voor-overheden/gemeenten-provincies-en-waterschappen/cvdr/handleiding-cvdr
    """
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://zoekservice.overheid.nl/sru/Search', 
                                                        x_connection='cvdr', verbose=verbose
                                                        #, extra_query='c.product-area==cvdr' this doesn't work, and x_connection seems to be enough in this case (?)
        )





## Tested for basic function 
# ...usually because we have a script that fetches data from it, but we haven't done anything with that data yet so have not dug deeper

class OfficielePublicaties(wetsuite.datacollect.sru.SRUBase):
    def __init__(self, verbose=False):
        " SRU endpoint for the OfficielePublicaties repository "
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru', 
                                                        x_connection='officielepublicaties', extra_query='c.product-area==officielepublicaties', verbose=verbose)


class SamenwerkendeCatalogi(wetsuite.datacollect.sru.SRUBase):
    " SRU endpoint for the Samenwerkende Catalogi repository '
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self,  base_url='http://repository.overheid.nl/sru', 
                                                        x_connection='samenwerkendecatalogi', extra_query='c.product-area==samenwerkendecatalogi', verbose=verbose)


class LokaleBekendmakingen(wetsuite.datacollect.sru.SRUBase):
    " SRU endpoint for bekendmakingen repository "
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru', 
                                                        x_connection='lokalebekendmakingen', extra_query='c.product-area==lokalebekendmakingen', verbose=verbose)


class StatenGeneraalDigitaal(wetsuite.datacollect.sru.SRUBase):
   """ SRU endpoint for Staten-Generaal Digitaal repository """
   def __init__(self, verbose=False):
       wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='https://repository.overheid.nl/sru', 
                                                      x_connection='sgd', extra_query='c.product-area==sgd', verbose=verbose)



## Untested

class Belastingrecht(wetsuite.datacollect.sru.SRUBase):
    """ test: SRU endpoint for Basis Wetten Bestand, restricted to a specific rechtsgebied (via silent insertion into query)
    """
    def __init__(self):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://zoekservice.overheid.nl/sru', 
                                                        x_connection='BWB', extra_query='overheidbwb.rechtsgebied == belastingrecht')


class TuchtRecht(wetsuite.datacollect.sru.SRUBase):
    """ SRU endpoint for the TuchtRecht repository
   
        https://tuchtrecht.overheid.nl/
    """
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru/Search',
                                                        x_connection='tuchtrecht', extra_query='c.product-area==tuchtrecht', verbose=verbose)


## Broken or untested

# Does not seem to do what I think - though I may be misunderstanding it.
class WetgevingsKalender(wetsuite.datacollect.sru.SRUBase):
    """ SRU endpoint for wetgevingskalender, see e.g. https://wetgevingskalender.overheid.nl/ """
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru',
                                                        x_connection='wgk', 
                                                        #extra_query='c.product-area any wgk', 
                                                        verbose=verbose)


# broken in that the documents URLs it links to will 404 - this seems to be because PLOOI beta led to a half-retraction and redesign?
class PLOOI(wetsuite.datacollect.sru.SRUBase):
    """ SRU endpoint for the Platform Open Overheidsinformatie repository 

        https://www.open-overheid.nl/plooi/

        https://www.koopoverheid.nl/voor-overheden/rijksoverheid/plooi-platform-open-overheidsinformatie
    """
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://zoekservice.overheid.nl/sru/Search', x_connection='plooi', verbose=verbose)
        #wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru', x_connection='plooi', verbose=verbose)


class PUCOpenData(wetsuite.datacollect.sru.SRUBase):
    """ Publicatieplatform UitvoeringsContent
        https://puc.overheid.nl/
    """
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru', x_connection='pod', #extra_query='c.product-area==pod', 
                                                  verbose=verbose)
        #wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://zoekservice.overheid.nl/sru/Search', x_connection='pod', extra_query='c.product-area==pod', verbose=verbose)


class EuropeseRichtlijnen(wetsuite.datacollect.sru.SRUBase):
    def __init__(self, verbose=False):
        wetsuite.datacollect.sru.SRUBase.__init__(self, base_url='http://repository.overheid.nl/sru', 
                                                  x_connection='eur', extra_query='c.product-area any eur', verbose=verbose)




##### Helper functions


def cvdr_meta(tree, flatten=False):
    """ Takes an etree object that is either 
        - a search result's individual record  (in which case we're looking for ./recordData/gzd/originalData/meta
        - CVDR content xml's root              (in which case it's ./meta)
        ...because both contain almost the same metadata almost the same way (the difference is enrichedData in the search results).

        Returns owmskern, owmsmantel, and cvdripm's elements merged into a single dict. 
        If it's a search result, it will also mention the enrichedData.

        Because various elements can repeat - and various things frequently do (e.g. 'source'), each value is a list.

        Because in some cases there are tag-specific attributes, for this reason:
          If flatten==False (default),    returns a dict like 
                                            { 'creator': [{'attr': {'scheme': 'overheid:Gemeente'}, 'text': 'Zuidplas'}], ... }
        For quick and dirty presentation you may wish to smush those into one string:
          If flatten==True,               you get a creatively flattened single string, like 
                                            { 'creator': 'Zuidplas (overheid:Gemeente)', ... }
            Please avoid it when you care to deal with data in a structured way  (even if you can sometimes get away with it due to empty attributs).


        In a lot of cases we care mainly for tagname and text, and there are no attributes, e.g.
          owmskern's    <identifier>CVDR641872_2</identifier>
          owmskern's    <title>Nadere regels jeugdhulp gemeente Pijnacker-Nootdorp 2020</title>
          owmskern's    <language>nl</language>
          owmskern's    <modified>2022-02-17</modified>
          owmsmantel's  <alternative>Nadere regels jeugdhulp gemeente Pijnacker-Nootdorp 2020</alternative>
          owmsmantel's  <subject>maatschappelijke zorg en welzijn</subject>
          owmsmantel's  <issued>2022-02-08</issued>
          owmsmantel's  <rights>De tekst in dit document is vrij van auteursrecht en databankrecht</rights>

        In others you may also care about an attribute or two, e.g.:
          owmskern's    <type scheme="overheid:Informatietype">regeling</type>  (except there's no variation in that value anyway)
          owmskern's    <creator scheme="overheid:Gemeente">Pijnacker-Nootdorp</creator>
          owmsmantel's  <isRatifiedBy scheme="overheid:BestuursorgaanGemeente">college van burgemeester en wethouders</isRatifiedBy>
          owmsmantel's  <isFormatOf resourceIdentifier="https://zoek.officielebekendmakingen.nl/gmb-2022-66747">gmb-2022-66747</isFormatOf>
          owmsmantel's  <source resourceIdentifier="https://lokaleregelgeving.overheid.nl/CVDR641839">Verordening jeugdhulp gemeente Pijnacker-Nootdorp 2020</source>
    """
    ret = {}

    tree = wetsuite.helpers.etree.strip_namespace(tree)
    #print( wetsuite.helpers.etree.tostring(tree).decode('u8') )


    # we want tree to be the node under which ./meta lives
    if tree.find('meta') is not None:
        meta_under = tree 
    else:
        meta_under = tree.find('recordData/gzd/originalData')

        if tree is None:
            raise ValueError("got XML that seems to be neither a document or a search result record")


    enrichedData = tree.find('recordData/gzd/enrichedData')
    if enrichedData is not None: # only appears in search results, not the XML that points to
        for enriched_key, enriched_val in wetsuite.helpers.etree.kvelements_to_dict( enrichedData ).items():
            if enriched_key not in ret:
                ret[enriched_key] = []
            ret[enriched_key].append( {'text':enriched_val, 'attr':{}} ) # imitate the structure the below use

    owmskern   = meta_under.find('meta/owmskern')
    for child in owmskern:
        tagname = child.tag
        if child.text is not None:
            tagtext = child.text
            if tagname not in ret:
                ret[tagname]=[]
            ret[tagname].append( {'text':tagtext, 'attr':child.attrib} )

    owmsmantel = meta_under.find('meta/owmsmantel')
    for child in owmsmantel:
        tagname = child.tag
        tagtext = child.text
        if child.text is not None:
            if tagname not in ret:
                ret[tagname]=[]
            ret[tagname].append( {'text':tagtext, 'attr':child.attrib} )

    cvdripm = meta_under.find('meta/cvdripm')
    for child in cvdripm:
        tagname = child.tag
        text = ''.join( wetsuite.helpers.etree.all_text_fragments( child ) )
        if tagname not in ret:
            ret[tagname]=[]
        ret[tagname].append( {'text':text, 'attr':child.attrib} )

    if flatten:
        simpler = {}
        for meta_key, value_list in ret.items(): # each of the metadata
            simplified_text = []
            for item in value_list:
                text = item['text']
                if item['attr']:
                    for attr_key, attr_val in item['attr'].items(): 
                        text = '%s (%s)'%(text, attr_val)  # this seems to make decent sense half the time (the attribute name is often less interesting)
                simplified_text.append( text )
            simpler[meta_key] = (',  '.join( simplified_text )).strip()
        ret = simpler

    return ret


def cvdr_parse_identifier(text:str):
    """ Given a CVDR style identifier string (sometimes called JCDR), returns a tuple:
        - work ID                                          , without 'CVDR'
        - expression ID  (will be None if it was a work ID), without 'CVDR'
        e.g.
            101404_1      -->  ('101404', '101404_1')
            CVDR101405_1  -->  ('101405', '101405_1')
            CVDR101406    -->  ('101406',  None     )
            1.0:101407_1  -->  ('101407', '101407_1')
    """
    if ':' in text:
        text = text.split(':',1)[1]
    m = re.match('(?:CVDR)?([0-9]+)([_][0-9]+)?', text.replace('/','_'))
    if m is not None:
        work, enum = m.groups()
        if enum==None:
            return work, None
        else:
            return work, work+enum
    else:
        raise ValueError('%r does not look like a CVDR identifier'%text)


def cvdr_param_parse(rest:str):
    """ Picks the parameters from a juriconnect style identifier string.   Used by cvdr_refs.  Duplicates code in meta.py - TODO: centralize that """
    params = {}
    for param in rest.split('&'):
        pd = urllib.parse.parse_qs(param)
        for key in pd:
            val = pd[key]
            print( key, val)
            if key=='artikel':
                val = val.lstrip('artikel.')
            if key not in params:
                params[key] = val
            else:
                params[key].extend( val )
    return params



def cvdr_text(tree):
    """ Given the XML content document as etree object, this is a quick and dirty 'give me mainly the plaintext in it',
        skipping any introductions and such.

        Returns a single string.
          this ic currently a best-effort formatting, where you should e.g. find that paragraphs are split with double newlines.

        This is currently mostly copy-pasted from the bwb code TODO: unify, after I figure out all the varying structure

        TODO: write functions that support "give me flat text for each article separately"
    """
    ret = []
    tree = wetsuite.helpers.etree.strip_namespace( tree )

    body           = tree.find('body')
    regeling       = body.find('regeling')
    regeling_tekst = regeling.find('regeling-tekst')

    identifier = tree.find('meta/owmskern/identifier')

    # TODO: decide on a best way to extract the text from this type of document, and use that in all places it happens

    for artikel in regeling_tekst.getiterator():  # assumes all tekst in these elements, and that they are not nested.  Ignores structure.
        if artikel.tag not in ['artikel', 'enig-artikel', 'tekst', 'structuurtekst']:
            continue

        if artikel.find('lid'):
            aparts = artikel.findall('lid')
        else:
            aparts = [artikel]

        for apart in aparts:
            if apart.get('status') in ('vervallen',):
                break # ?

            text = [] # collected per lid, effectively

            if 1:
                # this is a somewhat awkward way to do it, but may be more robust to unusual nesting                
                for node in apart.getiterator(): 
                    #print( node.tag )
                    if node.tag in ('al', 'table', 'definitielijst'):
                        text.extend( ['\n'] + 
                                     wetsuite.helpers.etree.all_text_fragments( node ) )

                    elif node.tag in ('extref',):
                        text.extend( wetsuite.helpers.etree.all_text_fragments( node ) )

                    elif node.tag in ('titel',):
                        text.extend( wetsuite.helpers.etree.all_text_fragments( node )+[' '] )

                    elif node.tag in ('lid',):
                        text.extend( ['\n'] )

                    elif node.tag in ( # <kop> <label>Artikel</label> <nr>1</nr> <titel>Begripsbepalingen</titel> </kop>
                                      'kop',  'label', 'nr', 
                                      'li',  'lijst',      # we will get its contents
                                      'artikel', 'lid', 'lidnr',
                                      'specificatielijst', 'li.nr','meta-data','tussenkop', 'plaatje', 'adres',):
                        #print("%s IGNORE tag type %r"%(identifier, node.tag))
                        pass
                    else:
                        pass
                        #print("%s UNKNOWN tag type %r"%(identifier, node.tag))
                        #print( wetsuite.helpers.etree.tostring( node ).decode('u8') )

            else:
                for ch in apart.getchildren():
                    if ch.tag in ('lidnr', 'meta-data'):
                        continue

                    if ch.tag == 'lijst':
                        for li in ch.getchildren():
                            for lich in li:
                                if lich.tag in ('al',):
                                    text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                                elif lich.tag in ('lijst',): # we can probably do this a little nicer
                                    text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                                elif lich.tag in ('table',):
                                    text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                                elif lich.tag in ('definitielijst',):
                                    text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                                elif lich.tag in ('specificatielijst',):
                                    pass
                                elif lich.tag in ('li.nr','meta-data',):
                                    pass
                                elif lich.tag in ('tussenkop',):
                                    pass
                                elif lich.tag in ('plaatje',):
                                    pass
                                elif lich.tag in ('adres',):
                                    pass
                                else:
                                    print("%s IGNORE unknown lijst child %r"%(identifier, lich.tag))
                                    print( wetsuite.helpers.etree.tostring(lich).decode('u8') )

                    elif ch.tag in ('al',):
                        text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
                    elif ch.tag in ('al-groep',):
                        text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
                    elif ch.tag in ('table',):
                        text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
                    elif ch.tag in ('definitielijst',):
                        text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )

                    elif ch.tag in ('specificatielijst',):
                        pass
                    elif ch.tag in ('kop','tussenkop',):
                        pass
                    elif ch.tag in ('adres','adreslijst'):
                        pass
                    elif ch.tag in ('artikel.toelichting',):
                        pass
                    elif ch.tag in ('plaatje','formule'):
                        pass
                    elif ch.tag in ('citaat','wetcitaat',):
                        pass
                    else:
                        print( "%s IGNORE unknown lid-child %r"%(identifier, ch.tag) )
                        print( wetsuite.helpers.etree.tostring(ch).decode('u8') )

            #print( text )
            lid_text = (''.join(text)).strip(' ')
            #lid_text = re.sub('\s+',' ', lid_text).strip()
            ret.append( lid_text )

    ret = ('\n'.join(ret)).strip()
    ret = re.sub(r'\n{2,}', '\n\n', ret)
    return ret


def cvdr_sourcerefs(tree): 
    ''' Given the XML content document as an etree object, looks for the <source> tags, which are references to laws and other regulations (VERIFY)
    
        The references seem to be more convention-based than standardized.

        This exists in part to normalize it a bit - yet this is more creative than a helper function probably should be.
    '''
    ret = []
    tree = wetsuite.helpers.etree.strip_namespace(tree)
    owmsmantel = tree.find('meta/owmsmantel')
    for source in owmsmantel.findall('source'):
        resourceIdentifier = source.get('resourceIdentifier')
        source_text        = source.text

        if source_text is None:
            continue

        source_text = source_text.strip()
        if len(source_text)==0:
            continue

        if resourceIdentifier.startswith('CVDR://') or 'CVDR' in resourceIdentifier:
            orig = resourceIdentifier
            if resourceIdentifier.startswith('CVDR://'):
                resourceIdentifier = resourceIdentifier[7:]
            parsed = cvdr_parse_identifier(resourceIdentifier)
            specref = parsed[1]
            if specref is None:
                specref = parsed[0]
            ret.append( ('CVDR', orig, specref, None, source_text) )

            #print( '%r -> %r'%(orig, parsed ))


        elif resourceIdentifier.startswith('BWB://'):
            # I've not found its definition, probably because there is none, but it looks mostly jci?
            # BWB://1.0:r:BWBR0005416
            # BWB://1.0:c:BWBR0008903&artikel=12&g=2011-11-08
            # BWB://1.0:v:BWBR0015703&artikel=art. 30              which is messy
            m = re.match('(?:jci)?([0-9.]+):([a-z]):(BWB[RV][0-9]+)(.*)', resourceIdentifier)
            if m is not None:
                version, typ, bwb, rest = m.groups()
                params = cvdr_param_parse(rest)
                ret.append( ('BWB', resourceIdentifier, bwb, params, source_text) )
                #print( 'BWB://-style   %r  %r'%(bwb, params) )

        elif resourceIdentifier.startswith('http://') or resourceIdentifier.startswith('https://'):
            # http://wetten.overheid.nl/BWBR0013016
            # http://wetten.overheid.nl/BWBR0003245/geldigheidsdatum_19-08-2009
            
            m = re.match('https?://wetten.overheid.nl/(BWB[RV][0-9]+)(/.*)?', resourceIdentifier)
            if m is not None:
                bwb, rest = m.groups()
                params={}
                if rest is not None:
                    params =  cvdr_param_parse(rest)
                #print("http-wetten: %r %r"%(bwb, params))
                ret.append( ('BWB', resourceIdentifier, bwb, params, source_text) )

            #else:
            #    print("http-UNKNOWN: %r"%(resourceIdentifier), file=sys.stderr)
            #
            #
            # though also includes things that are specific but don't look like it, e.g.
            #   http://wetten.overheid.nl/cgi-bin/deeplink/law1/title=Gemeentewet/article=255
            # actually redirects to 
            #   https://wetten.overheid.nl/BWBR0005416/2022-08-01/#TiteldeelIV_HoofdstukXV_Paragraaf4_Artikel255
            #
            # or completely free-form, like the following (which is a broken link)
            #   http://www.stadsregioamsterdam.nl/beleidsterreinen/ruimte_wonen_en/wonen/regelgeving_wonen

        elif resourceIdentifier.startswith('jci') or 'v:BWBR' in resourceIdentifier or 'c:BWBR' in resourceIdentifier:
            try:
                d = wetsuite.datacollect.meta.parse_jci( resourceIdentifier )
            except ValueError as ve:
                #print("ERROR: bad jci in %r"%ve, file=sys.stderr)
                continue
            bwb, params = d['bwb'], d['params']
            #print("JCI: %r %r"%(bwb, params))
            ret.append( ('BWB', resourceIdentifier, bwb, params, source_text) )

        else:
            pass
            #if len(resourceIdentifier.strip())>0:
            #    print( 'UNKNOWN: %r %r'%(resourceIdentifier, source_text), file=sys.stderr )
            #    #print( wetsuite.helpers.etree.tostring(source) )
    return ret


# def cvdr_toelichting(tree):
#     ''' Annoyingly, toelichting can be either in regeling/nota-toelichting
#         or just be bijlage content 
#         TODO: also deal with the latter
#     '''
#     nota_toelichting = tree.find('body/regeling/nota-toelichting')
#     ret = wetsuite.helpers.etree.all_text_fragments( nota_toelichting )
#     return ('\n\n'.join(ret)).strip()
# 
#     #bijlage = tree.find('body/regeling/bijlage')


def bwb_title_looks_boring(text):
    ' Give title text, estimate whether the content has much to say '
    text = text.lower()
    for boringizing_substring in [
        'veegwet', 'wijzigingswet', 'herzieningswet', 'aanpassingswet', 'aanpassings- en verzamelwet', 'reparatiewet', 'overige fiscale maatregelen', 
          'evaluatiewet', 'intrekkingswet', 'verzamelwet', 'invoeringswet', 'tijdelijke', 'overgangswet',
        'aanpassingsbesluit', 'wijzigingsbesluit', 'wijzigingsregeling',
        'tot wijziging', # not always 
        'tot aanpassing', 
        'tot herziening',
        #'tot vaststelling'  not actually, just figuring out the language
            ]:
        if re.search(r'\b%s\b'%boringizing_substring, text):
            return True
    return False



def bwb_searchresult_meta(record): # TODO: rename bwb_meta to this in files
    ' takes individual SRU result record as an etree subtrees, and picks out BWB-specific metadata (merging the separate metadata sections) '
    record = wetsuite.helpers.etree.strip_namespace( record )

    #recordSchema   = record.find('recordSchema')      # e.g. <recordSchema>http://standaarden.overheid.nl/sru/</recordSchema>
    #recordPacking  = record.find('recordPacking')     # probably <recordPacking>xml</recordPacking>
    recordData     = record.find('recordData')        # the actual record 
    recordPosition = record.find('recordPosition')    # e.g. <recordPosition>12</recordPosition>
    payload = recordData[0]
    #print( etree.ElementTree.tostring( payload, encoding='unicode' ) )

    originalData = payload.find('originalData')
    owmskern     = wetsuite.helpers.etree.kvelements_to_dict( originalData.find('meta/owmskern')   )
    owmsmantel   = wetsuite.helpers.etree.kvelements_to_dict( originalData.find('meta/owmsmantel') ) 
    bwbipm       = wetsuite.helpers.etree.kvelements_to_dict( originalData.find('meta/bwbipm')     ) 
    enrichedData = wetsuite.helpers.etree.kvelements_to_dict( payload.find('enrichedData') )

    merged = {}
    merged.update(owmskern)
    merged.update(owmsmantel)
    merged.update(bwbipm)
    merged.update(enrichedData)

    return merged


def bwb_toestand_usefuls(tree):
    ''' Fetch interesting metadata from parsed toestand XML.    TODO: finish '''
    ret = {}
    wetgeving = tree.find('wetgeving') # TODO: also allow the alternative roots
    ret['intitule']               = wetgeving.findtext('intitule')
    ret['citeertitel']            = wetgeving.findtext('citeertitel')
    ret['soort']                  = wetgeving.get('soort')
    ret['inwerkingtredingsdatum'] = wetgeving.get('inwerkingtredingsdatum')
    # this might contain nothing we can't get better in wti or manifest?
    #wetgeving_metadata = wetgeving.find('meta-data')
    return ret


def bwb_wti_usefuls(tree):
    ''' Fetch interesting  metadata from parsed WTI XML.    
        TODO: finish, and actually do it properly -- e.g. look to the schema as to what may be omitted, may repeat, etc.
    '''
    ret = {} 
    tree = wetsuite.helpers.etree.strip_namespace(tree)

    # root level has these four
    algemene_informatie      = tree.find('algemene-informatie')
    gerelateerde_regelgeving = tree.find('gerelateerde-regelgeving')
    wijzigingen              = tree.find('wijzigingen')
    owms_meta                = tree.find('meta')


    ### algemene_informatie ###########################################################################################
    ret['algemene_informatie'] = {}

    ret['algemene_informatie']['citeertitels'] = []
    citeertitels = algemene_informatie.find('citeertitels')
    if citeertitels is not None:
        for citeertitel in citeertitels:
            ret['algemene_informatie']['citeertitels'].append( (citeertitel.get('geldig-van'), citeertitel.get('geldig-tot'), citeertitel.text) )

    # TODO: similar for niet-officiele-titels

    for name in ('eerstverantwoordelijke', 'identificatienummer'):
        ret['algemene_informatie'][name] = algemene_informatie.findtext(name)

    ret['algemene_informatie']['rechtsgebieden'] = []
    for rechtsgebied in algemene_informatie.find('rechtsgebieden'):
        ret['algemene_informatie']['rechtsgebieden'].append( (rechtsgebied.findtext('hoofdgebied'), rechtsgebied.findtext('specifiekgebied')) )

    ret['algemene_informatie']['overheidsdomeinen'] = []
    for overheidsdomein in algemene_informatie.find('overheidsdomeinen'):
        ret['algemene_informatie']['overheidsdomeinen'].append( overheidsdomein.text )


    ### gerelateerde_regelgeving ######################################################################################
    ret['related'] = []
    for gnode in gerelateerde_regelgeving.find('regeling'):
        gname = gnode.tag
        for grel in gnode:
            bwbid = grel.get('bwb-id')
            extref = grel.find('extref')
            if extref is not None: # TODO: figure out why that happens
                ret['related'].append( (gname, bwbid, extref.get('doc'), extref.text))
    # TODO: parse the similar regelingelementen


    ### wijzigingen ###################################################################################################
    ret['wijzigingen'] = []
    for datum in wijzigingen.find('regeling'): 
        wijziging = {}

        wijziging['waarde'] = datum.get('waarde') # e.g. 1998-01-01
        details = datum.find('details') # contains e.g. betreft, ontstaansbron
        wijziging['betreft'] = details.findtext('betreft') # e.g. nieuwe-regeling, wijziging, intrekking-regeling
        
        ontstaansbron = details.find('ontstaansbron')
        bron = ontstaansbron.find('bron')

        wijziging['ondertekening'] = bron.findtext('ondertekening')

        bekendmaking = bron.find('bekendmaking') # apparently the urlidentifier, that should be something like stb-1997-581, is sometimes missing
        if bekendmaking is not None:
            wijziging['bekendmaking'] = ( bekendmaking.get('soort'), bekendmaking.findtext('publicatiejaar'), bekendmaking.findtext('publicatienummer') )  

        wijziging['dossiernummer'] = bron.findtext('dossiernummer')

        ret['wijzigingen'].append( wijziging )

    # TODO: also parse the similar regelingelementen

    ### owms-meta ###################################################################################################
    owms_kern      = owms_meta.find('kern')
    for node in owms_kern: # TODO: check with schema this is actually flat and there are no dupe tags (there probably are)
        ret[ node.tag ] = node.text
    return ret


def bwb_manifest_usefuls(tree):
    ''' Fetch interesting metadata from manifest WTI XML.    TODO: finish '''
    ret = {'expressions':[]}
    #metadata = tree.find('metadata')
    for expression in tree.findall('expression'):
        ex = {'manifestations':[]}
        for node in expression.find('metadata'):
            ex[ node.tag ] = node.text

        for manifestation in expression.findall('manifestation'):
            #hashcode = manifestation.findtext('metadata/hashcode')
            #size     = manifestation.findtext('metadata/size')
            label    = manifestation.find('item').get('label')
            ex['manifestations'].append( label )

        ret['expressions'].append( ex )
        
    #datum_inwerkingtreding
    return ret


def bwb_merge_usefuls(toestand_usefuls=None, wti_usefuls=None, manifest_usefuls=None):
    ''' Merge the result of the above, into a flatter structure '''
    merged = {}

    if wti_usefuls is not None:
        merged.update( wti_usefuls['algemene_informatie'] )
        for k in wti_usefuls:
            if k not in ('algemene_informatie',):
                merged[k] = wti_usefuls[k]

    #if manifest_usefuls is not None:
    #    merged.update( manifest_usefuls )

    if toestand_usefuls is not None:
        merged.update( toestand_usefuls )

    merged.update( toestand_usefuls )
    #merged.update( meta['manifest'] )

    return merged


def bwb_toestand_text(tree):
    ''' Given the document, this is a quick and dirty 'give me mainly the plaintext in it',
        skipping any introductions and such.

        Not structured data, intended to assist generic "how do these setences parse" code

        TODO: 
        * review this, it makes various assumptions about document structure
        * review the handling of certain elements, like lijst, table, definitielijst

        * see if there are contained elements to ignore, like maybe <redactie type="vervanging"> ?

        * generalize to have a parameter ignore_tags=['li.nr', 'meta-data', 'kop', 'tussenkop', 'plaatje', 'adres', 'specificatielijst', 'artikel.toelichting', 'citaat', 'wetcitaat']
    '''
    ret=[]

    bwb_id = tree.get('bwb-id')    # only used in debug
    wetgeving = tree.find('wetgeving')
    soort = wetgeving.get('soort') # only used in debug
    for artikel in wetgeving.getiterator():  # assumes all tekst in these elements, and that they are not nested.  Ignores structure.
        if artikel.tag not in ['artikel', 'enig-artikel', 'tekst', 'structuurtekst']:
            continue

        if artikel.find('lid'):
            aparts = artikel.findall('lid')
        else:
            aparts = [artikel]

        for apart in aparts:
            if apart.get('status') in ('vervallen',):
                break

            text = [] # collected per lid, effectively
            for ch in apart.getchildren():
                if ch.tag in ('lidnr', 'meta-data'):
                    continue


                if ch.tag == 'lijst':
                    for li in ch.getchildren():
                        for lich in li:
                            if lich.tag in ('al',):
                                text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                            elif lich.tag in ('lijst',): # we can probably do this a little nicer
                                text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                            elif lich.tag in ('table',):
                                text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                            elif lich.tag in ('definitielijst',):
                                text.extend( wetsuite.helpers.etree.all_text_fragments( lich ) )
                            elif lich.tag in ('specificatielijst',):
                                pass
                            elif lich.tag in ('li.nr','meta-data',):
                                pass
                            elif lich.tag in ('tussenkop',):
                                pass
                            elif lich.tag in ('plaatje',):
                                pass
                            elif lich.tag in ('adres',):
                                pass
                            else:
                                print("%s/%s IGNORE unknown lijst child %r"%(bwb_id, soort, lich.tag))
                                print( wetsuite.helpers.etree.tostring(lich).decode('u8') )

                elif ch.tag in ('al',):
                    text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
                elif ch.tag in ('al-groep',):
                    text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
                elif ch.tag in ('table',):
                    text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )
                elif ch.tag in ('definitielijst',):
                    text.extend( wetsuite.helpers.etree.all_text_fragments( ch ) )

                elif ch.tag in ('specificatielijst',):
                    pass
                elif ch.tag in ('kop','tussenkop',):
                    pass
                elif ch.tag in ('adres','adreslijst'):
                    pass
                elif ch.tag in ('artikel.toelichting',):
                    pass
                elif ch.tag in ('plaatje','formule'):
                    pass
                elif ch.tag in ('citaat','wetcitaat',):
                    pass
                else:
                    print( "%s/%s IGNORE unknown lid-child %r"%(bwb_id,soort, ch.tag) )
                    print( wetsuite.helpers.etree.tostring(ch).decode('u8') )

            lid_text = (' '.join(text)).rstrip()
            lid_text = re.sub('\s+',' ', lid_text).strip()
            ret.append( lid_text )

    return '\n\n'.join(ret)


    if 0:
        # It seems that the text is consistently under an element called artikel,
        # but there is much less consistency in the organization above that.
        # This section was an experiment of trying to find out what that organisation is.
        # 
        # (but below is the much easier answr)
        
        parents_of_artikel = []

        if soort in ('wet', 'wet-BES'):
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/titeldeel')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/titeldeel/afdeling')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk/titeldeel')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/paragraaf')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/boek/titeldeel/afdeling')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/afdeling')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/afdeling/hoofdstuk/paragraaf')
            

        elif soort in ('AMvB', 'AMvB-BES'):
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/paragraaf')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk/titeldeel')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/afdeling')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/titeldeel')

        elif soort == 'KB':
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/afdeling/paragraaf')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/paragraaf')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk/titeldeel')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk/paragraaf')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/regeling/regeling-tekst')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/deel/hoofdstuk/afdeling')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/deel/hoofdstuk/afdeling/paragraaf')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst')


        elif soort == 'rijksKB':
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/paragraaf')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst')


        elif soort == 'rijksAMvB':
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst')

        elif soort in ('ministeriele-regeling', 'ministeriele-regeling-BES'):
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/afdeling/hoofdstuk')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/paragraaf')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/paragraaf/sub-paragraaf')
            parents_of_artikel += wetgeving.findall('circulaire/circulaire-tekst/circulaire.divisie')

        elif soort == 'zbo':
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/hoofdstuk/paragraaf')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/paragraaf')
            parents_of_artikel += wetgeving.findall('circulaire/circulaire-tekst')

        elif soort == 'rijkswet':
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('wet-besluit/wettekst/paragraaf')

        elif soort in ('beleidsregel','beleidsregel-BES'):
            parents_of_artikel += wetgeving.findall('circulaire/circulaire-tekst')
            parents_of_artikel += wetgeving.findall('circulaire/circulaire-tekst/circulaire.divisie')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/hoofdstuk')
    
        elif soort == 'pbo':
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/paragraaf')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/hoofdstuk')

        elif soort == 'ministeriele-regeling-archiefselectielijst':
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst')

        elif soort in ('circulaire', 'circulaire-BES'):
            parents_of_artikel += wetgeving.findall('circulaire/circulaire-tekst')
            parents_of_artikel += wetgeving.findall('circulaire/circulaire-tekst/circulaire.divisie')

        elif soort == 'reglement':
            parents_of_artikel += wetgeving.findall('circulaire/circulaire-tekst/hoofdstuk')
            parents_of_artikel += wetgeving.findall('regeling/regeling-tekst/hoofdstuk')

        else:
            raise ValueError('UNKNOWN soort %r for %r'%(soort,bwb_id))


        for poa in parents_of_artikel:

            for artikel in (poa.findall('artikel') + 
                            poa.findall('enig-artikel') + 
                            poa.findall('tekst')   # used in circulaire
                            ):
                pass # got replaced by the below

    #if len(parents_of_artikel)>0 and len(ret)==0:
    #    print('\n%s (%s)'%(bwb_id,soort))
    #    print(' POA: %s '%parents_of_artikel)
    #    print(' RET: %s '%ret)


_versions_cache = {}

def cvdr_versions_for_work( cvdrid:str ) -> list:
    """ takes a CVDR id (with or without _version, i.e. expression id or work id),
        searches KOOP's CVDR repo, 
        Returns: a list of all matching version expression ids  

        Keep in mind that this actively does requests, so preferably don't do this in bulk, and/or cache your results.
    """
    if cvdrid in _versions_cache:
        #print( "HIT %r -> %r"%(cvdrid, _versions_cache[cvdrid]) )
        return _versions_cache[cvdrid]

    sru_cvdr = CVDR() # TODO: see if doing this here stays valid
    work_id, expression_id = wetsuite.datacollect.koop_repositories.cvdr_parse_identifier(cvdrid)
    results = sru_cvdr.search_retrieve_many("workid = CVDR%s"%work_id, up_to=10000)   # only fetches as many as needed, usually a single page of results. TODO: maybe think about injection?
    #print(f"amt results: {len(results)}")
    ret=[]
    for record in results:
        meta = wetsuite.datacollect.koop_repositories.cvdr_meta(record)
        result_expression_id = meta['identifier'][0]['text']
        ret.append( result_expression_id )
    ret = sorted( ret )
    _versions_cache[cvdrid] = ret        
    return ret
