# pg-wikipedia
Scripts for linking Wikipedia with Project Gutenberg texts

Contents:
* `pg-wd.csv` a table linking project Gutenberg IDs with Wikidata Concepts
*  `pg_wikipedia.py` python utils to get Wikipedia summaries for a pg identifier
*  `find_pg_cites.py` python script to find wikipedia pages (and thus wikidata ids) that correspond to gutenberg texts. results in 1-2% false positives; compare the wiki title with the pg title to figure out which these are.
