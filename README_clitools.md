

A lot of examples and copy-pasteable fragments currently exist in code form in notebooks,
and loads from structured storage.

...but if you prefer to export things to files and work on files and run tools from the command line,
here is a start at exposing some of the useful functionality in single CLI tools.

You might want to add this directory to your PATH, to be able to use them anywhere.



## pdf-count-pages-with-text

Counts ghow many pages in a PDF file have nontrivial amounts of text,
to guess whether it 

```bash
$ pdf-count-pages-with-text test.pdf
  20 pages,   35% with nontrivial text    'test.pdf'
```


## xml-text

Prints out the contents of text nodes, completely unaware of what might be metadata.

```bash
$ ./xml-text test.xml
[output cut for brevity]
Les procès-verbaux contre les contrevenans seront affirmés dans les formes et délais prescrits par les lois.
Ils seront adressés en originaux à nos procureurs impériaux, qui seront tenus de poursuivre d'office les contrevenans devant les tribunaux de police correctionnelle, ainsi qu'il est réglé et usité pour les délits forestiers, et sans préjudice des dommages-intérêts des parties.
Les peines seront d'une amende de cinq cents fr. au plus et de cent francs au moins, double en cas de récidive, et d'une détention qui ne pourra excéder la durée fixée par le Code de police correctionnelle.
Collationné à l'original, par nous président et secrétaires du Corps législatif. Paris, le 21 Avril 1810. Signé le comte de Montesquiou, président; Puymaurin, Debosque, Plasschaert, Grellet, secrétaires.
Mandons et ordonnons que les présentes, revêtues des sceaux de L'États insérées au Bulletin des lois, soient adressées aux Cours, aux Tribunaux et aux autorités administratives, pour qu'ils les inscrivent dans leurs registres, les observent et les fassent observer; et notre Grand-Juge Ministre de la justice est chargé d'en surveiller la publication.
```


## xml-color

Show colored XML in the shell, optionally with namespaces stripped,
to try to figure out structure of unseen XML documents with less staring. 

(and avoiding some external tools/dependencies, e.g. xmllint plus pygmentize)

Slightly custom for this project, in that there are some namespaces baked in,
Focused on pretty printing to the point its output is not actually valid XML anymore


## xml-path-statistics

```bash 
$ ./xml-path-statistics -u wetgeving/wet-besluit/wettekst test.xml
[output cut for brevity]
    72   wettekst/titeldeel/paragraaf/artikel/kop/label
    72   wettekst/titeldeel/paragraaf/artikel/kop
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie/publicatiejaar
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie/publicatienr
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie/ondertekeningsdatum
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie/publicatiejaar
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie/publicatienr
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie/ondertekeningsdatum
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/inwerkingtreding.datum
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata
    72   wettekst/titeldeel/paragraaf/artikel/meta-data
    72   wettekst/titeldeel/paragraaf/artikel
    79   wettekst/titeldeel/paragraaf/artikel/al
   122   wettekst/titeldeel/paragraaf/artikel/meta-data/jcis/jci

```
