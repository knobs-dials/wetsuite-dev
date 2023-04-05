''' A wrapper around ElementTree import, from lxml (only) because some of this code is lxml-specific.

    TODO: minimize the amount of "will break because lxml only", and add tests to try to break that
    
    Some general helpers.    
    ...including some helper functions shared by some debug scripts.

    CONSIDER: 
    - A "turn tree into nested dicts" function - see e.g. https://lxml.de/FAQ.html#how-can-i-map-an-xml-tree-into-a-dict-of-dicts
'''

#try: 
import lxml.etree
from lxml.etree import ElementTree,  fromstring, tostring,   register_namespace, Element, _Comment, _ProcessingInstruction 
#except  ImportError:
#from xml.etree import ElementTree 
#from xml.etree.ElementTree import fromstring, tostring,   register_namespace, Element, _Comment, _ProcessingInstruction



some_ns_prefixes = { 
    'http://www.w3.org/2000/xmlns/':'xmlns',
    'http://www.w3.org/2001/XMLSchema':'xsd',
    #'http://www.w3.org/2001/XMLSchema#':'xsd', # ?   Also, maybe avoid duplicate names? Except we are only doing this _only_ for pretty printing.

    'http://www.w3.org/XML/1998/namespace':'xml',

    'http://www.w3.org/2001/XMLSchema-instance':'xsi',
    'http://www.w3.org/1999/xhtml':'xhtml',
    'http://www.w3.org/1999/xlink':'xlink',
    'http://schema.org/':'schema',

    'http://www.w3.org/1999/02/22-rdf-syntax-ns#':'rdf',
    'http://www.w3.org/2000/01/rdf-schema':'rdfs',
    'http://www.w3.org/2000/01/rdf-schema#':'rdfs',
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

    'http://www.w3.org/1998/Math/MathML':'mathml', # more usually m: or mml: but this may be clearer

    'http://tuchtrecht.overheid.nl/':'tucht',
    'http://www.tweedekamer.nl/xsd/tkData/v1-0':'tk',
    'http://publications.europa.eu/celex/':'celex',
    'http://decentrale.regelgeving.overheid.nl/cvdr/':'cvdr',
    'http://psi.rechtspraak.nl/':'psi',
    'https://e-justice.europa.eu/ecli':'ecli',
    'http://www.rechtspraak.nl/schema/rechtspraak-1.0':'recht', # ?

    'http://standaarden.overheid.nl/owms/terms/':'overheid',
    'http://standaarden.overheid.nl/owms/terms':'overheid',  # maybe 'owms' would be clearer?
    
    'http://standaarden.overheid.nl/rijksoverheid/terms':'rijksoverheid',
    'http://standaarden.overheid.nl/inspectieloket/terms/':'inspectieloket',
    'http://standaarden.overheid.nl/bm/terms':'overheidbm',
   
    'http://standaarden.overheid.nl/buza/terms/':'overheidbuza',
    'http://standaarden.overheid.nl/oep/meta/':'overheidoep', # ?
    'http://standaarden.overheid.nl/op/terms/':'overheidop', # ?
    'http://standaarden.overheid.nl/vergunningen/terms/':'overheidvg',
    'http://standaarden.overheid.nl/product/terms/':'overheidproduct',
    'http://standaarden.overheid.nl/cvdr/terms/':'overheidrg',
    'http://standaarden.overheid.nl/vac/terms/':'overheidvac',

    'http://schemas.microsoft.com/ado/2007/08/dataservices':'ms-odata',
    'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata':'ms-odata-meta',
}
'some readable XML prefixes for friendlier display. Purely for pretty-printing, will NOT be according to the document definition. '
# It might be useful to find namespaces from many XML files:
#   locate .xml | tr '\n' '\0' | xargs -0 grep -oh 'xmlns:[^ >]*'
# with an eventual
#   | sort | uniq -c | sort -rn


