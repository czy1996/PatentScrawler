import requests
import json
import pandas as pd
from utils import log
from pyquery import PyQuery as pq
import os
import multiprocessing
import hashlib
import lxml
import jieba.analyse

cookies = {
    'IS_LOGIN': 'true',
    'WEE_SID': 'NrtsyAN6KC9HdODUfTzgFxHoxk5jlOjXoeGCAsclglNiGYroWvJy!-1866545472!-18978141',
    'avoid_declare': 'declare_pass',
    'JSESSIONID': 'NrtsyAN6KC9HdODUfTzgFxHoxk5jlOjXoeGCAsclglNiGYroWvJy!-1866545472!-18978141',
}
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
}
search_url = 'http://www.pss-system.gov.cn/sipopublicsearch/patentsearch/showSearchResult-startWa.shtml'
detail_url = 'http://www.pss-system.gov.cn/sipopublicsearch/search/search/showViewList.shtml'
info_url = 'http://www.pss-system.gov.cn/sipopublicsearch/patentsearch/viewAbstractInfo-viewAbstractInfo.shtml'


def post_data_from_name(name):
    post_data = {
        'resultPagination.limit': '12',
        'resultPagination.sumLimit': '10',
        'resultPagination.start': '0',
        'searchCondition.searchType': 'Sino_foreign',
        'searchCondition.searchExp': name,
        'wee.bizlog.modulelevel': '0200802',
        'searchCondition.executableSearchExp': "VDB:(NBI='{}')".format(name),
    }
    return post_data


def test_post():
    url = search_url
    post_data = post_data_from_name('CN206027392U')
    r = requests.post(url, headers=headers, cookies=cookies, data=post_data)
    log(r.text)


def cached_html(name):
    # log('**debug', name, str(hash(name)))
    cached_path = os.path.join('cached_html', search_url.split('/')[-1] + hashlib.md5(name.encode()).hexdigest())
    if os.path.exists(cached_path):
        try:
            with open(cached_path, 'r', encoding='utf-8') as f:
                log('restored from cache')
                return f.read()
        except UnicodeDecodeError:
            with open(cached_path, 'r', encoding='gbk') as f:
                log('restored from cache')
                return f.read()
    else:
        post_data = post_data_from_name(name)
        r = requests.post(search_url, headers=headers, cookies=cookies, data=post_data)
        # log('**debug', r.text)
        with open(cached_path, 'w', encoding='utf-8') as f:
            f.write(r.text)
        return r.text


def html_from_name(name):
    return cached_html(name)


def patent_keywords_from_xls(xls):
    """
    
    :param xls: file name 
    :return: list
    """
    df = pd.read_excel(xls)
    # log(df)
    keyword_list = list(df['公开号'])
    log('keywords', keyword_list)
    # new_list = []
    # for name in name_list:
    #     new_list.append(name.replace('/', '-'))
    return keyword_list


def id_from_html(html):
    if html == '':
        raise UnboundLocalError
    try:
        p = pq(html)
        vid = p('input').filter(lambda i, this: pq(this).attr('name') == 'vIdHidden')[0].value
        uid = p('input').filter(lambda i, this: pq(this).attr('name') == 'idHidden')[0].value
    except IndexError:
        log('**debug', html)
    return vid, uid


def cached_json(vid, uid):
    cached_path = os.path.join('cached_json', '{}.json'.format(uid))
    if os.path.exists(cached_path):
        with open(cached_path, 'r') as f:
            d = json.load(f)
            log('retrieved from cached', d)
    else:
        url = info_url
        post_data = {
            'nrdAn': vid,
            'cid': uid,
            'sid': uid,
            'wee.bizlog.modulelevel': '0201101',
        }

        log('retrieving, ({}) ({})'.format(vid, uid), )
        r = requests.post(url, headers=headers, cookies=cookies, data=post_data)
        d = r.json()
        with open(cached_path, 'w') as f:
            json.dump(d, f)
        log('retrieved', d)
    return d


