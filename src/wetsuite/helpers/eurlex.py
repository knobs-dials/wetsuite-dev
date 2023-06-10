

def extract_html(htmlbytes):
    ''' Extract data from formatted HTML.

        Written for JUDG pages, may need work for others.

        There are plenty of assumptions in this code that probably won't hold over time,
        so you should probably use an API instead.

        TODO: see how language sensitive this is.
        CONSIDER: extract more link hrefs
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
    ret['dates']={}
    parsed_dates = {}
    for what, val in parse_datalist( PPDates_Contents.find('dl') ).items():
        if '/' in val: # format ISO8601 style for less ambiguity
            val = datetime.datetime.strptime(val, "%d/%m/%Y").strftime('%Y-%m-%d')
        ret['dates'][what] = val

    PPMisc_Contents = soup.find(id='PPMisc_Contents')
    ret['misc'] = parse_datalist( PPMisc_Contents.find('dl') )

    PPProc_Contents = soup.find(id='PPProc_Contents')
    ret['proc'] = parse_datalist( PPProc_Contents.find('dl') )

    PPLinked_Contents = soup.find(id='PPLinked_Contents')
    parsed = {}
    for what, val in parse_datalist(PPLinked_Contents.find('dl')).items():
        if type(val) is bs4.element.ResultSet:
            parsedval = []
            for li in val:
                a = li.find('a')
                parsedval.append(   (  'CELEX:'+a.get('data-celex'), ''.join( li.findAll(text=True) ).strip()  )   )
            parsed[what] = parsedval
        else:
            parsed[what] = val
    ret['linked'] = parsed

    PPDoc_Contents = soup.find(id='PPDoc_Contents')
    parsed = {}
    for what, val in parse_datalist(PPDoc_Contents.find('dl')).items():
        if type(val) is bs4.element.ResultSet:
            parsedval = []
            for li in val:
                a = li.find('a')
                parsedval.append(  li.text  ) # TODO: check that doesn't need to be a join-findall too
            parsed[what] = parsedval
        else:
            parsed[what] = val
    ret['doctrine'] = parsed

    PPClass_Contents = soup.find(id='PPClass_Contents')
    parsed = {}
    for what, val in parse_datalist(PPClass_Contents.find('dl')).items():
        if type(val) is bs4.element.ResultSet:
            parsedval = []
            for li in val:
                div = li.find('div')
                if div is not None:
                    parsedval.append(  list(s.strip()   for s in div.findAll(text=True)  if len(s.strip())>0 )  )
                else:
                    parsedval.append( ''.join( li.findAll(text=True) ).strip() )  
            parsed[what] = parsedval
        else:
            parsed[what] = val
    ret['classifications'] = parsed


    #Languages and formats available
    PP2Contents = soup.find(id='PP2Contents')
    contents = []
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
                    contents.append( (lang, format, 'https://eur-lex.europa.eu/legal-content/%s/TXT/%s/?uri=CELEX:%s'%(lang, format, celex)) )
    ret['contents'] = contents

    PP4Contents = soup.find(id='PP4Contents')
    TexteOnly = PP4Contents.find(id='TexteOnly')

    txt = []
    section_name, section_txt = '', []

    for node in TexteOnly.children:

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
            elif node.name in ('br',):
                pass # is nothing
            elif node.name in ('a',): # seem to be used mainly as anchors for browsers to #go to, so skippable
                if len(node.text.strip())>0:
                    raise ValueError("Bad assumption, that <a> has no text, in %r"%node) 
            else:
                raise ValueError( "Don't yet handle %r"%node.name  )

    if len(section_txt) > 0:
        txt.append( (section_name, section_txt) )
    section_name, section_txt = '', []
    
    ret['text'] = txt

    return ret
