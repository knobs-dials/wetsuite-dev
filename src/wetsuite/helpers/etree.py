''' Is 
    - a wrapper around ElementTree import,
    - some general helpers.
    - including some helper functions shared by some debug scripts.


    CONSIDER: 
    - A "turn tree into nested dicts" function - see e.g. https://lxml.de/FAQ.html#how-can-i-map-an-xml-tree-into-a-dict-of-dicts
'''

# TODO: evaluate how different/better lxml is, and maybe don't fall back to avoid confusion?
try: 
    from lxml.etree import ElementTree,  fromstring, tostring,   register_namespace, Element, _Comment, _ProcessingInstruction 
except  ImportError:
    from xml.etree import ElementTree 
    from xml.etree.ElementTree import fromstring, tostring,   register_namespace, Element, _Comment, _ProcessingInstruction



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
    
    'http://standaarden.overheid.nl/owms/terms':'overheid',  # maybe 'owms' would be clearer?
    'http://standaarden.overheid.nl/oep/meta/':'overheidop', # ?
}
'some readable XML prefixes for friendlier display. Purely for pretty-printing, not according to the document definition. '
# It might be useful to find namespaces from many XML files:
#   locate .xml | tr '\n' '\0' | xargs -0 grep -oh 'xmlns:[^ >]*'
# with an eventual
#   | sort | uniq -c | sort -rn


def kvelements_to_dict(under, strip_text=True):
    ''' Where people use elements for single text values, it's convenient to get them as a dict.
        
        Given an etree object,
        Returns a dict that is mostly just  { el.tag:el.text }
        
        Would for example turn
            <foo>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp/>
            </foo>
        into:
            {'identifier':'BWBR0001840', 'title':'Grondwet'}
    '''
    ret = {}
    for ch in under:
        if ch.text is not None:
            text = ch.text
            if strip_text:
                text = text.strip()
            ret[ch.tag] = text
    return ret



def all_text_fragments(under, ignore_empty=False, ignore_tags=[]):
    ''' Returns all fragments of text contained in a subtree, as a list of strings

        ignore_tags does not currently ignore the subtree, just the direct contents

        For example:

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



def strip_namespace(tree, namespace=None, remove_from_attr=True):
    ''' Returns a copy of a tree, with namespaces stripped.
        See strip_namespace_inplace for the parameters.
    '''
    # There may be a slightly faster way of doing this in one go?
    import copy
    newtree = copy.deepcopy( tree ) # assuming this is enough.  Should verify with lxml and etree implementation
    strip_namespace_inplace(newtree, namespace=namespace, remove_from_attr=remove_from_attr)
    return newtree


def strip_namespace_inplace(etree, namespace=None, remove_from_attr=True):
    ''' Takes a parsed ET structure and does an in-place removal of all namespaces,
        or removes a specific namespace (by its URL - and it needs to be exact,
        we don't do anything clever like dealing with final-slash differences).
 
        Can make node searches simpler in structures with unpredictable namespaces
        and in content given to be non-mixed.
 
        By default does so for node names as well as attribute names.       
        (doesn't remove the namespace definitions, but apparently
         ElementTree serialization omits any that are unused)

        Note that for attributes that are unique only because of namespace, this may cause attributes to be overwritten. 
        For example: <e p:at="bar" at="quu">   would become: <e at="bar">
        I don't think I've yet seen any XML where this matters, though.

        Returns the URLs for the stripped namespaces, in case you want to report them.

        CONSIDER: 
        - remove all (applicalbe) 'xmlns' and 'xmlns:*' attributes.  They're not in the way, but unused namespaces can be confusing.

    '''
    ret = {}
    if namespace==None: # all namespaces                               
        for elem in etree.getiterator():
            if isinstance(elem, _Comment): # won't have a .tag to have a namespace in.
                continue
            if isinstance(elem, _ProcessingInstruction): # won't have a .tag to have a namespace in.
                continue
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
            if isinstance(elem, _Comment):
                continue
            if isinstance(elem, _ProcessingInstruction):
                continue
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


def indent(tree, whitespacestrip=True):
    ''' Returns a copy of a tree, with text so that it would print indented by depth. 

        See also indent_inplace()
    '''
    import copy
    newtree = copy.deepcopy( tree )
    indent_inplace(newtree, level=0, whitespacestrip=whitespacestrip)
    return newtree


def indent_inplace(elem, level=0, whitespacestrip=True):
    ''' Alters the text nodes so that the tostring()ed version will look nice and indented.
    
        Keep in mind that this may change the meaning of the document - the output should _only_ be used for presentation.
 
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


def node_walk(root):  # https://stackoverflow.com/questions/60863411/find-path-to-the-node-using-elementtree
    ''' walks all nodes, in a way where we remember both path and node.
        Is a generator yieldng (path, node)

        Mainly a helper for path_count()
    '''
    path_to_node = []
    node_stack = [root]
    while node_stack:
        node = node_stack[-1]
        if path_to_node  and  node is path_to_node[-1]:
            path_to_node.pop()
            node_stack.pop()
            yield (path_to_node, node)
        else:
            path_to_node.append(node)
            for child in reversed(node):
                node_stack.append(child)


def path_count(root):
    ''' Count how often each path happens, under a specific root node.
        Meant to help grasp the structure of documents.

        Returns a dict from path strings to their count
    '''
    count = {}
    for node_path, n in node_walk( root ):
        path = "/".join([n.tag for n in node_path] + [n.tag]) # includes root, which is a little redundant, but more consistent
        if path not in count:
            count[ path ] = 1
        else:
            count[ path ] += 1
    return count    





