__author__ = 'William Jagels'

__base_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TBWizardView?catalogId=10001&langId=-1&storeId=19073'
__req_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TextBookProcessDropdownsCmd?campusId=17548069&termId=64536529&deptId=&courseId=&sectionId=&storeId=19073&catalogId=10001&langId=-1&dropdown=term'
__dept_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TextBookProcessDropdownsCmd?campusId=17548069&termId=64536529&courseId=&sectionId=&storeId=19073&catalogId=10001&langId=-1&dropdown=dept'
__class_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TextBookProcessDropdownsCmd?campusId=17548069&termId=64536529&deptId=64536807&sectionId=&storeId=19073&catalogId=10001&langId=-1&dropdown=course'
__book_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/BNCBTBListView'
__book_data__ = 'storeId=19073&catalogId=10001&langId=-1&viewName=TBWizardView&mcEnabled=N&showCampus=false&campus1=17548069&firstTermName_17548069=SPRING+2015&firstTermId_17548069=64536529'

__book_data2__ = {
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


from pymongo import MongoClient
import urllib3
import json
import http.cookies
import re
import pprint
import requests
from time import sleep


headers = {'content-type': 'application/json'}
conn = urllib3.PoolManager()


def main():
    # Have to get cookies so we look legit
    r = conn.urlopen('GET', __base_url__)
    print('HDR:', r.headers)
    print('DATA:', r.data)
    cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
    headers['Cookie'] = cookie.output(attrs=[], header='').strip()
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.35 Safari/537.36'
    r = conn.urlopen('GET', __req_url__, headers=headers)
    print('DATA:', r.data)
    for dept in json.loads(r.data.decode("utf-8")):
        scrape_dept(dept)


def renewCookie():
    r = conn.urlopen('GET', __base_url__)
    cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
    headers['Cookie'] = cookie.output(attrs=[], header='').strip()


def scrape_dept(dept):
    renewCookie() # Do this periodically so we don't get rate limited
    url = __dept_url__ + '&deptId=' + dept['categoryId']
    r = conn.urlopen('GET', url, headers=headers)
    print("New dept!", dept['categoryName'])
    try:
        data = json.loads(r.data.decode("utf-8"))
        for cl in data:
            scrape_class(cl)
    except:
        print(headers)
        print(r.data)
        print("Damnit, something broke again")
        renewCookie()
        scrape_dept(dept)
        pass


def scrape_class(cl):
    url = __class_url__ + '&courseId=' + cl['categoryId']
    r = conn.urlopen('GET', url, headers=headers)
    try:
        data = json.loads(r.data.decode("utf-8"))
        for section in data:
            scrape_section(section)
    except:
        print(r.data)
        print("Shit, something bad happened")
        renewCookie()
        scrape_class(cl)
        pass


def scrape_section(section):
    url = __book_url__
    urldata = __book_data2__
    urldata.update({'section_1': section['categoryId']})
    myheaders = headers.copy()
    myheaders['content-type'] = 'application/x-www-form-urlencoded'
    #urldata = urllib3.encode_multipart_formdata(urldata)
    #r = conn.request('POST', url, body=urldata, headers=headers)
    try:
        r = requests.post(url, data=urldata, headers=myheaders, timeout=10)
        #print(r.text)
        # print(grep(r.data.decode("utf-8"), "bookPrice"))
        #print(grep(r.text, "bookPrice"))
    except:
        print("Oh noes!")
        renewCookie()
        scrape_section(section)
        pass


def extractPrices():
    return # TODO: make this dump stuff into mongodb

def grep(s,pattern):
    return '\n'.join(re.findall(r'^.*%s.*?$'%pattern,s,flags=re.M))


main()