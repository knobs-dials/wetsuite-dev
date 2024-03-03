''' Helps interact with the EUR-Lex website and APIs.
'''
import re, datetime, urllib.parse

import requests

import bs4


def fetch_by_resource_type(typ='JUDG'):
    ''' Intends to query the SPARQL endpoint to ask for most CELEXes of a specific type, 
        (defaulting to court judgments for no particular reason)

        TODO: fetch values e.g. at 
        https://github.com/SEMICeu/Excel-to-CPSVAP-RDF-transformation/blob/master/page-objects/utils/CPSVtemplateWithCodelists.json
        in handier form

        Asks to give its semantic results as JSON data,  which we parse and return as a python structure.


        @param typ: the type to fetch, e.g. 
          - 'JUDG'  for court judgments
          - 'REG'   for regulations (but there are a handful of related things) 

        @return: a (possibly-many-item'd) nested structure (python structure, loaded from JSON)

        The structure you get back looks like:  ( see also https://www.w3.org/TR/2013/REC-sparql11-results-json-20130321/ ) ::
            {
                'head': {
                    'link': [], 'vars': ['work', 'type', 'celex', 'date', 'force']
                },
                'results': {
                    'distinct': False,
                    'ordered': True,
                    'bindings': [
                        {
                            'work':{
                                'type':'uri',           
                                'value':'http://publications.europa.eu/resource/cellar/1e3100ce-8a71-433a-8135-15f5cc0e927c'
                            },
                            'type':{
                                'type':'uri',
                                'value':'http://publications.europa.eu/resource/authority/resource-type/JUDG'
                            },
                            'celex':{
                                'type':'typed-literal', 
                                'value':'61996CJ0080', 
                                'datatype': 'http://www.w3.org/2001/XMLSchema#string'
                            },
                            'date': {
                                'type': 'typed-literal',
                                'value':'1998-01-15',
                                'datatype': 'http://www.w3.org/2001/XMLSchema#date'
                            }
                        },
                        # ...one of these for each result
                    ]
                }
            }
    '''
    # The proper way would be to use a library like sparqlwrapper
    #   but for now we can get away with hardcodig a query like:
    query = '''PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
      select distinct ?work ?type ?celex ?date ?force 
      WHERE {
          ?work cdm:work_has_resource-type ?type. 
          FILTER(?type=<http://publications.europa.eu/resource/authority/resource-type/%s>)
          FILTER not exists{?work cdm:work_has_resource-type <http://publications.europa.eu/resource/authority/resource-type/CORRIGENDUM>
      } 
      OPTIONAL { ?work cdm:resource_legal_id_celex ?celex. } 
      OPTIONAL { ?work cdm:work_date_document ?date. } 
      OPTIONAL { ?work cdm:resource_legal_in-force ?force. } 
      FILTER not exists{?work cdm:do_not_index "true"^^<http://www.w3.org/2001/XMLSchema#boolean>}. }'''%typ

    url = ''.join([
        'http://publications.europa.eu/webapi/rdf/sparql?default-graph-uri=&query=',
        urllib.parse.quote(query),
        '&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on&run=+Run+Query+'
    ])
    resp = requests.get(url, timeout=30)
    return resp.json()


