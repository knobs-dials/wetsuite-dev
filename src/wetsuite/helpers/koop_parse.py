'''
Data and metadata parsing that is probably specific to KOOP's SRU repositories.

For more general things, see 
  - meta.py
  - patterns.py
'''
import re
import sys
import urllib.parse
import warnings
from collections import OrderedDict

import wetsuite.datacollect.koop_repositories
import wetsuite.helpers.meta

import wetsuite.helpers.etree

from wetsuite.helpers.etree import _Comment, _ProcessingInstruction, tostring



def cvdr_meta(tree, flatten=False):
    ''' Extracts metadata from a CVDR

        Because various elements can repeat - and various things frequently do (e.g. 'source'), each value is a list.

        Context for flatten:
        ====================
        In a lot of cases we care mainly for tagname and text, and there are no attributes, e.g.
          - owmskern's    <identifier>CVDR641872_2</identifier>
          - owmskern's    <title>Nadere regels jeugdhulp gemeente Pijnacker-Nootdorp 2020</title>
          - owmskern's    <language>nl</language>
          - owmskern's    <modified>2022-02-17</modified>
          - owmsmantel's  <alternative>Nadere regels jeugdhulp gemeente Pijnacker-Nootdorp 2020</alternative>
          - owmsmantel's  <subject>maatschappelijke zorg en welzijn</subject>
          - owmsmantel's  <issued>2022-02-08</issued>
          - owmsmantel's  <rights>De tekst in dit document is vrij van auteursrecht en databankrecht</rights>

        In others you may also care about an attribute or two, e.g.:
          - owmskern's    <type scheme="overheid:Informatietype">regeling</type>  (except there's no variation in that value anyway)
          - owmskern's    <creator scheme="overheid:Gemeente">Pijnacker-Nootdorp</creator>
          - owmsmantel's  <isRatifiedBy scheme="overheid:BestuursorgaanGemeente">college van burgemeester en wethouders</isRatifiedBy>
          - owmsmantel's  <isFormatOf resourceIdentifier="https://zoek.officielebekendmakingen.nl/gmb-2022-66747">gmb-2022-66747</isFormatOf>
          - owmsmantel's  <source resourceIdentifier="https://lokaleregelgeving.overheid.nl/CVDR641839">Verordening jeugdhulp gemeente Pijnacker-Nootdorp 2020</source>
    
        When those attributes matter, you want C{flatten=False} (the default) and you will get a dict like: ::
                { 'creator': [{'attr': {'scheme': 'overheid:Gemeente'}, 'text': 'Zuidplas'}], ... }
        

        @param tree: an etree object that is either 
          - a search result's individual record  
            (in which case we're looking for ./recordData/gzd/originalData/meta
          - CVDR content xml's root      
            (in which case it's              ./meta)
        ...because both contain almost the same metadata almost the same way (the difference is enrichedData in the search results).
        @param flatten: For quick and dirty presentation (only) you may wish to ask to creatively smush those into one string by asking for C{flatten==True}
        in which case you get something like: ::
                { 'creator': 'Zuidplas (overheid:Gemeente)', ... }
        Please avoid this when you care to deal with data in a structured way  (even if you can sometimes get away with it due to empty attributs).

        @return: a dict containing owmskern, owmsmantel, and cvdripm's elements merged into a single dict.
        If it's a search result, it will also mention its enrichedData.
    '''
    ret = {}

    tree = wetsuite.helpers.etree.strip_namespace(tree)
    #print( wetsuite.helpers.etree.tostring(tree).decode('u8') )


    # we want tree to be the node under which ./meta lives
    # TODO: review, this looks unclear
    if tree.find('meta') is not None:
        meta_under = tree
    else:
        meta_under = tree.find('recordData/gzd/originalData')
        if meta_under is None:
            raise ValueError("got XML that seems to be neither a document or a search result record")


    enriched_data = tree.find('recordData/gzd/enrichedData')
    if enriched_data is not None: # only appears in search results, not the XML that points to
        for enriched_key, enriched_val in wetsuite.helpers.etree.kvelements_to_dict( enriched_data ).items():
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
                        # this seems to make decent sense half the time (the attribute name is often less interesting)
                        text = '%s (%s)'%(text, attr_val)
                simplified_text.append( text )
            simpler[meta_key] = (',  '.join( simplified_text )).strip()
        ret = simpler

    return ret


