import re, datetime, urllib.parse

import requests

import bs4


def fetch_JUDG():
    ''' Returns some specifically structured
    '''
    # The proper way would be to use a library like sparqlwrapper
    # but for now we can get away with things like:
    query = '''PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
      PREFIX annot: <http://publications.europa.eu/ontology/annotation#>
      PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
      PREFIX dc:<http://purl.org/dc/elements/1.1/>
      PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
      PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      PREFIX owl:<http://www.w3.org/2002/07/owl#>
      select distinct ?work ?type ?celex ?date ?force 
      WHERE {
          ?work cdm:work_has_resource-type ?type. 
          FILTER(?type=<http://publications.europa.eu/resource/authority/resource-type/JUDG>)
          FILTER not exists{?work cdm:work_has_resource-type <http://publications.europa.eu/resource/authority/resource-type/CORRIGENDUM>
      } 
      OPTIONAL { ?work cdm:resource_legal_id_celex ?celex. } 
      OPTIONAL { ?work cdm:work_date_document ?date. } 
      OPTIONAL { ?work cdm:resource_legal_in-force ?force. } 
      FILTER not exists{?work cdm:do_not_index "true"^^<http://www.w3.org/2001/XMLSchema#boolean>}. }'''

    url = 'http://publications.europa.eu/webapi/rdf/sparql?default-graph-uri=&query='+urllib.parse.quote(query)+'&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on&run=+Run+Query+'
    resp = requests.get(url)
    return resp.json()


