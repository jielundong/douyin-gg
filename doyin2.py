#!/usr/bin/python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from urlparse import urlparse, parse_qs
import urllib
import urllib2
import json
import re
import os

headers = {
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'upgrade-insecure-requests': '1',
    'user-agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
}

HEADERS = {'user-agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"}

mapCode2Name = {"0xe602":"num_","0xe605":"num_3","0xe606":"num_4","0xe603":"num_1","0xe604":"num_2","0xe618":"num_","0xe619":"num_4","0xe60a":"num_8","0xe60b":"num_9","0xe60e":"num_","0xe60f":"num_5","0xe60c":"num_4", \
    "0xe60d":"num_1","0xe612":"num_6","0xe613":"num_8","0xe610":"num_3","0xe611":"num_2","0xe616":"num_1","0xe617":"num_3","0xe614":"num_9","0xe615":"num_7","0xe609":"num_7","0xe607":"num_5","0xe608":"num_6","0xe61b":"num_5",\
        "0xe61c":"num_8","0xe61a":"num_2","0xe61f":"num_6","0xe61d":"num_9","0xe61e":"num_7"}
mapCode2Font = {"num_9":8,"num_5":5,"num_6":6,"num_":1,"num_7":9,"num_8":7,"num_1":0,"num_2":3,"num_3":2,"num_4":4}

def getUserInfo(shared_url, **headers):
    html_doc = getHtml(shared_url, **headers)
    result = {}
    if html_doc:
        html_doc = html_doc.replace('&#','hzsd')
        soup = BeautifulSoup(html_doc, 'html.parser')
        header_url = soup.select("[class~=avatar]")[0]['src']
        nickname = soup.select("[class~=nickname]")[0].string
        uid = soup.select("[class~=shortid]")[0].get_text()
        uid = uid.split(" ")
        id = woff2tff(uid)
        sign = soup.select("[class~=signature]")[0].string
        dataInfo = soup.select("[class~=follow-info]")[0]
        dataInfo = splitByChinese(dataInfo.get_text())
        dataInfo = [ d for d in dataInfo if len(d) > 0 ]
        focus = dataInfo[0].split(' ')
        focus = woff2tff(focus)
        fans = dataInfo[1].split(' ')
        fans = woff2tff(fans)
        liked = dataInfo[2].split(' ')
        liked = woff2tff(liked)
        works = soup.select("[class='user-tab active tab get-list']")[0].get_text()
        works = woff2tff(works.split(' '))
        result['avatar'] = header_url
        result['nickname'] = nickname
        result['id'] = id
        result['sign'] = sign
        result['focus'] = focus
        result['fans'] = fans
        result['liked'] = liked
        result['works'] = works
    return result

def getUserVideos(url):
    number = re.findall(r'share/user/(\d+)', url)
    if not len(number):
        return
    dytk = get_dytk(url)
    hostname = urlparse(url).hostname
    if hostname != 't.tiktok.com' and not dytk:
        return
    user_id = number[0]
    return getUserMedia(user_id, dytk, url)


def getRealAddress(url):
    if url.find('v.douyin.com') < 0:
        return url
    res = requests.get(url, headers=headers, allow_redirects=False)
    return res.headers['Location'] if res.status_code == 302 else None


def get_dytk(url):
    res = requests.get(url, headers=headers)
    if not res:
        return None
    dytk = re.findall("dytk: '(.*)'", res.content.decode('utf-8'))
    if len(dytk):
        return dytk[0]
    return None

def generateSignature(value):
    p = os.popen('node fuck-byted-acrawler.js %s' % value)
    return p.readlines()[0]

def getUserMedia(user_id, dytk, url):
    videos = []
    parsed = urlparse(url)
    hostname = parsed.hostname
    sec_uid = parse_qs(parsed.query)['sec_uid']

    #signature = generateSignature(str(user_id))
    user_video_url = "https://%s/web/api/v2/aweme/post/" % hostname
    user_video_params = {
        'sec_uid': sec_uid,
        'count': '35',
        'max_cursor': '0',
        'aid': '1128',
        '_signature': '2Vx9mxAZh0o-K4Wdv7NFKNlcfY',
        'dytk': dytk
    }
    if hostname == 't.tiktok.com':
        user_video_params.pop('dytk')
        user_video_params['aid'] = '1180'

    max_cursor, video_count = None, 0
    while True:
        if max_cursor:
            user_video_params['max_cursor'] = str(max_cursor)
        res = requests.get(user_video_url, headers=headers,
                            params=user_video_params)
        contentJson = json.loads(res.content.decode('utf-8'))
        aweme_list = contentJson.get('aweme_list', [])
        for aweme in aweme_list:
            video_count += 1
            aweme['hostname'] = hostname
            video =  {
                'addr': aweme['video']['play_addr']['url_list'][0],
                'desc': aweme['desc'],
                'duration': aweme['video']['duration'],
                'cover': aweme['video']['cover']['url_list'][0],
                'statistics': aweme['statistics']
            }
            videos.append(video)
        if contentJson.get('has_more'):
            max_cursor = contentJson.get('max_cursor')
        else:
            break
   

    if video_count == 0:
        print("There's no video in number %s." % user_id)

    return videos

def getVideo(url):
    try:
        req = urllib2.Request(url,headers=HEADERS)
        resp = urllib2.urlopen(req)
        return resp.read()
    except urllib2.HTTPError:
        return ''

def getVideoName(url):
    parsed = urlparse(url) 
    vid = parse_qs(parsed.query)['video_id']
    return vid

def getHtml(url,**headers):
    try:
    	req = urllib2.Request(url,headers=headers)
    	resp = urllib2.urlopen(req)
    	return str(resp.read()).decode('utf-8')
    except urllib2.HTTPError:
        return ''


def woff2tff(ls):
    res = ''
    for s in ls:
       res = res + formatNum(s)
    return res

def splitByChinese(s):
    p = re.compile(u"[\u4e00-\u9fa5]")
    return p.split(s)

def isChinese(s):
    p = re.compile(u"[\u4e00-\u9fa5]")
    result = p.match(s)
    if result :
        return True
    return False
    

def formatNum(s):
    if isChinese(s):
        return ''
    if len(s)<8 or s.find("hzsdxe6") < 0 :
        return s
    s1 = '0'+s[4:-1] 
    res = mapCode2Font[mapCode2Name[s1]]
    return str(res)


def getUserAll(shared_url):
    if shared_url.find('v.douyin.com') < 0 :
        return {}
    profile = getUserInfo(shared_url, **HEADERS)
    if profile:
        videos = getUserVideos(getRealAddress(shared_url))
        profile['videos'] = videos
        return profile
    return {}

if __name__ == '__main__':
    userInfo = getUserAll("https://v.douyin.com/qKDMXG/")
    print(json.dumps(userInfo))