def cvdr_parse_identifier(text:str, prepend_cvdr=False):
    ''' Given a CVDR style identifier string (sometimes called JCDR), 
        
        returns @return: a tuple of strings: (work ID, expression ID), the latter of which will be None if input was a work ID
        
        Both without 'CVDR', unless you set prepend_cvdr=True

        Examples: ::
            101404_1      -->  ('101404', '101404_1')
            CVDR101405_1  -->  ('101405', '101405_1')
            CVDR101406    -->  ('101406',  None     )
            1.0:101407_1  -->  ('101407', '101407_1')
    '''
    if ':' in text:
        text = text.split(':',1)[1]
    cvdr_matchobject = re.match('(?:CVDR)?([0-9]+)([_][0-9]+)?', text.replace('/','_'))
    if cvdr_matchobject is not None:
        work, enum = cvdr_matchobject.groups()
        if prepend_cvdr:
            work = 'CVDR%s'%work
        if enum is None:
            return work, None
        else:
            return work, work+enum
    else:
        raise ValueError('%r does not look like a CVDR identifier'%text)


def cvdr_param_parse(rest:str):
    ''' Picks the parameters from a juriconnect (jci) style identifier string.  
        Used by cvdr_refs.  Duplicates code in meta.py - TODO: centralize that 
    '''
    params = {}
    for param in rest.split('&'):
        pd = urllib.parse.parse_qs(param)
        for key, val in pd.items():
            out_key = key
            if key.startswith('amp;'):    # this variation seems to be a fairly common mistake in general, so try to be robust to it
                out_key = key[4:]         #   ...though it may well be better to handle this earlier in the function
            if key=='artikel':
                val = val.lstrip('artikel.')
            if key not in params:
                params[out_key] = val
            else:
                params[out_key].extend( val )
    return params


def cvdr_text(tree):
    ''' Given the XML content document as etree object, this is a quick and dirty 'give me mainly the plaintext in it',
        skipping any introductions and such.

        Returns a single string.
        This is currently a best-effort formatting, where you should e.g. find that paragraphs are split with double newlines.

        This is currently mostly copy-pasted from the bwb code TODO: unify, after I figure out all the varying structure

        TODO: write functions that support "give me flat text for each article separately"
    '''
    ret = []
    tree = wetsuite.helpers.etree.strip_namespace( tree )

    body           = tree.find('body')
    regeling       = body.find('regeling')
    regeling_tekst = regeling.find('regeling-tekst')

    identifier = tree.find('meta/owmskern/identifier')

    # TODO: decide on a best way to extract the text from this type of document, and use that in all places it happens

    for artikel in regeling_tekst.iter():  # assumes all tekst in these elements, and that they are not nested.  Ignores structure.
        if artikel.tag not in ['artikel', 'enig-artikel', 'tekst', 'structuurtekst']:
            continue

        if artikel.find('lid') is not None:
            aparts = artikel.findall('lid')
        else:
            aparts = [artikel]

        for apart in aparts:
            if apart.get('status') in ('vervallen',):
                break # ?

            text = [] # collected per lid, effectively

            # TODO: decide and clean up.
            if 1:
                # this is a somewhat awkward way to do it, but may be more robust to unusual nesting
                for node in apart.iter():
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