def extract_html(htmlbytes):
    ''' Extract data from formatted HTML.

        Written for JUDG pages, may need work for others.

        There are plenty of assumptions in this code that probably won't hold over time,
        so for serious projects you should probably use a data API instead.

        TODO: see how language-sensitive this is.
        CONSIDER: extract more link hrefs (would probably need to hand in page url to)
    '''
    def parse_datalist(under_dl_node):
        ' pick out the basic parts of a data list '
        ret = {}
        for node in under_dl_node.children:
            if node.name == 'dt':
                what = node.text.strip().strip(':')
            elif node.name == 'dd':
                if node.find(['ul','ol']):
                    ret[what] = node.findAll('li') # the structure is consistent only within each section, so leave it for outside code to process
                else:
                    ret[what] = node.text.strip()
        return ret

    ret = {}
    soup = bs4.BeautifulSoup( htmlbytes, features='lxml' )

    # the CELEX appears on the page a lot but I'm not sure what the most stable source would be.
    celex = soup.find('meta', attrs={'name':'WT.z_docID'}).get('content')
    ret['celex'] = celex

    PP1Contents = soup.find(id='PP1Contents')
    ret['titles']={}
    ret['titles']['title'] = PP1Contents.find(id='title').text
    ret['titles']['englishTitle'] = PP1Contents.find(id='englishTitle').text
    ret['titles']['originalTitle'] = PP1Contents.find(id='originalTitle').text

    eid = PP1Contents.find('p', text=re.compile(r'.*ECLI identifier.*'))
    if eid is not None:
        ret['ecli'] = eid.text.split(':', 1)[1].strip()

    PPDates_Contents = soup.find(id='PPDates_Contents')
    ret['dates'] = {}
    for what, val in parse_datalist( PPDates_Contents.find('dl') ).items():
        if ';' in val:
            val = val.split(';')[0].strip()
        if '/' in val: # format ISO8601 style for less ambiguity
            val = datetime.datetime.strptime(val, "%d/%m/%Y").strftime('%Y-%m-%d')
        ret['dates'][what] = val

    PPMisc_Contents = soup.find(id='PPMisc_Contents')
    ret['misc'] = parse_datalist( PPMisc_Contents.find('dl') )


    PPProc_Contents = soup.find(id='PPProc_Contents')
    proc = []
    if PPProc_Contents is not None:
        proc = parse_datalist( PPProc_Contents.find('dl') )
    ret['proc'] = proc


    PPLinked_Contents = soup.find(id='PPLinked_Contents')
    parsed_link = {}
    for what, val in parse_datalist(PPLinked_Contents.find('dl')).items():
        if type(val) is bs4.element.ResultSet:
            parsedval = []
            for li in val:
                a = li.find('a')
                data_celex = a.get('data-celex')
                parsedval.append(   (  'CELEX:'+data_celex, ''.join( li.findAll(text=True) ).strip()  )   )
            parsed_link[what] = parsedval
        else:
            parsed_link[what] = val
    ret['linked'] = parsed_link


    # Doctrine
    PPDoc_Contents = soup.find(id='PPDoc_Contents')
    parsed_doctr = {}
    if PPDoc_Contents is not None:
        for what, val in parse_datalist(PPDoc_Contents.find('dl')).items():
            if type(val) is bs4.element.ResultSet:
                parsedval = []
                for li in val:
                    a = li.find('a')
                    parsedval.append(  li.text  ) # TODO: check that doesn't need to be a join-findall too
                parsed_doctr[what] = parsedval
            else:
                parsed_doctr[what] = val
    ret['doctrine'] = parsed_doctr


    # Classifications
    PPClass_Contents = soup.find(id='PPClass_Contents')
    parsed_class = {}
    if PPClass_Contents is not None:
        for what, val in parse_datalist(PPClass_Contents.find('dl')).items():
            if type(val) is bs4.element.ResultSet:
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
    PP2Contents = soup.find(id='PP2Contents')
    parsed_contents = []
    if PP2Contents is not None:
        for ul in PP2Contents.findAll('ul'):
            format = None
            for maybe_format in ul.get('class'):
                if maybe_format.startswith('PubFormat'):
                    format = maybe_format[9:]
            if format != None:
                for li in ul.findAll('li'):
                    if 'disabled' not in li.get('class',''):
                        a = li.find('a')
                        lang = a.find('span').text
                        if format == 'VIEW':
                            continue
                        # constructing the URL like that is cheating and may not always work. Ideally we'd urllib.parse.urljoin  it from the href, but then we must know the URL this was fetched from.
                        parsed_contents.append( (lang, format, 'https://eur-lex.europa.eu/legal-content/%s/TXT/%s/?uri=CELEX:%s'%(lang, format, celex)) )
    ret['contents'] = parsed_contents


    #Document text  (not always there)
    PP4Contents = soup.find(id='PP4Contents')
    txt = []
    if PP4Contents is not None:
        doc = PP4Contents.find('p').parent    #TexteOnly = PP4Contents.find(id='TexteOnly')
        section_name, section_txt = '', []
        for node in doc.children:
            if type(node) is bs4.element.NavigableString:
                s = node.string.strip()
                if len(s)>0:
                    txt.append(s)
            else: # assume Tag
                if node.name in ('h2',):
                    if len(section_txt) > 0:
                        txt.append( (section_name, section_txt) )
                    section_name, section_txt = '', []
                    section_name = node.text

                elif node.name in ('p',):
                    txtfrags = list(  frag  for frag in node.findAll(text=True) if len(frag.strip())>0)
                    section_txt.extend( txtfrags )
                elif node.name in ('em',):
                    txtfrags = list(  frag  for frag in node.findAll(text=True) if len(frag.strip())>0)
                    section_txt.extend( txtfrags )
                elif node.name in ('br','hr'):
                    pass # is nothing
                elif node.name in ('a',): # seem to be used mainly as anchors for browsers to #go to, so skippable
                    if len(node.text.strip())>0:
                        raise ValueError("Bad assumption, that <a> has no text, in %r"%node) 

                # not really inspected, add flattened for now
                elif node.name in (
                    'title',
                    'div',
                    'span',
                    'table',
                    'dl','dt','dd',
                ):
                    #print( node.name.upper(), node)
                    txtfrags = list(  frag  for frag in node.findAll(text=True) if len(frag.strip())>0)
                    section_txt.extend( txtfrags )

                # ignore
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
                    raise ValueError( "Don't yet handle %r"%node.name  )

        if len(section_txt) > 0:
            txt.append( (section_name, section_txt) )
        section_name, section_txt = '', []
        
    ret['text'] = txt


    return ret