def kvelements_to_dict(under, strip_text=True, ignore_tagnames=[]):
    ''' Where people use elements for single text values, it's convenient to get them as a dict.
        
        Given an etree element containing a series of such values,
        Returns a dict that is mostly just  { el.tag:el.text }
        Skips keys with empty values.
        
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
        if isinstance(ch, _Comment) or isinstance(ch, _ProcessingInstruction): 
            continue
        if ch.tag in ignore_tagnames:
            continue
        if ch.text is not None:
            text = ch.text
            if strip_text:
                text = text.strip()
            ret[ch.tag] = text
    return ret


def all_text_fragments(under, strip:str=None, ignore_empty:bool=False, ignore_tags=[], join:str=None):
    ''' Returns all fragments of text contained in a subtree, as a list of strings.
        
        Note that for free-form HTML-like documents, the best choices are more contextual than we'd like, 
          and this function does _not_ give enough  control.

        strip() is what to remove
        ignore_empty removes strings that are empty when called with strip(strip)

        ignore_tags does not currently ignore the subtree, just the direct (first) content.

        For example,  all_text_fragments( fromstring('<a>foo<b>bar</b></a>') ) == ['foo', 'bar']

        TODO: more tests, I'm moderately sure strip doesn't do quite what I think.
    '''
    ret = []
    for elem in under.iter(): # walks the subtree
        if isinstance(elem, _Comment) or isinstance(elem, _ProcessingInstruction): 
            continue
        #print("tag %r in ignore_tags (%r): %s"%(elem.tag, ignore_tags, elem.tag in ignore_tags))
        if elem.text != None:
            if elem.tag not in ignore_tags: # only ignore contents of ignored tags; tail is considered outside
                etss = elem.text.strip(strip)
                if ignore_empty and len(etss)==0:
                    pass
                else:
                    ret.append( etss )
        if elem.tail != None:
            etss = elem.tail.strip(strip)
            if ignore_empty and len(etss)==0:
                pass
            else:
                ret.append( etss )
    if join is not None:
        ret = join.join( ret )
    return ret


def strip_namespace(tree, remove_from_attr=True):
    ''' Returns a copy of a tree that has its namespaces stripped.

        More specifically it removes
        * namespace from element names
        * namespaces from attribute names (default, but optional)
        * default namespaces (TODO: test that properly)

        Note that for attributes with the same name, that are unique only because of a different namespace,
        this may cause attributes to be overwritten. 
        For example:   <e p:at="bar" at="quu">   would become   <e at="bar">
        I've not yet seen any XML where this matters - but it might.

        Returns the URLs for the stripped namespaces, in case you want to report them.
    '''
    if not isinstance(tree, lxml.etree._Element):
        import warnings
        warnings.warn("That tree does not seem to parsed by lxml, and having non-lxml objects can cause issues.  Please consider using lxml, e.g. via wetsuite.helpers.etree.fromstring().  Trying to work around this, which may be slow.")
        try:
            import xml.etree
            if isinstance(tree, xml.etree.ElementTree.Element):
                tree = lxml.etree.fromstring( xml.etree.ElementTree.tostring( tree ) )  # copy it the dumb way - could possibly be done faster?
            # implied else: hope for the best                
        except ImportError as ie:
            pass # no fix for you, then.
        _strip_namespace_inplace(tree, remove_from_attr=remove_from_attr)
    else:
        import copy
        tree = copy.deepcopy( tree ) # assuming this is enough.  Should verify with lxml and etree implementation
        _strip_namespace_inplace(tree, remove_from_attr=remove_from_attr)
    return tree


def _strip_namespace_inplace(tree, remove_from_attr=True):
    ''' Takes a parsed ET structure and does an in-place removal of all namespaces.
        Returns a list of removed namespaces, which you can usually ignore.
        No longer meant to be used directly - mostly to help centralize a check for non-lxml etrees, feel free to use it if you stick to lxml.
    '''
    ret = {}
    for elem in tree.iter():
        if isinstance(elem, _Comment): # won't have a .tag to have a namespace in,
            continue # so we can ignore it
        if isinstance(elem, _ProcessingInstruction): # won't have a .tag to have a namespace in,
            continue # so we can ignore it
        tagname = elem.tag
        if tagname[0]=='{':
            elem.tag = tagname[ tagname.index('}',1)+1: ]
        if remove_from_attr:
            to_delete = []
            to_set    = {}
            for attr_name in elem.attrib:
                if attr_name[0]=='{':
                    urlendind = attr_name.index('}', 1)
                    ret[ attr_name[1:urlendind] ] = True
                    old_val = elem.attrib[attr_name]
                    to_delete.append( attr_name )
                    attr_name = attr_name[urlendind+1:]
                    to_set[attr_name] = old_val
            for delete_key in to_delete:
                elem.attrib.pop( delete_key )
            elem.attrib.update( to_set )
    lxml.etree.cleanup_namespaces( tree ) # remove unused namespace declarations. Will only work on lxml etree objects, hence the code above.
    return ret


def indent(tree, whitespacestrip=True):
    ''' Returns a copy of a tree, with text so that it would print indented by depth. 

        Keep in mind that this may change the meaning of the document - the output should _only_ be used for presentation.

        whitespacestrip can make contents that contain a lot of newlines look cleaner, 
        but changes the stored data even more.

        See also _indent_inplace()
    '''
    import copy
    newtree = copy.deepcopy( tree )
    _indent_inplace(newtree, level=0, whitespacestrip=whitespacestrip)
    return newtree


def _indent_inplace(elem, level=0, whitespacestrip=True):
    ''' Alters the text nodes so that the tostring()ed version will look nice and indented when printed as plain text.
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
            _indent_inplace(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i



def path_between(under, element):
    ''' Given an ancestor and a descentent element from the same tree
          (In many applications you want under to be the the root element)

        Returns the xpath-style path to get from (under) to this specific element
             ...or raises a ValueError mentioning that the element is not in this tree

        Keep in mind that if you reformat a tree, the latter is likely.

        This function has very little code, and if you do this for much of a document, you may want to steal the code
    '''
    letree = lxml.etree.ElementTree( under )
    return letree.getpath( element )




def node_walk(under, max_depth=None):  # Based on https://stackoverflow.com/questions/60863411/find-path-to-the-node-using-elementtree
    ''' Walks all elements under the given element,  remembering both path string and element reference as we go.
        (note that this is not an xpath style with specific indices, just the names of the elements)

        If given None, it emits nothing (we assume it's from a find() that hit nothing, and that it's easier to ignore here than in your code)

        Is a generator yielding (path, element),   and is mainly a helper used by path_count()

        TODO: re-test now that I've added max_depth, because I'm not 100% on the details
    '''
    if under is None:
        return
    path_to_element = []
    element_stack = [under]
    while len(element_stack) > 0:
        element = element_stack[-1]
        if len(path_to_element) > 0  and  element is path_to_element[-1]:
            path_to_element.pop()
            element_stack.pop()
            yield (path_to_element, element)
        else:
            path_to_element.append( element )
            for child in reversed( element ):
                if max_depth is None or (max_depth is not None and len(path_to_element) < max_depth):
                    element_stack.append( child )
                


def path_count(under, max_depth=None):
    ''' Walk nodes under an etree element,
          count how often each path happens (counting the complete path string).
          written to summarize the rough structure of a document.

        Returns a dict from path strings to their count
    '''
    count = {}
    for node_path, n in node_walk( under, max_depth=max_depth ):
        if isinstance(n, _Comment) or isinstance(n, _ProcessingInstruction): 
            continue # ignore things that won't have a .tag
        path = "/".join([n.tag  for n in node_path] + [n.tag] )  # includes `under`` element, which is a little redundant, but more consistent
        if path not in count:
            count[ path ] = 1
        else:
            count[ path ] += 1
    return count    