def cvdr_sourcerefs(tree, ignore_without_id=True, debug=False):
    ''' Given the CVDR XML content document as an etree object, 
        looks for the <source> tags, which are references to laws and other regulations (VERIFY)

        This function 
          - extracts (only) the source tags that specify
            ...and ignores 
        
        in part to normalize what is in there a bit. 
        Be aware this is more creative than a helper function probably should be.
    
        Returns a list of ::
          (type, orig, specref, parts, source_text)
        where 
          - type is currently one of 'BWB' or 'CVDR'
          - URL-like reference
          - just the identifier
          - dict of parts parsed from URL, or None
          - link text (name and often part to a reference)
            seem to be more convention-based than standardized.

        For example (mostly to point out there is _plenty_ of variation in most parts) ::
         ('BWB', 
          '1.0:c:BWBR0015703&artikel=6&g=2014-11-13',
          'BWBR0015703', 
          {'artikel': ['6'], 'g': ['2014-11-13']}, 
          'Participatiewet, art. 6')
        or ::
         ('BWB', 
          'http://wetten.overheid.nl/BWBR0015703/geldigheidsdatum_15-05-2011#Hoofdstuk1_12', 
          'BWBR0015703', 
          {}, 
          'Wet werk en bijstand, art. 8, lid 1')
        or ::
         ('CVDR', 
          'CVDR://103202_1',
          '103202_1',
          None,
          'Inspraakverordening Spijkenisse, art. 2')
        or ::
         ('CVDR', 
          '1.1:CVDR229520-1',
          '229520',
          None, 
          'Verordening voorzieningen maatschappelijke participatie 2012-A, artikel 4')
    '''
    ret = []
    tree = wetsuite.helpers.etree.strip_namespace(tree)
    owmsmantel = tree.find('meta/owmsmantel')
    for source in owmsmantel.findall('source'):
        resource_identifier = source.get('resourceIdentifier')
        source_text        = source.text

        if source_text is None:
            continue

        source_text = source_text.strip()
        if len(source_text)==0:
            continue

        if resource_identifier.startswith('CVDR://')  or  'CVDR' in resource_identifier:
            orig = resource_identifier
            if resource_identifier.startswith('CVDR://'):
                resource_identifier = resource_identifier[7:]
            try:
                parsed = cvdr_parse_identifier( resource_identifier )
                specref = parsed[1]
                if specref is None:
                    specref = parsed[0]
                ret.append( ('CVDR', orig, specref, None, source_text) )
            except ValueError as ve:
                if debug:
                    print( 'failed to parse CVDR in %s (%s)'%(resource_identifier, ve), file=sys.stderr )

            #print( '%r -> %r'%(orig, parsed ))


        elif resource_identifier.startswith('BWB://'):
            # I've not found its definition, probably because there is none, but it looks mostly jci?
            # BWB://1.0:r:BWBR0005416
            # BWB://1.0:c:BWBR0008903&artikel=12&g=2011-11-08
            # BWB://1.0:v:BWBR0015703&artikel=art. 30              which is messy
            m = re.match('(?:jci)?([0-9.]+):([a-z]):(BWB[RV][0-9]+)(.*)', resource_identifier)
            if m is not None:
                version, typ, bwb, rest = m.groups() # pylint: disable=W0612
                params = cvdr_param_parse(rest)
                ret.append( ('BWB', resource_identifier, bwb, params, source_text) )
                if debug:
                    print( 'BWB://-style   %r  %r'%(bwb, params), file=sys.stderr )

        elif resource_identifier.startswith('http://')  or  resource_identifier.startswith('https://'):
            # TODO: centralize a 'reference_from_url' function, because there is more than this one style, and we can extract more

            # http://wetten.overheid.nl/BWBR0013016
            # http://wetten.overheid.nl/BWBR0003245/geldigheidsdatum_19-08-2009

            m = re.match('https?://wetten.overheid.nl/(?:zoeken_op/)?(BWB[RV][0-9]+)(/.*)?', resource_identifier)
            if m is not None:
                bwb, rest = m.groups()
                params={}
                if rest is not None:
                    params =  cvdr_param_parse(rest)
                if debug:
                    print("http-wetten: %r %r"%(bwb, params), file=sys.stderr)
                ret.append( ('BWB', resource_identifier, bwb, params, source_text) )

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

        elif resource_identifier.startswith('jci') or 'v:BWBR' in resource_identifier or 'c:BWBR' in resource_identifier:
            try:
                d = wetsuite.helpers.meta.parse_jci( resource_identifier )
            except ValueError as ve:
                if debug:
                    print("ERROR: bad jci in %r"%ve, file=sys.stderr)
                continue
            bwb, params = d['bwb'], d['params']
            if debug:
                print("JCI: %r %r"%(bwb, params))
            ret.append( ('BWB', resource_identifier, bwb, params, source_text) )

        else:
            if not ignore_without_id:
                ret.append( ('unknown', None, None, None, source_text) )
            if debug and len(resource_identifier.strip())>0:
                print( 'UNKNOWN: %r %r'%(resource_identifier, source_text), file=sys.stderr )
                #print( wetsuite.helpers.etree.tostring(source) )

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



