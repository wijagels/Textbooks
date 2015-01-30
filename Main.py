__author__ = 'William Jagels'

__base_url__ = 'http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TBWizardView?catalogId=10001&langId=-1&storeId=19073'
__req_url__ = "http://binghamton.bncollege.com/webapp/wcs/stores/servlet/TextBookProcessDropdownsCmd?campusId=17548069&termId=64536529&deptId=&courseId=&sectionId=&storeId=19073&catalogId=10001&langId=-1&dropdown=term"

from pymongo import MongoClient
import urllib3
import json
import http.cookies

headers = {'content-type': 'application/json'}
conn = urllib3.PoolManager()

def main():
    #Have to get cookies so we look legit
    r = conn.urlopen('GET', __base_url__)
    print('HDR:', r.headers)
    print('DATA:', r.data)
    cookie = http.cookies.SimpleCookie(r.headers['set-cookie'])
    print(cookie)
    headers['Cookie']=cookie.output(attrs=[], header='').strip()
    r = conn.urlopen('GET', __req_url__, headers=headers)
    print('DATA:', r.data)

def scrapeDept(dept):


main()