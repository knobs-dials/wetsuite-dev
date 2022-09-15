

from xml.etree import ElementTree 

from xml.etree.ElementTree import fromstring, tostring,   register_namespace, Element  # aliases for things I commonly use



# common namespaces and the prefix often used for it - or I prefer for arbitrary reasons.
#   The prefixes are not according to the document definition, they are purely for pretty-printing
# Sources:
some_ns_prefixes = { 
    'http://www.w3.org/2000/xmlns/':'xmlns',
    'http://www.w3.org/2001/XMLSchema':'xsd',
    #'http://www.w3.org/2001/XMLSchema#':'xsd', # ?   Also, maybe avoid duplicate names? Except we _explicitly_ are only doing this for pretty printing.

    'http://www.w3.org/XML/1998/namespace':'xml',

    'http://www.w3.org/2001/XMLSchema-instance':'xsi',
    'http://www.w3.org/1999/xhtml':'xhtml',
    'http://www.w3.org/1999/xlink':'xlink',
    'http://schema.org/':'schema',

    'http://www.w3.org/1999/02/22-rdf-syntax-ns#':'rdf',
    'http://www.w3.org/2000/01/rdf-schema':'rdfs',
    'http://www.w3.org/ns/rdfa#':'rdfa',
    'http://purl.org/dc/terms/':'dcterms', #cf dc, see also https://stackoverflow.com/questions/47519315/what-is-the-difference-between-dublin-core-terms-and-dublin-core-elements-vocabu
    'http://purl.org/dc/elements/1.1/':'dc',

    'http://www.w3.org/TR/vocab-regorg/':'rov',
    'http://www.w3.org/TR/vocab-org/':'org',
    'http://www.w3.org/2004/02/skos/core#':'skos',
    'http://www.w3.org/2002/07/owl#':'owl',
    'http://ogp.me/ns#':'og',

    'http://www.w3.org/2001/XInclude':'xi',
    'http://www.w3.org/1999/XSL/Transform':'xsl', # there seem to be multiple. See also http://www.w3.org/XSL/Transform/1.0 and http://www.w3.org/TR/WD-xsl ?
    #'http://icl.com/saxon':'saxon',
    #'http://xml.apache.org/xslt':'xalan',
    'http://www.w3.org/1999/XSL/Format':'fo',
    'http://www.w3.org/2003/g/data-view#':'grddl',
    'http://xmlns.com/foaf/0.1/':'foaf',
    'http://purl.org/rss/1.0/modules/content/':'content',
    'http://rdfs.org/sioc/ns#':'sioc',
    'http://rdfs.org/sioc/types#':'sioct',
    'http://www.w3.org/ns/locn':'locn',
    'http://www.w3.org/2000/svg':'svg',

    'http://www.w3.org/2005/Atom':'atom',

    'http://www.w3.org/1998/Math/MathML':'mathml', # more usually m: or mml:

    'http://tuchtrecht.overheid.nl/':'tucht',     # maybe tr
    'http://publications.europa.eu/celex/':'celex',
    'http://decentrale.regelgeving.overheid.nl/cvdr/':'cvdr',
    'http://psi.rechtspraak.nl/':'psi', 
    'https://e-justice.europa.eu/ecli':'ecli',
    'http://www.rechtspraak.nl/schema/rechtspraak-1.0':'recht', # ?
    
    'http://standaarden.overheid.nl/owms/terms':'overheid',  # or owms
    'http://standaarden.overheid.nl/oep/meta/':'overheidop', # ?

    
    #'https://zoek.officielebekendmakingen.nl/':'op', # ?

    # locate .xml | tr '\n' '\0' | xargs -0 grep -oh 'xmlns:[^ >]*'
}