def bwb_searchresult_meta( record_node ):
    ''' Takes individual SRU result record as an etree subtrees, 
        picks out BWB-specific metadata (merging the separate metadata sections).
        Returns a dict
    '''
    record_node = wetsuite.helpers.etree.strip_namespace( record_node )

    #recordSchema   = record.find('recordSchema')      # e.g. <recordSchema>http://standaarden.overheid.nl/sru/</recordSchema>
    #recordPacking  = record.find('recordPacking')     # probably <recordPacking>xml</recordPacking>
    record_data     = record_node.find('recordData')        # the actual record
    #recordPosition = record.find('recordPosition')    # e.g. <recordPosition>12</recordPosition>
    payload = record_data[0]
    #print( etree.ElementTree.tostring( payload, encoding='unicode' ) )

    original_data = payload.find('originalData')
    owmskern     = wetsuite.helpers.etree.kvelements_to_dict( original_data.find('meta/owmskern')   )
    owmsmantel   = wetsuite.helpers.etree.kvelements_to_dict( original_data.find('meta/owmsmantel') )
    bwbipm       = wetsuite.helpers.etree.kvelements_to_dict( original_data.find('meta/bwbipm')     )
    enriched_data = wetsuite.helpers.etree.kvelements_to_dict( payload.find('enrichedData') )

    merged = {}
    merged.update(owmskern)
    merged.update(owmsmantel)
    merged.update(bwbipm)
    merged.update(enriched_data)
    return merged


def bwb_toestand_usefuls( tree ):
    ''' Fetch the most interesting metadata from parsed toestand XML.    TODO: finish '''
    ret = {}

    ret['bwb-id']                   = tree.get('bwb-id')

    wetgeving = tree.find('wetgeving') # TODO: also allow the alternative roots
    ret['intitule']               = wetgeving.findtext('intitule')
    ret['citeertitel']            = wetgeving.findtext('citeertitel')
    ret['soort']                  = wetgeving.get('soort')
    ret['inwerkingtredingsdatum'] = wetgeving.get('inwerkingtredingsdatum')

    # this might contain nothing we can't get better in wti or manifest?
    #wetgeving_metadata = wetgeving.find('meta-data')
    return ret


def bwb_wti_usefuls( tree ):
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
            wijziging['bekendmaking'] = ( bekendmaking.get('soort'),
                                          bekendmaking.findtext('publicatiejaar'),
                                          bekendmaking.findtext('publicatienummer') )

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

    if manifest_usefuls is not None:
        merged.update( manifest_usefuls )

    if toestand_usefuls is not None:
        merged.update( toestand_usefuls )

    return merged


