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
from bs4 import BeautifulSoup
from pymongo import MongoClient


headers = {'content-type': 'application/json'}
conn = urllib3.PoolManager()  # TODO: migrate to requests
#client = MongoClient()
#db = client.test


def main():
    # Have to get cookies so we look legit
    r = conn.urlopen('GET', __base_url__)  # TODO: migrate to requests
    print('HDR:', r.headers)
    print('DATA:', r.data)
    cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
    headers['Cookie'] = cookie.output(attrs=[], header='').strip()
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.35 Safari/537.36'
    r = conn.urlopen('GET', __req_url__, headers=headers)  # TODO: migrate to requests
    print('DATA:', r.data)
    for dept in json.loads(r.data.decode("utf-8")):
        scrape_dept(dept)


def renew_cookie():
    r = conn.urlopen('GET', __base_url__)  # TODO: migrate to requests
    cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
    headers['Cookie'] = cookie.output(attrs=[], header='').strip()


def scrape_dept(dept):
    renew_cookie() # Do this periodically so we don't get rate limited
    url = __dept_url__ + '&deptId=' + dept['categoryId']
    r = conn.urlopen('GET', url, headers=headers)  # TODO: migrate to requests
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
    r = conn.urlopen('GET', url, headers=headers)  # TODO: migrate to requests
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
    urldata = __book_data__
    urldata.update({'section_1': section['categoryId']})
    tmp_headers = headers.copy()
    tmp_headers['content-type'] = 'application/x-www-form-urlencoded'
    try:
        r = requests.post(url, data=urldata, headers=tmp_headers, timeout=10)
        extract_prices(r.text, section, cl, dept)
    except:
        print("Oh noes!")
        renew_cookie()
        scrape_section(section, cl, dept)
        pass


def extract_prices(html, section, cl, dept):
    # print(grep(html, "bookPrice"))
    # print(re.finditer("span class=\"bookPrice\" title=\"(.*?)\"", html)[0])
    soup = BeautifulSoup(html)
    for el in soup.find_all("div", class_='book_details'):
        li = el.find_all("li", class_='selectableBook')
        # print(li)
        for price in li:
            if li.string == "BUY USED":
                print("hey sup")
            price = li[0].find("span", class_='bookPrice')[0]['title']
    book = {
        'Department': dept['categoryName'],
        'Class': cl['categoryName'],
        'Section': section['categoryName'],
        'Price': {
            'RentUsed': price,
            'RentNew': '',
            'BuyUsed': '',
            'BuyNew': ''
        }
    }
    print(json.dumps(book))


def grep(s, pattern):
    return '\n'.join(re.findall(r'^.*%s.*?$'%pattern,s,flags=re.M))


main()