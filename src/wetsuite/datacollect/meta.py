' some metadata helpers not tied to a specific API or data source '
import re, urllib.parse


def parse_jci(s: str):
    """ 
        jci{version}:{type}:{BWB-nummer}{key-value}*
        e.g. jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3.1

        ...though the below is robust to some non-standard things I've seen in real use.

        generating them is more involved due to changes of what parameters to use between versions

        for type=='c' (single consolidation), expected params include
            g  geldigheidsdatum
            z  zichtdatum

        for type=='v' (collection), expected params include
            s  start of geldigheid
            e  end of geldigheid
            z  zichtdatum
    """
    d = {}
    m = re.match('(?:jci)?([0-9.]+):([a-z]):(BWB[RV][0-9]+)(.*)', s)
    if m is None:
        raise ValueError('%r does not look like a valid jci'%s)
    else:
        version, typ, bwb, rest = m.groups()
        d['version'] = version
        d['type']    = typ
        d['bwb']     = bwb
        # The jci standard doesn't seem to make it clear whether it's supposed to be a conformant URL or URN, so it's unsure whether there is specific parameter encoding.
        #   The below is somewhat manual, but might prove more robust then just   d['params']  = urllib.parse.parse_qs(rest)
        params = {}
        for param in rest.split('&'):
            pd = urllib.parse.parse_qs(param)
            for key in pd:
                if key not in params:
                    params[key] = pd[key]
                else:
                    params[key].extend( pd[key] )
        d['params'] = params

    return d