def bwb_toestand_text(tree):
    ''' Given the document (as an etree object), this is a quick and dirty 'give me mainly the plaintext in it',
        skipping any introductions and such.

        Not structured data, intended to assist generic "how do these setences parse" code

        TODO: 
         -  review this, it makes various assumptions about document structure
         -  review the handling of certain elements, like lijst, table, definitielijst

         -  see if there are contained elements to ignore, like maybe <redactie type="vervanging"> ?

         - generalize to have a parameter ignore_tags=['li.nr', 'meta-data', 'kop', 'tussenkop', 'plaatje', 'adres',
           'specificatielijst', 'artikel.toelichting', 'citaat', 'wetcitaat']
    '''
    ret=[]
    tree = wetsuite.helpers.etree.strip_namespace( tree )

    bwb_id = tree.get('bwb-id')    # only used in debug
    wetgeving = tree.find('wetgeving')
    soort = wetgeving.get('soort') # only used in debug
    for artikel in wetgeving.iter():  # assumes all tekst in these elements, and that they are not nested.  Ignores structure.
        if artikel.tag not in ['artikel', 'enig-artikel', 'tekst', 'structuurtekst']:
            continue

        if artikel.find('lid') is not None:
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
            lid_text = re.sub(r'[\s]+',' ', lid_text).strip()
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
    ''' takes a CVDR id (with or without _version, i.e. expression id or work id),
        searches KOOP's CVDR repo, 
        Returns: a list of all matching version expression ids  

        Keep in mind that this actively does requests, so preferably don't do this in bulk, and/or cache your results.
    '''
    if cvdrid in _versions_cache:
        #print( "HIT %r -> %r"%(cvdrid, _versions_cache[cvdrid]) )
        return _versions_cache[cvdrid]

    sru_cvdr = wetsuite.datacollect.koop_repositories.CVDR() # TODO: see if doing this here stays valid
    work_id, expression_id = cvdr_parse_identifier(cvdrid)
    results = sru_cvdr.search_retrieve_many("workid = CVDR%s"%work_id, up_to=10000)   # only fetches as many as needed, usually a single page of results. TODO: maybe think about injection?
    #print(f"amt results: {len(results)}")
    ret=[]
    for record in results:
        meta = cvdr_meta(record)
        result_expression_id = meta['identifier'][0]['text']
        ret.append( result_expression_id )
    ret = sorted( ret )
    _versions_cache[cvdrid] = ret
    return ret



###################################


