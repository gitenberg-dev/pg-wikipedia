from wikipedia import wikipedia
import csv
import requests

_table={}
def get_item_summary(wd_id, lang='en'):
    r = requests.get(u'https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(wd_id))
    try:
        title = r.json()['entities'][wd_id]['sitelinks']['{}wiki'.format(lang)]['title']
        return wikipedia.summary(title)
    except ValueError:
        #not JSON
        return ""

def get_wd_id(pg_id):
    pg_id = str(pg_id)
    return _table.get(pg_id, None)

def get_pg_summary(pg_id):
    return get_item_summary(get_wd_id(pg_id))

pg_wd_file =  requests.get('https://raw.githubusercontent.com/gitenberg-dev/pg-wikipedia/master/pg-wd.csv')
csvreader= csv.reader(pg_wd_file.iter_lines(),delimiter=',', quotechar='"')
for (pg_id,wd_id) in csvreader:
    _table[pg_id]=wd_id