def kvelements_to_dict(under):
    ''' Where people use elements for single text values, it's convenient to get them as a dict.
        For example, would turn
            <foo>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp/>
            </foo>
        into:
            {'identifier':'BWBR0001840', 'title':'Grondwet'}
        (via el.tag:el.text)
    '''
    ret = {}
    for ch in under:
        if ch.text is not None:
            ret[ch.tag] = ch.text.strip()
    return ret


# https://lxml.de/FAQ.html#how-can-i-map-an-xml-tree-into-a-dict-of-dicts            
#def recursive_dict(element):
#     return element.tag, dict(map(recursive_dict, element)) or element.text


def all_text_fragments(under, ignore_empty=False, ignore_tags=[]):
    ''' Returns all fragments of text contained in a subtree, as a list of strings
        ignore_tags does not currently ignore the subtree, just the direct contents
    '''
    r = []
    for e in under.getiterator(): # walks the subtree
        if e.tag in ignore_tags:
            #print('IGNORE', e.tag)
            continue
        if e.text != None:
            if not (ignore_empty and len(e.text.strip())==0):
                r.append( e.text )
        if e.tail != None:
            if not (ignore_empty and len(e.tail.strip())==0):
                r.append( e.tail )
    return r



def strip_namespace_inplace(etree, namespace=None,remove_from_attr=True):
    """ Takes a parsed ET structure and does an in-place removal of all namespaces,
        or removes a specific namespace (by its URL - and it needs to be exact,
        we don't do anything clever like dealing with final-slash differences).
 
        Can make node searches simpler in structures with unpredictable namespaces
        and in content given to be non-mixed.
 
        By default does so for node names as well as attribute names.       
        (doesn't remove the namespace definitions, but apparently
         ElementTree serialization omits any that are unused)
 
        Note that for attributes that are unique only because of namespace,
        this may attributes to be overwritten. 
        For example: <e p:at="bar" at="quu">   would become: <e at="bar">
 
        I don't think I've seen any XML where this matters, though.

        Returns the URLs for the stripped namespaces, in case you want to report them.
    """
    ret = {}
    if namespace==None: # all namespaces                               
        for elem in etree.getiterator():
            tagname = elem.tag
            if tagname[0]=='{':
                elem.tag = tagname[ tagname.index('}',1)+1:]
 
            if remove_from_attr:
                to_delete=[]
                to_set={}
                for attr_name in elem.attrib:
                    if attr_name[0]=='{':
                        urlendind=attr_name.index('}',1)
                        ret[ attr_name[1:urlendind] ] = True
                        old_val = elem.attrib[attr_name]
                        to_delete.append(attr_name)
                        attr_name = attr_name[urlendind+1:]
                        to_set[attr_name] = old_val
                for key in to_delete:
                    elem.attrib.pop(key)
                elem.attrib.update(to_set)
 
    else: # asked to remove single specific namespace.
        ns = '{%s}' % namespace
        nsl = len(ns)
        for elem in etree.getiterator():
            if elem.tag.startswith(ns):
                elem.tag = elem.tag[nsl:]
 
            if remove_from_attr:
                to_delete=[]
                to_set={}
                for attr_name in elem.attrib:
                    if attr_name.startswith(ns):
                        old_val = elem.attrib[attr_name]
                        to_delete.append(attr_name)
                        ret[ attr_name[1:nsl-1] ] = True
                        attr_name = attr_name[nsl:]
                        to_set[attr_name] = old_val
                for key in to_delete:
                    elem.attrib.pop(key)
                elem.attrib.update(to_set)

    return ret


def indent_inplace(elem, level=0, whitespacestrip=True):
    ''' Alters the text nodes so that the tostring()ed version will look nice and indented.
 
        whitespacestrip can make contents that contain a lot of newlines look cleaner, 
        but changes the stored data even more.
    '''
    i = "\n" + level*"  "
 
    if whitespacestrip:
        if elem.text:
            elem.text=elem.text.strip()
        if elem.tail:
            elem.tail=elem.tail.strip()
 
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_inplace(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