def json_from_uid(vid, uid):
    d = cached_json(vid, uid)
    result = {
        '编号': '',
        '资源类型': '',
        '资源分类': '',
        '名称': d['abstractInfoDTO']['tioIndex']['value'],
        '编号名称': d['abstractInfoDTO']['abstractItemList'][2]['value'] + d['abstractInfoDTO']['tioIndex']['value'],
        '数据格式': 'PDF',
        # '关键字': '',
        # '摘要': pq(d['abstractInfoDTO']['abIndexList'][0]['value']).find('p').text(),
        '申请号': d['abstractInfoDTO']['abstractItemList'][0]['value'],
        '申请日': d['abstractInfoDTO']['abstractItemList'][1]['value'],
        '公开（公告）号': d['abstractInfoDTO']['abstractItemList'][2]['value'],
        '公开（公告）日': d['abstractInfoDTO']['abstractItemList'][3]['value'],
        'IPC分类号': d['abstractInfoDTO']['abstractItemList'][4]['value'],
        '申请（专利权）人': d['abstractInfoDTO']['abstractItemList'][5]['value'],
        '发明人': d['abstractInfoDTO']['abstractItemList'][6]['value'],
        '优先权号': d['abstractInfoDTO']['abstractItemList'][7]['value'],
        '优先权日': d['abstractInfoDTO']['abstractItemList'][8]['value'],
        '申请人地址': d['abstractInfoDTO']['abstractItemList'][9]['value'],
        # '申请人邮编': d['abstractInfoDTO']['abstractItemList'][10]['value'],
        # 'CPC分类号': d['abstractInfoDTO']['abstractItemList'][11]['value'],
    }
    try:
        cpc = d['abstractInfoDTO']['abstractItemList'][11]['value']
    except IndexError:
        cpc = ''
    try:
        post = d['abstractInfoDTO']['abstractItemList'][10]['value']
    except IndexError:
        post = ''
    ab = pq(d['abstractInfoDTO']['abIndexList'][0]['value'])
    for i in range(4):
        ab = ab.children()
    # print(ab.text())
    result['摘要'] = ab.text()
    result['CPC分类号'] = cpc
    result['申请人邮编'] = post
    result['关键词'] = ';'.join(jieba.analyse.extract_tags(result['名称'], topK=4))
    # log(result['关键词'])
    return result


class Item(object):
    def __init__(self):
        self.request_id = ''
        self.request_date = ''
        self.release_id = ''
        self.release_date = ''
        self.ipc = ''
        self.requester = ''
        self.inventor = ''
        self.first_right_id = ''
        self.first_right_date = ''
        self.address = ''
        self.post_number = ''
        self.cpc = ''

    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s

    def json(self):
        d = {
            '申请号': self.release_id,
            '申请日': self.request_date,
            '公开（公告）号': self.release_id,
            '公开（公告）日': self.release_date,
            'IPC分类号': self.ipc,
            '申请（专利权）人': self.requester,
            '发明人': self.inventor,
            '优先权号': self.first_right_id,
            '优先权日': self.first_right_date,
            '申请人地址': self.address,
            '申请人邮编': self.post_number,
            'CPC分类号': self.cpc,
        }
        return d


def download_filename(path, filename):
    log(path,filename)
    full_path = os.path.join(path, filename)
    log(full_path)
    names = patent_keywords_from_xls(full_path)
    l = []
    # log('shit ({})'.format(names))
    for i, name in enumerate(names):
        log('处理第({})个'.format(i))
        html = html_from_name(name)
        try:
            vid, uid = id_from_html(html)
        except UnboundLocalError:
            continue
        try:
            l.append(json_from_uid(vid, uid))
        except lxml.etree.XMLSyntaxError as e:
            log('** error', e)
            continue
    save_to_excel(l, filename)
    log('download {} end'.format(filename))


def save_to_excel(l, filename):
    df = pd.DataFrame(l)
    df = df.reindex_axis(['名称', '编号名称', '数据格式', '关键词', '摘要', '申请号',
                          '申请日', '公开（公告）号', '公开（公告）日', 'IPC分类号', '申请（专利权）人', '发明人',
                          '优先权号', '优先权日', '申请人地址', '申请人邮编', 'CPC分类号'], axis=1)
    df = df.drop_duplicates('名称')
    df.to_excel('results/{}'.format(filename), index=False)


def main():
    path = 'origin'
    filenames = os.listdir(path)
    for i, filename in enumerate(filenames):
        log('启动进程{} {}'.format(i, filename))
        p = multiprocessing.Process(target=download_filename, args=(path, filename))
        p.start()


if __name__ == '__main__':
    # log(patent_keywords_from_xls('1.xls'))
    # log(html_from_name('混合切削结构石油天然气钻井钻头'))
    # log(test_post())
    # html = html_from_name('混合切削结构石油天然气钻井钻头')
    # vid, uid = id_from_html(html)
    # log(json_from_uid(vid, uid))
    # main()
    test_post()