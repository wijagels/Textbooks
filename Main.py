__author__ = 'William Jagels'


__store_id__ = '19073'
__campus_id__ = '17548069'
__term_id__ = '64536529'
__servlet__ = 'http://american.bncollege.com/webapp/wcs/stores/servlet/'
__base_url__ = __servlet__ + 'TBWizardView?catalogId=10001&langId=-1&storeId=' + __store_id__
__api_base__ = __servlet__ + 'TextBookProcessDropdownsCmd?campusId=' + __campus_id__ + '&termId=' + __term_id__ + \
    '&catalogId=10001&langId=-1&storeId=' + __store_id__
__req_url__ = __api_base__ + '&dropdown=term'
__dept_url__ = __api_base__ + '&dropdown=dept'
__class_url__ = __api_base__ + '&dropdown=course'
__book_url__ = __servlet__ + 'BNCBTBListView'
__book_data__ = {
    "storeId": __store_id__,
    "catalogId": "10001",
    "viewName": "TBWizardView",
    "campus1": __campus_id__,
    "firstTermId_" + __campus_id__: __term_id__
}


import urllib3
import json
import http.cookies
import re
import requests
import traceback
import time
from bs4 import BeautifulSoup, Tag
from pymongo import MongoClient


headers = {'content-type': 'application/json'}
conn = urllib3.PoolManager()  # TODO: migrate to requests
failures = 0



def main():
    # Have to get cookies so we look legit
    r = conn.urlopen('GET', __base_url__)  # TODO: migrate to requests
    cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
    headers['Cookie'] = cookie.output(attrs=[], header='').strip()
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.35 Safari/537.36'
    r = conn.urlopen('GET', __req_url__, headers=headers, timeout=3)  # TODO: migrate to requests
    for dept in json.loads(r.data.decode("utf-8")):
        scrape_dept(dept)


def renew_cookie():
    global failures
    try:
        r = conn.urlopen('GET', __base_url__, timeout=3)  # TODO: migrate to requests
        cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
        headers['Cookie'] = cookie.output(attrs=[], header='').strip()
        failures = 0
    except:
        failures += 1
        time.sleep(10 * failures)
        print("Renew cookie failed")
        renew_cookie()
        pass


def scrape_dept(dept):
    renew_cookie()  # Do this periodically so we don't get rate limited
    url = __dept_url__ + '&deptId=' + dept['categoryId']
    try:
        r = conn.urlopen('GET', url, headers=headers, timeout=3)  # TODO: migrate to requests
        print("New dept!", dept['categoryName'])
        data = json.loads(r.data.decode("utf-8"))
        for cl in data:
            scrape_class(cl, dept)
    except:
        print("Damnit, something broke again")
        # traceback.print_exc()
        renew_cookie()
        scrape_dept(dept)
        pass


def scrape_class(cl, dept):
    try:
        url = __class_url__ + '&courseId=' + cl['categoryId']
        r = conn.urlopen('GET', url, headers=headers, timeout=3)  # TODO: migrate to requests
        data = json.loads(r.data.decode("utf-8"))
        for section in data:
            scrape_section(section, cl, dept)
    except:
        # traceback.print_exc()
        print("Shit, something bad happened")
        renew_cookie()
        scrape_class(cl, dept)
        pass


def scrape_section(section, cl, dept):
    try:
        url = __book_url__
        url_data = __book_data__
        url_data.update({'section_1': section['categoryId']})
        tmp_headers = headers.copy()
        tmp_headers['content-type'] = 'application/x-www-form-urlencoded'
        r = requests.post(url, data=url_data, headers=tmp_headers, timeout=3)
        extract_prices(r.text, section, cl, dept)
    except:
        # traceback.print_exc()
        print("Oh noes!")
        renew_cookie()
        scrape_section(section, cl, dept)
        pass


def extract_prices(html, section, cl, dept):
    soup = BeautifulSoup(html)
    ru = rn = bu = bn = ''
    book_list = soup.find_all("div", class_='book_details')
    for el in book_list:
        assert isinstance(el, Tag)
        li = el.find_all("li", class_='selectableBook')
        required = el.find('input', type='hidden')
        ir = False
        if required['value'] == '1':
            ir = True
        for price in li:
            assert isinstance(price, Tag)
            type_price = price['title']
            try:
                if type_price == 'RENT USED':
                    ru = price.find("span", class_='bookPrice')['title']
                elif type_price == 'RENT NEW':
                    rn = price.find("span", class_='bookPrice')['title']
                elif type_price == 'BUY USED ':  # The idiots who designed the site put trailing spaces in these...
                    bu = price.find("span", class_='bookPrice')['title']
                elif type_price == 'BUY NEW ':
                    bn = price.find("span", class_='bookPrice')['title']
            except KeyError:
                pass
            title = price.find('a', class_="clr121")['title']
        if book_list.__len__() > 0:
            book = {
                'Title': title,
                'Department': dept['categoryName'],
                'Class': cl['categoryName'],
                'Section': section['categoryName'],
                'isRequired': ir,
                'RentUsed': tof(ru),
                'RentNew': tof(rn),
                'BuyUsed': tof(bu),
                'BuyNew': tof(bn)
            }
            add_book(book)


def tof(num):
    if num is '':
        return ''
    return float(num.strip('$'))


def grep(s, pattern):
    return '\n'.join(re.findall(r'^.*%s.*?$'%pattern,s,flags=re.M))


def add_book(book):
    if db.test.find(book).count() == 0:
        print("Inserting " + json.dumps(book))
        db.test.insert(book)
    else:
        print("Skipping " + json.dumps(book))


client = MongoClient()
db = client.test
print(db)
main()