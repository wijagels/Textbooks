__author__ = 'William Jagels'


__store_id__ = '19073'
__base_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TBWizardView?catalogId=10001&langId=-1&storeId=19073'
__req_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TextBookProcessDropdownsCmd?campusId=17548069&termId=64536529&storeId=19073&catalogId=10001&langId=-1&dropdown=term'
__dept_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TextBookProcessDropdownsCmd?campusId=17548069&termId=64536529&storeId=19073&catalogId=10001&langId=-1&dropdown=dept'
__class_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TextBookProcessDropdownsCmd?campusId=17548069&termId=64536529&storeId=19073&catalogId=10001&langId=-1&dropdown=course'
__book_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/BNCBTBListView'
__book_data__ = {
    "storeId": "19073",
    "catalogId": "10001",
    "langId": "-1",
    "clearAll": "",
    "viewName": "TBWizardView",
    "removeSectionId": "",
    "mcEnabled": "N",
    "showCampus": "false",
    "selectTerm": "Select Term",
    "selectDepartment": "Select Department",
    "selectSection": "Select Section",
    "selectCourse": "Select Course",
    "campus1": "17548069",
    "firstTermName_17548069": "SPRING 2015",
    "firstTermId_17548069": "64536529",
    "section_1": "",
    "section_2": "",
    "section_3": "",
    "section_4": "",
    "numberOfCourseAlready": "4"
}


import urllib3
import json
import http.cookies
import re
import requests
from bs4 import BeautifulSoup, Tag
from pymongo import MongoClient


headers = {'content-type': 'application/json'}
conn = urllib3.PoolManager()  # TODO: migrate to requests



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
    try:
        r = conn.urlopen('GET', __base_url__, timeout=3)  # TODO: migrate to requests
        cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
        headers['Cookie'] = cookie.output(attrs=[], header='').strip()
    except:
        print("Renew cookie failed")
        renew_cookie()
        pass


def scrape_dept(dept):
    renew_cookie()  # Do this periodically so we don't get rate limited
    url = __dept_url__ + '&deptId=' + dept['categoryId']
    r = conn.urlopen('GET', url, headers=headers, timeout=3)  # TODO: migrate to requests
    print("New dept!", dept['categoryName'])
    try:
        data = json.loads(r.data.decode("utf-8"))
        for cl in data:
            scrape_class(cl, dept)
    except:
        print(headers)
        print(r.data)
        print("Damnit, something broke again")
        renew_cookie()
        scrape_dept(dept)
        pass


def scrape_class(cl, dept):
    url = __class_url__ + '&courseId=' + cl['categoryId']
    r = conn.urlopen('GET', url, headers=headers, timeout=3)  # TODO: migrate to requests
    try:
        data = json.loads(r.data.decode("utf-8"))
        for section in data:
            scrape_section(section, cl, dept)
    except:
        print(r.data)
        print("Shit, something bad happened")
        renew_cookie()
        scrape_class(cl, dept)
        pass


def scrape_section(section, cl, dept):
    url = __book_url__
    url_data = __book_data__
    url_data.update({'section_1': section['categoryId']})
    tmp_headers = headers.copy()
    tmp_headers['content-type'] = 'application/x-www-form-urlencoded'
    try:
        r = requests.post(url, data=url_data, headers=tmp_headers, timeout=3)
        extract_prices(r.text, section, cl, dept)
    except:
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
            if type_price == 'RENT USED':
                ru = price.find("span", class_='bookPrice')['title']
            elif type_price == 'RENT NEW':
                rn = price.find("span", class_='bookPrice')['title']
            elif type_price == 'BUY USED ':  # The idiots who designed the site put trailing spaces in these...
                bu = price.find("span", class_='bookPrice')['title']
            elif type_price == 'BUY NEW ':
                bn = price.find("span", class_='bookPrice')['title']
        if book_list.__len__() > 0:
            book = {
                'Department': dept['categoryName'],
                'Class': cl['categoryName'],
                'Section': section['categoryName'],
                'isRequired': ir,
                'Price': {
                    'RentUsed': ru.strip('$'),
                    'RentNew': rn.strip('$'),
                    'BuyUsed': bu.strip('$'),
                    'BuyNew': bn.strip('$')
                }
            }
            add_book(book)


def grep(s, pattern):
    return '\n'.join(re.findall(r'^.*%s.*?$'%pattern,s,flags=re.M))


def add_book(book):
    print(db.test.find(book).count())
    if db.test.find(book).count() == 0:
        print("Inserting " + json.dumps(book))
        db.test.insert(book)
    else:
        print("Skipping " + json.dumps(book))


client = MongoClient()
db = client.test
print(db)
main()