def extract_html(htmlbytes):
    ''' Extract data from formatted HTML from the website itself.

        Written for JUDG pages, probably needs work for others.

        Also, there are plenty of assumptions in this code that probably won't hold over time,
        so for serious projects you should probably use a data API instead.

        TODO: see how language-sensitive this is.
        CONSIDER: extract more link hrefs (would probably need to hand in page url to)

        @param htmlbytes: the page, as a bytes object
        @return: a nested structure
    '''
    # This code turned messier than it originally was,
    # because the page turned out to be more flexible

    def parse_datalist(under_dl_node):
        ' pick out the basic parts of a data list '
        ret = {}
        for node in under_dl_node.children:
            # generally we have a dt used as a label, and dd with a value
            if node.name == 'dt':
                what = node.text.strip().strip(':')
            elif node.name == 'dd':
                # however, the dd can contain a list instead of just a string
                #    the structure is consistent only within each section,
                #    so leave it for code calling this function to process usefully
                #    (forced to be - JSON would choke on it if you insert it as-is)
                if node.find(['ul','ol']):
                    ret[what] = node.findAll('li')
                else:
                    ret[what] = node.text.strip()
        return ret

    ret = {}
    soup = bs4.BeautifulSoup( htmlbytes, features='lxml' )

    # the CELEX appears on the page a lot but I'm not sure what the most stable source would be.
    celex = soup.find('meta', attrs={'name':'WT.z_docID'}).get('content')
    ret['celex'] = celex

    ret['titles']={}
    PP1Contents = soup.find(id='PP1Contents')
    if PP1Contents is not None:
        ret['titles']['title'] = PP1Contents.find(id='title').text
        ret['titles']['englishTitle'] = PP1Contents.find(id='englishTitle').text
        ret['titles']['originalTitle'] = PP1Contents.find(id='originalTitle').text

        eid = PP1Contents.find('p', text=re.compile(r'.*ECLI identifier.*'))
        if eid is not None:
            ret['ecli'] = eid.text.split(':', 1)[1].strip()

    PPDates_Contents = soup.find(id='PPDates_Contents')
    ret['dates'] = {}
    if PPDates_Contents is not None:
        for what, val in parse_datalist( PPDates_Contents.find('dl') ).items():
            if ';' in val:
                val = val.split(';')[0].strip()
            if '/' in val: # format ISO8601 style for less ambiguity
                val = datetime.datetime.strptime(val, "%d/%m/%Y").strftime('%Y-%m-%d')
            ret['dates'][what] = val

    ret['misc'] = {}
    PPMisc_Contents = soup.find(id='PPMisc_Contents')
    if PPMisc_Contents is not None:
        ret['misc'] = parse_datalist( PPMisc_Contents.find('dl') )


    ret['proc'] = {}
    PPProc_Contents = soup.find(id='PPProc_Contents')
    if PPProc_Contents is not None:
        # procedure looks like a key:value thing (e.g. Defendant:Raad),
        # but there are cases where the value is a list, which parse_datalist doesn't handle for us so we have to.
        # for consistency's sake, even the single-value cases are returned as a list
        for k, v in parse_datalist( PPProc_Contents.find('dl') ).items():
            if isinstance(v, str):
                ret['proc'][k] = [v]
            else: # will be a list of bs4 nodes, e.g.  [<li><a href="./../../../procedure/EN/2018_395">2018/0395/NLE</a></li>]
                ret['proc'][k] = []
                for li in v:
                    a = li.find('a')
                    if a is not None:
                        ret['proc'][k].append( a.text ) # TODO: consider actually figuring out the link
                #print( ret['proc'][k] )
                #print( k, type(v), v )

            # print( dlitem )
            # if type(dlitem) in (str, dict): # dict seems typical; TODO: rewrite the other cases to dict
            #     ret['proc'] = dlitem
            # else:
            #     # is still the bs4 object
            #     # e.g.  in 62020CJ0180
            #     # ignore for now? TODO: Warn?
            #     print("WARNING - didn't think proc would have a %s in %s"%(type(dlitem).__class__.__name__, celex))
            #     print('DLITEM',dlitem)
            #     raise
            #     #ret['proc'] = it


    ret['linked'] = {}
    PPLinked_Contents = soup.find(id='PPLinked_Contents')
    if PPLinked_Contents is not None:
        parsed_link = {}
        for what, val in parse_datalist(PPLinked_Contents.find('dl')).items(): 
            if isinstance(val, bs4.element.ResultSet):
                parsedval = []
                # This is far from complete
                for li in val:
                    a = li.find('a')
                    data_celex = a.get('data-celex')
                    if data_celex is not None:
                        parsedval.append(   (  'CELEX:'+data_celex, ''.join( li.findAll(text=True) ).strip()  )   )
                    else:
                        pass # TODO: handle other types
                parsed_link[what] = parsedval
            else:
                parsed_link[what] = val
        ret['linked'] = parsed_link


    # Doctrine
    ret['doctrine'] = {}
    PPDoc_Contents = soup.find(id='PPDoc_Contents')
    if PPDoc_Contents is not None:
        parsed_doctr = {}
        for what, val in parse_datalist(PPDoc_Contents.find('dl')).items():
            if isinstance(val, bs4.element.ResultSet):
                parsedval = []
                for li in val:
                    a = li.find('a')
                    parsedval.append(  li.text  ) # TODO: check that doesn't need to be a join-findall too
                parsed_doctr[what] = parsedval
            else:
                parsed_doctr[what] = val
        ret['doctrine'] = parsed_doctr


    # Classifications
    ret['classifications'] = {}
    PPClass_Contents = soup.find(id='PPClass_Contents')
    if PPClass_Contents is not None:
        parsed_class = {}
        for what, val in parse_datalist(PPClass_Contents.find('dl')).items():
            if isinstance(val, bs4.element.ResultSet):
                parsedval = []
                for li in val:
                    div = li.find('div')
                    if div is not None:
                        parsedval.append(  list(s.strip()   for s in div.findAll(text=True)  if len(s.strip())>0 )  )
                    else:
                        parsedval.append( ''.join( li.findAll(text=True) ).strip() )
                parsed_class[what] = parsedval
            else:
                parsed_class[what] = val
        ret['classifications'] = parsed_class


    # Languages and formats available   (not always there)
    ret['contents'] = []
    PP2Contents = soup.find(id='PP2Contents')
    if PP2Contents is not None:
        parsed_contents = []
        for ul in PP2Contents.findAll('ul'):
            format = None
            for maybe_format in ul.get('class'):
                if maybe_format.startswith('PubFormat'):
                    format = maybe_format[9:]
            if format is not None:
                for li in ul.findAll('li'):
                    if 'disabled' not in li.get('class',''):
                        a = li.find('a')
                        lang = a.find('span').text
                        if format == 'VIEW':
                            continue
                        # constructing the URL like that is cheating and may not always work. 
                        # Ideally we'd urllib.parse.urljoin  it from the href, but then we must know the URL this was fetched from.
                        parsed_contents.append(
                            (lang, format, 'https://eur-lex.europa.eu/legal-content/%s/TXT/%s/?uri=CELEX:%s'%(lang, format, celex)) )
        ret['contents'] = parsed_contents


    #Document text  (not always there)
    PP4Contents = soup.find(id='PP4Contents')
    txt = []
    if PP4Contents is not None:

        # TODO: review, this may be overkill and/or not complete
        titerate = []
        TexteOnly = PP4Contents.find(id='TexteOnly') # probably better if it's there?
        if TexteOnly is not None:
            titerate.append( TexteOnly )
        else: #  currently looks for  div > p    (because p also appears e.g. inside tables)
            for p in PP4Contents.findAll('p'):
                if p.parent.name in ('div',)   and  p.parent not in titerate: # yeah okay, that's nasty
                    titerate.append( p.parent )

        # txt will become a list of (section_name_str, section_contents_strlist)
        #   and all the parts will collect into:
        cur_section_name, cur_section_txt = '', []

        for iterate_under in titerate:
            for node in iterate_under.children:
                if isinstance(node, bs4.element.NavigableString):
                    s = node.string.strip()
                    if len(s)>0:
                        cur_section_txt.append(s)
                else: # assume Tag
                    if node.name in ('h2',
                                     'h3' # arguably this should not split?
                                     ):
                        if len(cur_section_txt) > 0: # flush
                            txt.append( (cur_section_name, cur_section_txt) )
                        cur_section_name, cur_section_txt = '', []
                        cur_section_name = node.text

                    elif node.name in ('p',):
                        txtfrags = list(  frag  for frag in node.findAll(text=True) if len(frag.strip())>0)
                        cur_section_txt.extend( txtfrags )
                    elif node.name in ('em','b','i',
                                       'center',
                                       ):
                        txtfrags = list(  frag  for frag in node.findAll(text=True) if len(frag.strip())>0)
                        cur_section_txt.extend( txtfrags )
                    elif node.name in ('br','hr'):
                        pass # is nothing
                    elif node.name in ('a',): # seem to be used mainly as anchors for browsers to #go to, so skippable
                        if len(node.text.strip())>0:
                            cur_section_txt.extend( node.text.strip() ) # probably used as a header
                            #raise ValueError("Bad assumption, that an  a  tag has no text, in %r"%(node))

                    # not really inspected, add flattened for now
                    elif node.name in (
                        'title',
                        'div',
                        'span',
                        'table',
                        'dl','dt','dd',

                        'td' # TODO: think
                    ):
                        #print( node.name.upper(), node)
                        txtfrags = list(  frag  for frag in node.findAll(text=True) if len(frag.strip())>0)
                        cur_section_txt.extend( txtfrags )

                    # ignore
                    elif node.name in ('img',):
                        pass
                    elif node.name in ('link',): # seems to be stylesheets
                        #print('LINK', node)
                        pass
                    elif node.name in ('meta', # probably just a charset?
                                    'font'): 
                        #print('META', node)
                        pass

                    elif node.name is None:
                        print('NONE', node)

                    else:
                        raise ValueError( "Don't yet handle %r"%node.name )

        if len(cur_section_txt) > 0: # final flush
            txt.append( (cur_section_name, cur_section_txt) )

    ret['text'] = txt

    return ret
