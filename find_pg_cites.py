'''
Try to find Wikipedia pages that correspond to Project Gutenberg books
'''

from wikipedia import wikipedia
import re 
import requests
import time

RATE_LIMIT_LAST_CALL = None
USER_AGENT = 'wikipedia (https://github.com/gitenberg-dev/pg-wikipedia)'
RATE_LIMIT = False
RATE_LIMIT_MIN_WAIT = None
API_URL = 'http://en.wikipedia.org/w/api.php'

def wiki_request(params):
    '''
    Make a request to the Wikipedia API using the given search parameters.
    Returns a parsed dict of the JSON response.
    '''

    params['format'] = 'json'
    if not 'action' in params:
        params['action'] = 'query'

    headers = {
    'User-Agent': USER_AGENT
    }

    if RATE_LIMIT and RATE_LIMIT_LAST_CALL and \
        RATE_LIMIT_LAST_CALL + RATE_LIMIT_MIN_WAIT > datetime.now():

    # it hasn't been long enough since the last API call
    # so wait until we're in the clear to make the request

        wait_time = (RATE_LIMIT_LAST_CALL + RATE_LIMIT_MIN_WAIT) - datetime.now()
        time.sleep(int(wait_time.total_seconds()))

    r = requests.get(API_URL, params=params, headers=headers)

    if RATE_LIMIT:
        RATE_LIMIT_LAST_CALL = datetime.now()

    return r.json()

def get_wikidata_id(title):
    qparams = {'site':'en', 'page': title.replace(' ','_')}
    r = requests.get("https://www.wikidata.org/wiki/Special:ItemByTitle",params=qparams)
    if r.url.find('https://www.wikidata.org/wiki/')<0:
        return None
    else:
        answer = r.url[30:]
        if answer.find('Special:ItemByTitle')<0:
            return answer
        else:
            return None

def embeds(template, results=20):
    '''
    Do a Wikipedia search for `template` embeds.
    Keyword arguments:
      * results - the maxmimum number of results returned
    '''

    query_params = {
        'list': 'embeddedin',
        'eilimit': 50,
        'eititle': 'Template:{:}'.format(template),
    }
    last_continue = {}
    n_results = 0
    while True:
        params = query_params.copy()
        params.update(last_continue)
        raw_results = wiki_request(params)
        for raw_result in raw_results['query']['embeddedin']:
            n_results += 1
            yield raw_result
        
        if 'continue' not in raw_results or n_results > results:
            break
        last_continue = raw_results['continue']

# need to figure out what the entities are
dictionary = {}
def dictionary_lookup(wd_id):
    if wd_id in dictionary:
        return dictionary[wd_id]
    r = requests.get(u'https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(wd_id))
    label = get_label(r.json())
    dictionary[wd_id]= label
    return label
    
def get_label(wd_json, lang='en'):
    alii = wd_json['entities'].values()[0]['labels'][lang]
    return alii['value']
        
def lookup_item(wd_id):
    r = requests.get(u'https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(wd_id))
    try:
        claims = r.json()['entities'].values()[0]['claims']
        if isinstance(claims, dict) :
            for prop in claims.keys():
                for item in claims[prop]:
                    value = item['mainsnak']['datavalue']
                    item_value = None
                    item_label = ''
                    if value['type'] == 'string':
                        item_value= value['value']
                    elif value['type'] == 'wikibase-entityid':
                        item_value= u'Q{}'.format(value['value']['numeric-id'])
                        item_label = dictionary_lookup(item_value)
                    print u'{}\t{}\t{}\t{}'.format(prop, dictionary_lookup(prop), item_value, item_label)
                    #return (prop, dictionary_lookup(prop), item_value, item_label)
    except ValueError:
        return ("error",'','','')
def print_type(wd_id):
    r = requests.get(u'https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(wd_id))
    try:
        claims = r.json()['entities'].values()[0]['claims']
        for super_type in claims.get('P31',[]):
            value = super_type['mainsnak']['datavalue']
            item_value= u'Q{}'.format(value['value']['numeric-id'])
            item_label = dictionary_lookup(item_value)
            print u'{}\t{}'.format( item_value, item_label)
    except ValueError:
        print "error"    
def is_book(wd_id):
    r = requests.get(u'https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(wd_id))
    try:
        claims = r.json()['entities'].values()[0]['claims']
        if isinstance(claims, dict) :
            for super_type in claims.get('P31',[]):
                super_type_value = super_type['mainsnak']['datavalue']['value']['numeric-id']
                if super_type_value in (571,191067,35760,7725634):
                    return True
                else:
                    item_value= u'Q{}'.format(super_type_value)
                    item_label = dictionary_lookup(item_value)
        else:
            print u'non-dict claims in {}'.format(wd_id)
    except ValueError:
        return False    

pgmatch=re.compile(r"gutenberg.org/(etext|ebooks|files)/(\d+)")
# this file will contain candidate pages. some of these will not be exactly what we want.
fname='./metadata/pg-wikipedia-candidates.txt'
with open(fname,'w') as f:
    for result in embeds('Gutenberg', results=10000):
        wd_id = get_wikidata_id(result['title'])
        if is_book(wd_id):
            pg_ids=[]
            page = wikipedia.page(pageid=result['pageid'])
            for match in pgmatch.findall(page.html()):
                if match[1] not in pg_ids:
                    pg_ids.append( match[1])
                    line = u'{}\t{}\t{}'.format(result['title'],wd_id, int(match[1]))
                    print line
                    f.write(line.encode('UTF-8'))
                    f.write('\r')

