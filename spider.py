#!venv/bin/python3
import requests
import re
from bs4 import BeautifulSoup as soup

import pprint

pp = pprint.PrettyPrinter(indent=4)

URL='https://classic.wowhead.com/item={}'


TOOLTIP_TABLE_MAP = [
    {
        'td': 'slot',
        'th': 'type',
    },
    {
        'td': 'dmg',
        'th': 'speed',
    }
]

QUALITY_MAP = {
    'q0': 'junk',
    'q1': 'common',
    'q2': 'uncommon',
    'q3': 'rare',
    'q4': 'epic',
    'q5': 'legendary',
}

def getText(spoonfull):
    return spoonfull.text if spoonfull else ''

def getGroup(regex_match, group=0):
    return regex_match.group(group) if regex_match else ''

def getItem(item_number):
    print('getting...', URL.format(item_number))
    resp = requests.get(URL.format(item_number))

    #print(resp.status_code)

    #print(resp.text)
    

    slurp = soup(resp.text, 'html5lib')
    if slurp.find('div', class_='database-detail-page-not-found-message'):
        return (False, None, None)

    # Item Info
    tooltip_data = re.search(r'(?<=tooltip_enus = ).*(?:";)', resp.text).group(0)[1:-1]
    tooltip_data = tooltip_data.replace('\\"', '"')
    tooltip_data = tooltip_data.replace('\/', '/')
    #tooltip_data = tooltip_data.replace('<br>', '|')
    #print(tooltip_data)

    slurp = soup(tooltip_data, 'html5lib')

    item_info = {}
    name_element = slurp.find('b')

    item_info['id'] = item_number
    item_info['name'] = getText(name_element)
    item_info['boe'] = getGroup(re.search(r'(?<=<!--bo-->)[^<]*', tooltip_data))
    item_info['quality'] = QUALITY_MAP[name_element['class'][0]]
    item_info['ilvl'] = slurp.find('span', class_='q').text
    item_info['dps'] = getGroup(re.search(r'(?<=<!--dps-->)[^<]*', tooltip_data))[1:-1]
    item_info['ebstats'] = getGroup(re.search(r'(?<=<!--ebstats-->)[^<]*', tooltip_data))
    item_info['egstats'] = getGroup(re.search(r'(?<=<!--egstats-->)[^<]*', tooltip_data))
    item_info['eistats'] = ', '.join(
        filter(lambda e: e != '', 
            [i.strip() for i in getGroup(re.search(r'(?<=<!--eistats-->)(.*?)(?:<!--)', tooltip_data), 1).split('<br>')]
        )
    )
    item_info['rlvl'] = getGroup(re.search(r'(?<=<!--rlvl-->)[^<]*', tooltip_data))
    item_info['e'] = getGroup(re.search(r'(?<=<!--e-->)[^<]*', tooltip_data))
    item_info['ps'] = getGroup(re.search(r'(?<=<!--ps-->)[^<]*', tooltip_data))

    for index, table in enumerate(slurp.td.find_all('table')):
        #print(index)
        #print(table.text)
        item_info[TOOLTIP_TABLE_MAP[index]['td']] = table.tbody.td.text
        item_info[TOOLTIP_TABLE_MAP[index]['th']] = table.tbody.th.text

    item_info['gold'] = getText(slurp.find('span', class_='moneygold'))
    item_info['silver'] = getText(slurp.find('span', class_='moneysilver'))
    item_info['copper'] = getText(slurp.find('span', class_='moneycopper'))
        
    item_info['unavailable'] = item_info['name'][-5:] == '(old)'
    if item_info['boe'] == 'Quest Item' or item_info['name'][-5:] == '(old)':
        return True, item_info, None

    try:
        item_info['effects'] = list(map(getText, slurp.find_all('table')[3].find_all('span', class_='q2')))
    except Exception as e:
        item_info['effects'] = ''
    try:
        item_info['bonus-damage'] = slurp.find('table').tbody.tr.td.find_all('table')[1].find_all('td')[-1].text
    except Exception as e:
        item_info['bonus-damage'] = ''

    # = slurp.find('span', class_='q').text



    quickfacts_data = getGroup(re.search(r'(?<=printHtml\(")[^"]*', resp.text))
    #print(quickfacts_data)
    item_info['faction'] = getGroup(re.search(r'Alliance|Horde', quickfacts_data))
    item_info['enchanting'] = getGroup(re.search(r'[^\]]*enchanted', quickfacts_data))
    item_info['phase'] = getGroup(re.search(r'[^\]]*phase[^[]*', quickfacts_data))

    '''
    quit()



    slurp = soup(resp.text, 'html5lib')
    #print(slurp.prettify('latin-1'))

    # Get Item Information
    info_source_1 = slurp.find('div', id='tt{}'.format(item_number)) # Source 1
    print(info_source_1.prettify('latin-1'))
    print([i for i in info_source_1.contents])



    info_source_2 = slurp.find('table', class_='infobox-inner-table')
    
    '''
    return (True, item_info, None)

def spider(start = 1, max_ = -1, retries = 5, wait = -1):
    current_index = start
    false_count = 0
    while false_count < retries and (current_index <= max_ or max_ == -1):
        status, item_info, related_info = getItem(current_index)
        if not status:
            false_count, current_index = false_count + 1, current_index + 1
            print('fail to find')
            continue
        print('successful find')
        false_count, current_index = 0, current_index + 1

        pp.pprint(item_info)

if __name__ == '__main__': 
    import argparse
    parser = argparse.ArgumentParser(description='Spider from CLI')
    parser.add_argument('-n', '-s', '--start', type=int, help='The starting item for the scraper.', default=1)
    parser.add_argument('-d', '--distance', type=int, help='The item distance from [start] that we will attempt.', default=0)
    parser.add_argument('-e', '--max-error', type=int, help='The maximum error streak.', default=5)
    args = parser.parse_args()

    spider(args.start, args.start + args.distance, args.max_error)




