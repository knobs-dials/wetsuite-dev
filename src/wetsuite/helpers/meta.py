''' Some metadata helpers that we expect to be reusable, anything that isn't tied to a singular API or data source.

    Function name should give you some indication how what it belongs to and how specific it is.
'''
import re, collections, urllib.parse


_jcifind_re  = re.compile(r'(?:jci)?([0-9.]+):([a-z]):(BWB[RV][0-9]+)([^\s;"\']*)' ) # not meant for finding in free-form text
_eclifind_re = re.compile(r'ECLI:[A-Za-z]{2}:[A-Z-z0-9.]{1,7}:[0-9]{,4}:[A-Z-z0-9.]{,25}')


def parse_jci(text: str):
    """ Takes something in the form of jci{version}:{type}:{BWB-id}{key-value}*
          e.g. jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3.1
        Returns something like
          {'version': '1.31', 'type': 'c', 'bwb': 'BWBR0012345', 'params': {'g': ['2005-01-01'], 'artikel': ['3.1']}}

        Notes:
        - params is actually an an OrderedDict, so you can also fetch them in the order they appeared, for the cases where that matters.
        - tries to be robust to a few non-standard things we've seen in real use
        - for type=='c' (single consolidation), expected params include
            g  geldigheidsdatum
            z  zichtdatum
        - for type=='v' (collection), expected params include
            s  start of geldigheid
            e  end of geldigheid
            z  zichtdatum
        Note that precise interpretation, and generation of these links, is a little more involved,
        in that versions made small semantic changes to the meanings of some parts.
    """
    ret = {}
    m = _jcifind_re.match( text )
    if m is None:
        raise ValueError('%r does not look like a valid jci'%text)
    else:
        version, typ, bwb, rest = m.groups()
        ret['version'] = version
        ret['type']    = typ
        ret['bwb']     = bwb
        # The jci standard doesn't seem to make it clear whether it's supposed to be a conformant URL or URN, so it's unsure whether there is specific parameter encoding.
        #   The below is somewhat manual, but might prove more robust then just   d['params']  = urllib.parse.parse_qs(rest)
        params = collections.OrderedDict()
        for param in rest.split('&'):
            pd = urllib.parse.parse_qs(param)
            for key in pd:
                out_key = key
                if key.startswith('amp;'):    # this variation seems to be a fairly common mistake in general, so try to be robust to it
                    out_key = key[4:]         #   ...though it may well be better to handle this earlier in the function
                if key not in params:
                    params[out_key] = pd[key]
                else:
                    params[out_key].extend( pd[key] )
        ret['params'] = params

    return ret



# CONSIDER: adding the lists of dutch courts. It might change over time, but is still useful.


def findall_ecli(s:str, rstrip_dot=True):
    ''' Within plain text, this tries to find all occurences of things that look like an ECLI identifier
        Returns a list of strings.

        rstrip_dot - whether to return the match stripped of any final dot(s).
           While dots are valid in an ECLI (typically used as a separator),
             it is more likely that a dot on the end is an ECLI into a sentence than it is to be part of the ECLI.
           This stripping is enabled by default, but it would be more correct for you to always control this parameter,
             and for well-controlled metadata fields it may be more correct to use False.
    '''
    ret = []
    for match_str in _eclifind_re.findall( s ):
        if rstrip_dot:
            match_str = match_str.rstrip('.')
        ret.append( match_str )
    return ret 


def parse_ecli(text:str):
    ''' mostly just reports the parts in a dict - I don't actually see much use over .split(':')

    '''
    ret = {}
    ecli_list = text.strip().split(':')
    if len(ecli_list) != 5:
        raise ValueError("ECLI is expected to have five elements separated by four colons, %r does not"%text)
    
    ECLI, country_code, court_code, year, caseid = ecli_list
    if ECLI.upper() != 'ECLI':
        raise ValueError("First ECLI string isn't 'ECLI' in %r"%text)

    if len(country_code)!=2:
        raise ValueError("ECLI country %s isn't two characters"%country_code)

    #if len(court):

    # caseod    seems to be [A-Z-z0-9.]{,25} but countries usually keep shorter and structured, and may have historical numbering sorted in, etc.

    ret['country_code'] = country_code
    ret['court_code'] = court_code
    ret['year'] = year
    ret['caseid'] = caseid
    # TODO: court codes

    #if court_code in nl_court_codes:
    #    ret['court_name'] = nl_court_codes[court_code]

    return ret