def alineas_with_selective_path(tree, start_at_path=None, alinea_elemname='al'): # , ignore=['meta-data']
    ''' Given document-style XML data such as that of CVDR XML documents,
        tries to capture most of the interesting structure in easier-to-digest python data form,
        (and without expecting a specific nesting)
    
        Whenever we hit an <al>, we emit a dict that details all the interesting elements between body and this <al>
        This is intended as the lower-level half of potential cleanup, grouping, etc.

        Returns a list of dicts, one for each <al>.
        
        Each such output dict should look like: ::
            {
                'parts': [   {'what': 'hoofdstuk',  'hoofdstuklabel': 'Hoofdstuk', 'hoofdstuknr': '1', 'hoofdstuktitel': 'Algemene bepalingen',},
                            {'what': 'artikel',    'artikellabel': 'Artikel',     'artikelnr': '1:1', 'artikeltitel': 'Begripsomschrijvingen',}  ],
                'merged':    {'hoofdstuklabel': 'Hoofdstuk',
                            'hoofdstuknr': '1',
                            'hoofdstuktitel': 'Algemene bepalingen'
                            'artikellabel': 'Artikel',
                            'artikelnr': '1:1',
                            'artikeltitel': 'Begripsomschrijvingen',
                            },            
                'path':      '/cvdr/body/regeling/regeling-tekst/hoofdstuk[1]/artikel[1]/al',
                'text-flat': 'In deze verordening wordt verstaan dan wel mede verstaan onder:'
            }
        Where:
          - this is very much intended to then be simplified further, using merge_alinea_data
            which is separate largely for flexibility's sake, 
            (CONSIDER: also provide a extract-text-with-reasonable-defaults fuction)
          - 'parts' details each structural element (boek, hoofdstuk, afdeling paragraaf, artikel, lid)
             that encompasses this fragment
             the ...label keys are largely entirely redundant, but there are documents that abuse these, which you may want to know.
          - 'merged' is the part dicts, without the 'what' key, update()d into one dict.
             In simpler documents, e.g. where you just haev artikel and lid, this makes for an easier way to filter out the part you want.
             In complex documents, this may (for a smallish amount of cases) be incorrect because when you e.g. have an afdeling nested in an afdeling, values from one overwrite the other.
          - 'path' is the xpath of the item we're describing, in case you want to find this element in XML / etree form
          - 'text-flat' is plain text, with any markup elements flattened out 
          - WARNING: currently NONE of these keys in parts/merged are settled on yet, things may change.
    '''
    warnings.warn('The behaviour of alineas_with_selective_path() is not fully decided, and may still change')

    # this is based on observations of CVDR and BWB
    structure_elements = {
        'boek':{},
        'hoofdstuk':{'kop/label':'hoofdstuklabel', 'kop/nr':'hoofdstuknr', 'kop/titel':'hoofdstuktitel'},
        'afdeling': {'kop/label':'afdelinglabel',  'kop/nr':'afdelingnr',  'kop/titel':'afdelingtitel'},
        'paragraaf':{'kop/label':'paragraaflabel', 'kop/nr':'paragraafnr', 'kop/titel':'paragraaftitel'},
        'sub-paragraaf':{'kop/label':'subparagraaflabel', 'kop/nr':'subparagraafnr', 'kop/titel':'subparagraaftitel'},
        'artikel':{'kop/label':'artikellabel', 'kop/nr':'artikelnr', 'kop/titel':'artikeltitel'},
        'lid':{'lidnr':'lidnr'},
        'deel':{}, # have

        'divisie':  {'kop/label':'divisielabel', 'kop/nr':'divisienr', 'kop/titel':'divisietitel', '@bwb-ng-variabel-deel':'divisie_vd'},
        'circulaire.divisie':{'@bwb-ng-variabel-deel':'circulairedivisie_vd'},
        'definitielijst':{},
        'definitie-item':{'term':'term', 'li.nr':'li.nr'},

        'li':{'@nr':'li-nr', 'li.nr':'li.nr', '@bwb-ng-variabel-deel':'li_vd'},
        # some things to have in the stack-like thing, but which don't have details
        'aanhef':{},       #'afkondiging' 'preambule'
        'note-toelichting':{},
        'bijlage':{},
        'lijst':{},
        # table, plaatje?

        # rechtgeving.nl
        'uitspraak':{'@id':'id'},
        'section':{'@id':'id', 'title/nr':'nr', 'title':'title'},
        'listitem':{},
        'parablock':{'nr':'nr'},
        'uitspraak.info':{},
        'inhoudsindicatie':{'@id':'id'},
    }

    ret = []

    tree = wetsuite.helpers.etree.strip_namespace(tree)

    # adapted from node_walk
    if start_at_path is not None:
        start = tree.xpath(start_at_path)[0] # maybe use xpath() so it takes xpath paths
    else:
        start = tree

    path_to_element = []
    element_stack = [start]
    while element_stack:
        element = element_stack[-1]
        if path_to_element  and  element is path_to_element[-1]:
            path_to_element.pop()
            element_stack.pop()
            #print( path_to_element )

            if isinstance(element, _Comment) or isinstance(element, _ProcessingInstruction):
                pass
            else:
                if element.tag == alinea_elemname:
                    xpath_path = wetsuite.helpers.etree.path_between(tree, element)
                    emit = {'path':xpath_path, 'parts':[], 'merged':{}}
                    for pathelem in path_to_element:
                        if pathelem.tag in structure_elements:
                            part_dict = {}
                            for what_to_fetch, what_to_call_it in structure_elements[pathelem.tag].items():
                                if what_to_fetch[0]=='@': # TODO: less magical, maybe just call keys 'fetch_attr' and 'fetch_text'?
                                    part_dict[what_to_call_it] = pathelem.get( what_to_fetch[1:] )
                                else:
                                    pathelem_rel = pathelem.find( what_to_fetch )
                                    if pathelem_rel is None:
                                        pass
                                        #print("Did not find %r under %r"%(what_to_fetch, xpath_path))
                                    else:
                                        part_dict[what_to_call_it] = pathelem_rel.text
                            emit['merged'].update( part_dict ) # duplicated, easier to access, and clobbered whenever you have an element in the structure twice
                            part_dict['what'] = pathelem.tag
                            emit['parts'].append( part_dict )

                    emit['text-flat'] = wetsuite.helpers.etree.all_text_fragments( element, join=' ' )
                    #yield emit
                    ret.append( emit )

        else:
            path_to_element.append( element )
            for child in reversed( element ):
                element_stack.append( child )
    return ret