# member countries slowly change over time, of course, so maybe we should just accept any three letters,
#  or more pragmatically, any existing nearby country?
CELEX_COUNTRIES = [ 
    'BEL', 'DEU', 'FRA', 'CZE', 'ESP', 'PRT', 'AUT', 'CYP', 'BGR', 'EST', 'FIN', 'GBR', 'HUN', 'IRL', 
    'LTU', 'MLT', 'LVA', 'SVN', 'SWE', 'GRC,' 'POL', 'DNK', 'ITA', 'LUX', 'NLD', 'SVK', 'ROU', 'HRV',
]

CELEX_SECTORS = {
    '1':'Treaties',
    '2':'External Agreements',
    '3':'Legislation',
    '4':'Internal Agreements',
    '5':'Proposals + other preparatory documents',
    '6':'Case Law',
    '7':'National Implementation',
    '8':'National Case Law',
    '9':'Parliamentary Questions',
    '0':'Consolidated texts',
    'C':'OJC Documents',
    'E':'EFTA Documents',
}

# https://eur-lex.europa.eu/content/tools/TableOfSectors/types_of_documents_in_eurlex.html

CELEX_DOCTYPES = (
    ('1', 'K', 'Treaty establishing the European Coal and Steel Community (ECSC Treaty) 1951'),
    ('1', 'A', 'Treaty establishing the European Atomic Energy Community (EAEC Treaty or Euratom) (1957); Euratom Treaty consolidated versions (2010, 2012, 2016)'),
    ('1', 'E', 'Treaty establishing the European Economic Community (EEC Treaty or Treaty of Rome) (1957); Treaty establishing the European Community (TEC or EC Treaty) Maastricht consolidated version (1992), Amsterdam consolidated version (1997), Nice consolidated version (2002) and Athens consolidated version (2006); Treaty on the Functioning of the European Union (TFEU) consolidated versions (2008, 2010, 2012, 2016)'),
    ('1', 'F', 'Merger Treaty or Treaty of Brussels (1965); Treaty amending certain budgetary provisions or Treaty of Luxembourg (1970)'),
    ('1', 'B', 'Treaty of Accession of Denmark, Ireland, Norway* and the United Kingdom (1972)'),
    ('1', 'R', 'Treaty amending certain financial provisions (1975); Treaty amending certain provisions of the Protocol on the Statute of the European Investment Bank (1975)'),
    ('1', 'H', 'Treaty of Accession of Greece (1979)'),
    ('1', 'I', 'Treaty of Accession of Spain and Portugal (1985)'),
    ('1', 'G', 'Greenland Treaty (1985)'),
    ('1', 'U', 'Single European Act (SEA) 1986'),
    ('1', 'M', 'Treaty on the European Union (TEU or Treaty of Maastricht) consolidated versions (1992, 1997, 2002, 2006, 2008, 2010, 2012, 2016); Treaty of Amsterdam consolidated version (1997); Treaty of Nice consolidated version (2002); Treaty of Athens consolidated version (2006); Treaty of Lisbon consolidated versions (2008, 2010, 2012)'),
    ('1', 'N', 'Treaty of Accession of Austria, Finland and Sweden (1994)'),
    ('1', 'D', 'Treaty of Amsterdam (1997)'),
    ('1', 'C', 'Treaty of Nice (2001)'),
    ('1', 'T', 'Treaty of Accession of the Czech Republic, Estonia, Cyprus, Latvia, Lithuania, Hungary, Malta, Poland, Slovenia and Slovakia (2003)'),
    ('1', 'V', 'Treaty establishing a Constitution for Europe (2004)'),
    ('1', 'S', 'Treaty of Accession of the Republic of Bulgaria and Romania (2005)'),
    ('1', 'L', 'Treaty of Lisbon (2007)'),
    ('1', 'P', 'Charter of Fundamental Rights of the European Union consolidated versions (2007, 2010, 2012, 2016)'),
    ('1', 'J', 'Treaty of Accession of Croatia (2012)'),
    ('1', 'W', 'EU-UK Withdrawal agreement (2019)'),
    ('1', 'X', 'Treaty amending certain provisions of the Protocol on the Statute of the European Investment Bank (1975)'),
    ('1', 'ME','Consolidated versions of the Treaty on the European Union (TEU or Treaty of Maastricht) and Treaty on the Functioning of the European Union (TFEU) 2016'),

    ('2', 'A', 'Agreements with non-member States or international organisations'),
    ('2', 'D', 'Acts of bodies created by international agreements'),
    ('2', 'P', 'Acts of parliamentary bodies created by international agreements'),
    ('2', 'X', 'Other acts'),

    ('3', 'E', 'CFSP: common positions; joint actions; common strategies (pre-Lisbon title V of EU Treaty)'),
    ('3', 'F', 'Police and judicial co-operation in criminal matters (pre-Lisbon title VI of EU Treaty)'),
    ('3', 'R', 'Regulations'),
    ('3', 'L', 'Directives'),
    ('3', 'D', 'Decisions (with or without addressee)'),
    ('3', 'S', 'ECSC Decisions of general interest'),
    ('3', 'M', 'Non-opposition to a notified concentration'),
    ('3', 'J', 'Non-opposition to a notified joint venture'),
    ('3', 'B', 'Budget'),
    ('3', 'K', 'ECSC recommendations'),
    ('3', 'O', 'ECB guidelines'),
    ('3', 'H', 'Recommendations'),
    ('3', 'A', 'Opinions'),
    ('3', 'G', 'Resolutions'),
    ('3', 'C', 'Declarations'),
    ('3', 'Q', 'Institutional arrangements: Rules of procedure; Internal agreements'),
    ('3', 'X', 'Other documents published in OJ L (or pre-1967)'),
    ('3', 'Y', 'Other documents published in OJ C'),

    ('4', 'A', 'Agreements between Member States'),
    ('4', 'D', 'Decisions of the representatives of the governments of the Member States'),
    ('4', 'X', 'Other acts published in OJ L'),
    ('4', 'Y', 'Other acts published in OJ C'),
    ('4', 'Z', 'Complementary legislation'),

    ('5', 'AG', 'Council and MS - Council positions and statement of reasons'),
    ('5', 'KG', 'Council and MS - Council assents (ECSC Treaty)'),
    ('5', 'IG', 'Council and MS - Member States – initiatives'),
    ('5', 'XG', 'Council and MS - Other documents of the Council or the Member States'),
    ('5', 'PC', 'European Commission - COM – legislative proposals, and documents related'),
    ('5', 'DC', 'European Commission - Other COM documents (green papers, white papers, communications, reports, etc.)'),
    ('5', 'JC', 'European Commission - JOIN documents'),
    ('5', 'SC', 'European Commission - SEC and SWD documents'),
    ('5', 'EC', 'European Commission - Proposals of codified versions of regulations'),
    ('5', 'FC', 'European Commission - Proposals of codified versions of directives'),
    ('5', 'GC', 'European Commission - roposals of codified versions of decisions'),
    ('5', 'M', 'European Commission - Merger control documents'),
    ('5', 'AT', 'European Commission - Antitrust'),
    ('5', 'AS', 'European Commission - State aid'),
    ('5', 'XC', 'European Commission - Other documents of the Commission'),
    ('5', 'AP', 'European Parliament - Legislative resolutions of the EP'),
    ('5', 'BP', 'European Parliament - Budget (EP)'),
    ('5', 'IP', 'European Parliament - Other resolutions and declarations of the EP'),
    ('5', 'DP', 'European Parliament - Internal decisions of the EP'),
    ('5', 'XP', 'European Parliament - Other documents of the EP'),
    ('5', 'AA', 'European Court of Auditors - ECA Opinions'),
    ('5', 'TA', 'European Court of Auditors - ECA Reports'),
    ('5', 'SA', 'European Court of Auditors - ECA Special reports'),
    ('5', 'XA', 'European Court of Auditors - Other documents of the ECA'),
    ('5', 'AB', 'European Central Bank - ECB Opinions'), 
    ('5', 'HB', 'European Central Bank - ECB Recommendations'), 
    ('5', 'XB', 'European Central Bank - Other documents of the ECB'), 
    ('5', 'AE', 'European Economic and Social Committee - EESC Opinions on consultation'), 
    ('5', 'IE', 'European Economic and Social Committee - EESC Own-initiative opinions'), 
    ('5', 'AC', 'European Economic and Social Committee - EESC Opinions'), 
    ('5', 'XE', 'European Economic and Social Committee - Other documents of the EESC'), 
    ('5', 'AR', 'European Committee of the Regions - CoR Opinions on consultation'), 
    ('5', 'IR', 'European Committee of the Regions - CoR Own-initiative opinions'), 
    ('5', 'XR', 'European Committee of the Regions - Other documents of the CoR'), 
    ('5', 'AK', 'ECSC Commitee - ECSC Consultative Committee Opinions'), 
    ('5', 'XK', 'ECSC Commitee - Other documents of the ECSC Committee'), 
    ('5', 'XX', 'Other organs - Other documents'), 

    ('6', 'CJ', 'Court of Justice - Judgment'),
    ('6', 'CO', 'Court of Justice - Order'),
    ('6', 'CC', 'Court of Justice - Opinion of the Advocate-General'),
    ('6', 'CS', 'Court of Justice - Seizure'),
    ('6', 'CT', 'Court of Justice - Third party proceeding'),
    ('6', 'CV', 'Court of Justice - Opinion'),
    ('6', 'CX', 'Court of Justice - Ruling'),
    ('6', 'CD', 'Court of Justice - Decision'),
    ('6', 'CP', 'Court of Justice - View'),
    ('6', 'CN', 'Court of Justice - Communication: new case'),
    ('6', 'CA', 'Court of Justice - Communication: judgment'),
    ('6', 'CB', 'Court of Justice - Communication: order'),
    ('6', 'CU', 'Court of Justice - Communication: request for an opinion'),
    ('6', 'CG', 'Court of Justice - Communication: opinion'),
    ('6', 'TJ', 'General Court (pre-Lisbon: Court of First Instance) - Judgment'),
    ('6', 'TO', 'General Court (pre-Lisbon: Court of First Instance) - Order'),
    ('6', 'TC', 'General Court (pre-Lisbon: Court of First Instance) - Opinion of the Advocate-General'),
    ('6', 'TT', 'General Court (pre-Lisbon: Court of First Instance) - Third party proceeding'),
    ('6', 'TN', 'General Court (pre-Lisbon: Court of First Instance) - Communication: new case'),
    ('6', 'TA', 'General Court (pre-Lisbon: Court of First Instance) - Communication: judgment'),
    ('6', 'TB', 'General Court (pre-Lisbon: Court of First Instance) - Communication: order'),
    ('6', 'FJ', 'Civil Service Tribunal - Judgment'),
    ('6', 'FO', 'Civil Service Tribunal - Order'),
    ('6', 'FT', 'Civil Service Tribunal - Third party proceeding'),
    ('6', 'FN', 'Civil Service Tribunal - Communication: new case'),
    ('6', 'FA', 'Civil Service Tribunal - Communication: judgment'),
    ('6', 'FB', 'Civil Service Tribunal - Communication: order'),

    ('7', 'L', 'National measures to transpose directives'),
    ('7', 'F', 'National measures to transpose framework decisions'),

    ('8', 'BE', 'Belgium'),
    ('8', 'BG', 'Bulgaria'),
    ('8', 'CZ', 'Czech Republic'),
    ('8', 'DK', 'Denmark'),
    ('8', 'DE', 'Germany'),
    ('8', 'EE', 'Estonia'),
    ('8', 'IE', 'Ireland'),
    ('8', 'EL', 'Greece'),
    ('8', 'ES', 'Spain'),
    ('8', 'FR', 'France'),
    ('8', 'HR', 'Croatia'),
    ('8', 'IT', 'Italy'),
    ('8', 'CY', 'Cyprus'),
    ('8', 'LV', 'Latvia'),
    ('8', 'LT', 'Lithuania'),
    ('8', 'LU', 'Luxembourg'),
    ('8', 'HU', 'Hungary'),
    ('8', 'MT', 'Malta'),
    ('8', 'NL', 'Netherlands'),
    ('8', 'AT', 'Austria'),
    ('8', 'PL', 'Poland'),
    ('8', 'PT', 'Portugal'),
    ('8', 'RO', 'Romania'),
    ('8', 'SI', 'Slovenia'),
    ('8', 'SK', 'Slovakia'),
    ('8', 'FI', 'Finland'),
    ('8', 'SE', 'Sweden'),
    ('8', 'UK', 'United Kingdom'),
    ('8', 'CH', 'Switzerland'),
    ('8', 'IS', 'Iceland'),
    ('8', 'NO', 'Norway'),
    ('8', 'XX', 'Other countries, EFTA Court, European Court of Human Rights'),

    ('9', 'E', 'Written questions'),
    ('9', 'H', 'Questions at question time'),
    ('9', 'O', 'Oral questions'),

    ('E', 'A', 	'Agreements between EFTA Member States'),
    ('E', 'C',  'Acts of the EFTA Surveillance Authority'),
    ('E', 'G',  'Acts of the EFTA Standing Committee'),
    ('E', 'J',  'Decisions, orders, consultative opinions of the EFTA Court'),
    ('E', 'P',  'Pending cases of the EFTA Court'),
    ('E', 'X',  'Information and communications'),
    ('E', 'O',  'Other acts'),
)

def _celex_doctype(sector_number:str, document_type:str):
    ' helper to search in CELEX_DOCTYPES.  Returns None if nothing matches. '
    # keep in mind that sector number isn't a number (see C and E)
    for d_sn, d_dt, d_descr in CELEX_DOCTYPES:
        if d_sn == sector_number and d_dt == document_type:
            return d_descr
    return None


def equivalent_celex(celex1:str, celex2:str):
    ''' Do two CELEX identifiers refer to the same document? 
    
        Currently:
        - ignores sector to be able to ignore sector 0
        - tries to ingore
        This is currently based on estimation - we should read up on 

        Also note that this will 
    '''
    d1 = parse_celex( celex1 )
    d2 = parse_celex( celex2 )
    return d1[ 'id' ][1:] == d2[ 'id' ][1:]



_re_celex = re.compile( r'([1234567890CE])([0-9]{4})([A-Z][A-Z]?)([0-9\(\)]+)([^\s&.]*)?' )
#_re_celex = re.compile( r'([1234567890CE])([0-9]{4})([A-Z][A-Z]?)([0-9\(\)]+)([A-Z0-9\(\)_]*)?' )



def parse_celex(celex: str):
    ''' Normalize a CELEX number
            (e.g. strips a 'CELEX:' in front)
        Describes its parts in more readable form, where possible.
        All values are returned as strings, even where they are (ostensibly) numbers.

        Returns a dict detailing the parts.  NOTE that the details will change when I actually read the specs properly
        - norm is what you fed in, uppercased, and with an optional 'CELEX:' stripped
          but otherwise untouched
        - id is recoposed from sector_number, year, document_type, document_number
          which means it is stripped of additions - it may strip more than you want!

        Keep in mind that this will _not_ resolve things like "go to the consolidated version" like the EUR-Lex site will do

        TODO: read the spec, because I'm not 100% on 
         - sector 0
         - sector C
         - whether additions like (01) in e.g. 32012A0424(01) are part of the identifier or not
            (...yes. Theyse are unique documents) 
         - national transposition
         - if you have multiple additions like '(01)' and '-20160504' and 'FIN_240353',
           ...what order they should appear in
        
        TODO: we might be able to assist common in those cases (e.g. a test for "is this equivalent").
              I e.g. do not know whether id_nonattrans is useful or correct
    '''
    norm = celex.strip()
    norm = norm.upper() # the whole thing is case insensitive, so this is also normalisation
    if norm.startswith('CELEX:'):
        norm = norm[6:].strip()

    ret = { 'norm': norm }
    # TODO: read up on the possible additions, how they combine, because the current parsing is probably incomplete
    match = _re_celex.match( norm )
    # -[0-9]{8}|[A-Z]{3}_[0-9]+

    if match is None:
        raise ValueError("Did not understand %r (%r) as CELEX number"%(celex,norm))

    sector_number, year, document_type, document_number, addition = match.groups()

    # If there's more string to it, see if it makes sense to us.
    nattrans, specdate = '', ''
    #print( document_number, addition )
    if addition not in (None,''):
        if addition[:3] in CELEX_COUNTRIES: # CONSIDER: accept any three-letter combination, to be future-compatible
            nattrans = addition
        elif addition[0] == '-':
            specdate = addition
        else:
            raise ValueError('Did not understand extra value %r on %r'%(addition, norm))

    ret['sector_number']   = sector_number # actually a string, because of C and E
    if sector_number in CELEX_SECTORS:
        ret['sector_name'] = CELEX_SECTORS[sector_number]
    ret['year']            = year
    ret['document_type']   = document_type
    ret['document_type_description']   = _celex_doctype(sector_number, document_type)
    ret['document_number'] = document_number
    ret['nattrans']        = nattrans
    ret['specdate']        = specdate

    ret['id']   = ''.join( (sector_number, year, document_type, document_number) )
    #ret['id_nonattrans']   = ''.join( (sector_number, year, document_type, document_number) )

    return ret