def merge_alinea_data( alinea_dicts, if_same={
    # these first four rarely get into it
    'hoofdstuk':'hoofdstuknr',
    'afdeling':'afdelingnr',
    'paragraaf':'paragraafnr',
    'sub-paragraaf':'subparagraafnr',

    'artikel':'artikelnr', 
    'lid':'lidnr',

    'definitie-item':'term',

    #rechtspraak
    'uitspraak':'id',
    'uitspraak.info':None,
    'section':'nr',
    } ):
    ''' Takes the output of alineas_with_selective_path()
        puts text fragments together when their specified ['parts'] values are the same.

        In other words, this lets you control just how flat to make the text, e.g. 
          - flatten all text within a lid (e.g. flattening lists), 
          - smush all lid text within an article together, etc.
          - mostly flatten out the text, but still group it by hoofdstuk if those are present
        ...etc.

        CONSIDER: returning a meta dict for each such grouped text (instead of the raw key)
    '''
    r=0

    merged = OrderedDict()
    key_meta = {} # key -> meta dict

    for alinea_dict in alinea_dicts:
        # CONSIDER: a more readable/usable version of key
        key = []
        meta = []
        for part_dict in alinea_dict['parts']:
            what = part_dict['what']
            #print( part_dict)
            if what in if_same  and if_same[what] in part_dict:
                sel = if_same[what]
                #print(sel)
                if sel is None: # TODO: think about this adjustment
                    interesting_val='_dummy_%d'%r
                    r+=1
                else:
                    interesting_val = part_dict[sel]
                    if interesting_val is None: # maybe warn that there isn't?
                        interesting_val=''
                key.append( '%s:%s'%(what, interesting_val.strip()) )
                meta.append( (what, interesting_val.strip() ) )
        key = '  '.join(key)
        key_meta[key] = meta
        #print( key)

        if key not in merged:
            merged[key] = []

        merged[key].append( alinea_dict['text-flat'] )

    ret = []
    for key, text in merged.items():
        ret.append( (key_meta[key], text) )
    return ret


def iter_chunks_xml(xml):
    """ The combination of  alineas_with_selective_path()  and  merge_alinea_data()  

        Notes:
          - Sloppy initial implementation
          - attempts to handle tables
          - Currently geared specifically to CVDR xml
    """
    tree = wetsuite.helpers.etree.fromstring(xml)
    tree_stripped = wetsuite.helpers.etree.strip_namespace(tree)

    for n, table in enumerate(list(tree_stripped.findall(".//table"))):
        text = str(tostring(table))
        if len(text) < 10:
            continue
        yield {'n': n,
               'part_id': f'table {n}',
               'text': text,
               'from_table': True,
               }
        table.getparent().remove(table)

    alinea_dicts = alineas_with_selective_path(tree_stripped, start_at_path='body/regeling/regeling-tekst')
    merged = merge_alinea_data(alinea_dicts, if_same={  'hoofdstuk':'hoofdstuknr',
                                                        'afdeling':'afdelingnr',
                                                        'paragraaf':'paragraafnr',
                                                        'sub-paragraaf':'subparagraafnr',
                                                        'artikel':'artikelnr',
                                                    })

    for n, (label, content) in enumerate(merged):
        text = '\n'.join(content)
        # print(label, text)
        # r = input('prompt? y/n')
        # if r == 'y':
        if len(text) > 10:
            yield {'n': n,
                   'part_id': ' '.join(' '.join(l) for l in label),
                   'text': text,
                   'from_table': False,
                   }
