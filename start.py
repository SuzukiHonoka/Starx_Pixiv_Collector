#!/usr/bin/python3
import _thread
import configparser
import json
import os
import re
import sqlite3
import sys
import time
import zipfile
import socket

import demjson
import imageio
import requests
from bs4 import BeautifulSoup
from requests_toolbelt.adapters import host_header_ssl

# from selenium import webdriver
sys_platform = sys.platform

# symbol_win='\\'
# symbol_linux='/'
global_symbol = '/'

program_path = os.path.abspath('.') + global_symbol

save_path = os.path.abspath('.') + global_symbol + "Pixiv_Download" + global_symbol
###################
tag = 'Main'
sni_bypass = False
server_ip = ''
dl_server_ip = ''
###################
proxy_enable = False
proxy_host = ''
proxy_port = ''
pixiv_user_name = ''
pixiv_user_pass = ''
pixiv_user_cookies = ''
piviv_user_cookies_is_not_empty = False
login_status = False
direct_mode = False
cust_path_enable = False
print_info = False
bookmarked_filter = 0
###################
download_manga_enable = True
download_gif_enable = True
###################
current_threads = 0
subthreads_limit = 16
'''
For CN users only , PLEASE DON'T USE IT IF YOU ALREADY HAVE PROXY SERVER!
'''
d_dtrp_enable = False
d_dtrp_address = 'pximg.starx.workers.dev'
###################
# init get param
params = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/76.0.3809.132 Safari/537.36',
    'authority': 'www.pixiv.net',
    'content-type': 'application/x-www-form-urlencoded',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6',
    'dnt': '1',
    'referer': 'https://www.pixiv.net/'
}
# init post param
datas = {
    'captcha': '',
    'g_reaptcha_response': '',
    'password': 'user_password',
    'pixiv_id': 'user_name',
    'post_key': '',
    'source': 'accounts',
    'ref': '',
    'return_to': 'https://www.pixiv.net/'
}
#
download_params = {
    'referer': 'https://www.pixiv.net/'
}
#

login_url = 'https://accounts.pixiv.net/login'
post_url = 'https://accounts.pixiv.net/api/login?lang=en'
# 当前日期
year_month = time.strftime("%Y%m", time.localtime())
day = time.strftime("%d", time.localtime())
# param
p_date = '&date='
p_page = '&p='
#
page = 1
max_page = 10
# Finding the available Day
ranking_daily_json = ""


#
###################

###################
# voids
###################

def print_with_tag(tag, data):
    data_print = data
    if type(data) == list:
        data_print = ''
        for per_data in data:
            if len(data_print) == 0:
                data_print += str(per_data)
            else:
                data_print += ' ' + str(per_data)
    print('[' + time.asctime(time.localtime(time.time())) + '] ' + tag + ' =>', data_print)


print_with_tag(tag, 'Welcome to use this Pixiv ranking collector!')
print_with_tag(tag, 'This program is powered by Starx.')
print_with_tag(tag, ['Your are using', sys_platform, 'platform.'])


def input_yn(str):
    return input(str + ' (Y/N):').lower() == 'y'


def config_and_cookies_check():
    tag = 'Config_and_Cookies_Check_Process'
    global proxy_enable, proxy_host, proxy_port, sni_bypass, cust_path_enable, save_path, print_info, bookmarked_filter, pixiv_user_name, pixiv_user_pass, piviv_user_cookies_is_not_empty, pixiv_user_cookies,direct_mode
    if not os.path.exists('config.ini'):
        if input_yn('Do you want to use socks5 proxy?'):
            proxy_enable = True
            proxy_host = input('Please enter the socks5 server host ip address:')
            proxy_port = input('Please enter the socks5 server host port number:')
        else:
            print_with_tag(tag, 'Not using the proxy..')
            proxy_enable = False
            if input_yn('Did you want to use SNI Bypass mode?'):
                sni_bypass = True
        if input_yn('Did you want to use direct mode?'):
            direct_mode = True
        else:
            pixiv_user_name = input("Please enter your own pixiv account name:")
            pixiv_user_pass = input("Please enter your own pixiv account password:")
        if input_yn('Do you want to change default save path?'):
            cust_path_enable = True
            save_path = input("Please enter the full path to save the data:") + global_symbol
        if input_yn('Do you want to display the illust info when downloading?'):
            print_info = True
        if input_yn('Do you want to filter the ranking illust when downloading?'):
            bookmarked_filter = int(input('Please enter the bookmarked value to filter:'))
        if input_yn('Are you sure about that account information correct?'):
            # OPTIONAL
            if input_yn('Do you want to save this configuration as a file?'):
                path = program_path
                config_name = "config.ini"
                abs_path = path + config_name
                if os.path.exists(abs_path):
                    with open(abs_path, 'w'):
                        print_with_tag(tag, 'Creating empty config file')
                config = configparser.RawConfigParser()
                ###########
                config.add_section('Connection')
                config.set('Connection', 'sni_bypass_enable', str(sni_bypass))
                ###########
                config.add_section('Proxy')
                config.set('Proxy', 'Enable', str(proxy_enable))
                config.set('Proxy', 'IP', proxy_host)
                config.set('Proxy', 'PORT', proxy_port)
                config.add_section("Account")
                config.set('Account','Direct_Mode',str(direct_mode))
                config.set('Account', 'User_name', pixiv_user_name)
                config.set('Account', 'User_pass', pixiv_user_pass)
                config.add_section('Data')
                config.set('Data', 'CUST_PATH_ENABLE', str(cust_path_enable))
                config.set('Data', 'SAVE_PATH', save_path)
                config.set('Data', 'PRINT_INFO', str(print_info))
                config.set('Data', 'BOOKMARKED_FILTER', str(bookmarked_filter))
                with open(abs_path, 'w+') as f:
                    config.write(f)
            print_with_tag(tag, 'Done!')
    else:
        config = configparser.ConfigParser()
        config.read('config.ini')
        if config['Connection']['sni_bypass_enable'] == 'True':
            sni_bypass = True
        if config['Proxy']['Enable'] == 'True':
            proxy_enable = True
        proxy_host = config['Proxy']['IP']
        proxy_port = config['Proxy']['PORT']
        direct_mode = config['Account']['Direct_Mode']
        pixiv_user_name = config['Account']['User_name']
        pixiv_user_pass = config['Account']['User_pass']
        if config['Data']['CUST_PATH_ENABLE'] == 'True':
            cust_path_enable = True
            save_path = config['Data']['SAVE_PATH']
        if config['Data']['PRINT_INFO'] == 'True':
            print_info = True
        bookmarked_filter = config['Data']['BOOKMARKED_FILTER']
    if os.path.exists("cookies"):
        with open('cookies', 'r') as f:
            cookies = f.read()
            if len(cookies) > 0:
                piviv_user_cookies_is_not_empty = True
                pixiv_user_cookies = json.loads(cookies)
    else:
        print_with_tag(tag, 'Can not to find the Cookies.')


config_and_cookies_check()


def change_params_and_get_the_session():
    global params, datas, login_url, post_url, s, dl_session
    tag = 'Change_Params_And_Get_The_Session'
    print_with_tag(tag, 'Changing Request params..')
    datas['pixiv_id'] = pixiv_user_name
    datas['password'] = pixiv_user_pass
    print_with_tag(tag, 'Post data params changed.')
    s = requests.Session()
    s.headers = params
    # dl_session = requests.Session()
    print_with_tag(tag, 'Session started.')


change_params_and_get_the_session()


def ip_latency_test(ip, port=443):
    tag = 'IP_Latency_TEST'
    print_with_tag(tag, ['Prepare IP latency test for ip', ip, 'Port', str(port)])
    s_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_test.settimeout(10)
    s_start = time.time()
    try:
        s_test.connect((ip, port))
        s_test.shutdown(socket.SHUT_RD)
    except Exception as e:
        print_with_tag(tag, ['Error:', e])
        return None
    s_stop = time.time()
    s_runtime = '%.2f' % (1000 * (s_stop - s_start))
    print_with_tag(tag, [ip, 'Latency:', s_runtime])
    return float(s_runtime)


def get_dns_data_from_doh_server(name, type):
    '''
    :param name: str ['pixiv.net'...]
    :param type: str ['A','AAAA'...]
    :return:str
    FAQ:https://developers.cloudflare.com/1.1.1.1/dns-over-https/json-format/
    '''
    tag = 'DoH_Request_Format'
    doh_server = 'https://cloudflare-dns.com/dns-query?'
    doh_header = {'accept': 'application/dns-json'}
    final_doh_request_url = doh_server + 'name=' + name + '&type=' + type
    res = json.loads(requests.get(final_doh_request_url, headers=doh_header).text)['Answer']
    d_list = []
    for per_dns_data in res:
        if per_dns_data['type'] == 1:
            a_record = per_dns_data['data']
            d_list.append(a_record)
            print_with_tag(tag, ['Index Of DNS Record:', str(len(d_list))])
            print_with_tag(tag, ['Domain', name, 'A record found.'])
            print_with_tag(tag, ['A record:', a_record])
    # Init test
    ip_latency = {}
    for per_ip in d_list:
        ip_latency[str(ip_latency_test(per_ip))] = per_ip
    print_with_tag(tag, 'Selecting best ip node..')
    all_latency_keys = list(ip_latency.keys())
    all_latency_keys.sort(key=float)
    best_latency = all_latency_keys[0]
    best_node = ip_latency[best_latency]
    print_with_tag(tag, ['Selected:', best_node, 'for lowest latency:', best_latency])
    return best_node


def proxy_and_sni_switch():
    global proxy_enable, s, sni_bypass, server_ip, dl_server_ip, post_url
    tag = 'Proxy_And_Sni_Switch'
    if proxy_enable:
        print_with_tag(tag, 'Going to connect to your socks5 server..')
        try:
            # socks.set_default_proxy(socks.SOCKS5, proxy_host, int(proxy_port))
            # socket.socket = socks.socksocket
            # socket.timeout = 500
            proxies = {
                "http": "socks5://" + proxy_host + ":" + proxy_port,
                'https': "socks5://" + proxy_host + ":" + proxy_port
            }
            s.proxies = proxies
        except Exception as e:
            print_with_tag(tag, 'An error occurred when setting up the socks5 proxy for request.')
            print_with_tag(tag, e)
            exit()
        else:
            print_with_tag(tag, 'Proxy connection seems successfully created!!')
    else:
        print_with_tag(tag, 'Not using the proxy..')
        if sni_bypass:
            tag = 'Experiment Function: SNI Bypass'
            print_with_tag(tag, 'Starting..')
            ##########################################################
            print_with_tag(tag, 'Using DoH server to get the correct DNS record.')
            server_ip = get_dns_data_from_doh_server('www.pixiv.net', 'A')
            print_with_tag(tag, ['Server IP =>', server_ip])
            dl_server_ip = get_dns_data_from_doh_server('i.pximg.net', 'A')
            print_with_tag(tag, ['DL Server IP =>', dl_server_ip])
            post_url = post_url.replace('accounts.pixiv.net', server_ip)
            print_with_tag(tag, 'Setting up SSLadapter..')
            # common
            s.mount('https://', host_header_ssl.HostHeaderSSLAdapter())
            # download
            print_with_tag(tag, 'SNI Bypass done.')


proxy_and_sni_switch()


def get_text_from_url(url, mode=1):
    '''
    :param url:
    :param mode: 1=text 2=status_code
    :return:
    '''
    global params, sni_bypass
    tag = 'Get_Text_From_Url'
    retry = 0
    t_url = url
    temp_header = params
    if sni_bypass:
        host = url.split('//')[1].split('/')[0]
        temp_header['host'] = host
        host_home = 'www.pixiv.net'
        host_account = 'accounts.pixiv.net'
        host_dl = 'i.pximg.net'
        if host == host_home:
            t_url = t_url.replace(host_home, server_ip)
        elif host == host_account:
            t_url = t_url.replace(host_account, server_ip)
        elif host == host_dl:
            t_url = t_url.replace(host_dl, dl_server_ip)
        print_with_tag(tag, ['SNI HOST =>', host])
        print_with_tag(tag, ['SNI URL =>', t_url])
    while True:
        try:
            if retry == 3:
                print_with_tag(tag, 'Max retried reached')
                exit()
            retry += 1
            if mode == 1:
                return s.get(t_url, headers=temp_header, timeout=10).text
            if mode == 2:
                return s.get(t_url, headers=temp_header, timeout=10).status_code
        except Exception as e:
            print_with_tag(tag, ['Error Request URL:', url])
            print_with_tag(tag, ['Retry count:', retry])
            print_with_tag(tag, ['Error INFO:', e])
            print('Temp_Header:',temp_header)
            if retry == 2:
                print('Turning off the verify.. (Warning: This is not safe if your are ok with that you cloud just keep doing what your want.)')
                s.verify = False
            # traceback.print_exc()


def update_user_cookies():
    global s, datas, piviv_user_cookies_is_not_empty, program_path
    tag = 'Update_User_Cookies'
    s.cookies.clear()
    # 获取登录页面
    res = get_text_from_url(login_url)
    pattern = re.compile(r'name="post_key" value="(.*?)">')
    r = pattern.findall(res)

    datas['post_key'] = r[0]
    print_with_tag(tag, ['Post_Key:', datas['post_key']])
    result = s.post(post_url, data=datas, timeout=10)
    result_check = json.loads(result.text)['body']
    print_with_tag(tag, ['Response:', str(result_check)])
    if 'success' in result_check:
        print_with_tag(tag, 'Login success!')
        with open(program_path + 'cookies', 'w+') as f:
            f.write(json.dumps(result.cookies))
    else:
        print_with_tag(tag, "Login Error!")
        if input_yn('Do you want to try to login with your own cookies?'):
            print_with_tag(tag, 'How did you get the cookies?')
            where_did_you_get = input(
                'From the Chrome Desktop Console/From the Firefox\'s Cookies Quick Manager[Type 1 or 2]:')
            if where_did_you_get == '1':
                cookies = input('Please enter the cookies:')
                print_with_tag(tag, 'Parsing the cookies..')
                cookies_dict = {}
                lst = cookies.split(';')
                for each_key in lst:
                    name = each_key.split('=')[0]
                    value = each_key.split('=')[1]
                    cookies_dict[name] = value
                print_with_tag(tag, 'Done!')
                with open('cookies', 'w+') as f:
                    f.write(json.dumps(cookies_dict))
                s.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
                piviv_user_cookies_is_not_empty = True
            elif where_did_you_get == '2':
                if input_yn('Did you saved the json file to ' + program_path + ' ?'):
                    cookies_file = open(program_path + 'cookies.json', 'r')
                    cookies = json.loads(cookies_file.read())
                    cookies_file.close()
                    print_with_tag(tag, 'Parsing the cookies..')
                    ex_cookies = {}
                    for each_key in cookies:
                        name = each_key['Name raw']
                        value = each_key['Content raw']
                        ex_cookies[name] = value
                    print_with_tag(tag, 'Done!')
                    with open('cookies', 'w+') as f:
                        f.write(json.dumps(ex_cookies))
                    s.cookies = requests.utils.cookiejar_from_dict(ex_cookies)
                    piviv_user_cookies_is_not_empty = True
                else:
                    print_with_tag(tag, 'You should save that json file to your current program dir.')
                    print_with_tag(tag, 'Bye!!')
                    exit()
        else:
            print_with_tag(tag, 'You can not run this program without log in.')
            print_with_tag(tag, 'Bye!!')
            exit()

            # chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument('--proxy-server=socks5://192.168.31.105:10808')
            # pixiv_login_web = webdriver.Chrome(options=chrome_options)
            # pixiv_login_web.get(login_url)
            # pixiv_login_web.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[1]/input').send_keys(
            #     pixiv_user_name)
            # pixiv_login_web.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[2]/input').send_keys(
            #     pixiv_user_pass)
            # pixiv_login_web.find_element_by_xpath('//*[@id="LoginComponent"]/form/button').click()
            # while pixiv_login_web.current_url == 'https://accounts.pixiv.net/login':
            #     time.sleep(1)
            #     print(time.localtime())
            #     print("The web page haven't redirected..")
            #     print('If the Google reCaptcha show up,Please finish it.')
            # print('Redirected!')
            # final_cookies = pixiv_login_web.get_cookies()
            # for cookie in final_cookies:
            #     s.cookies.set(cookie['name'], cookie['value'])
            # with open('cookies', 'w+') as f:
            #     f.write(json.dumps(requests.utils.dict_from_cookiejar(s.cookies)))
            # piviv_user_cookies_is_not_empty = True


def load_cookies():
    tag = 'Load_Cookies'
    if not piviv_user_cookies_is_not_empty:
        print_with_tag(tag, 'Cookies is empty.')
        if not direct_mode:
            update_user_cookies()
    else:
        print_with_tag(tag, 'Cookies is not empty.')
        pixiv_user_cookies_dict = dict(pixiv_user_cookies)
        s.cookies = requests.utils.cookiejar_from_dict(pixiv_user_cookies_dict)
        print_with_tag(tag, 'Cookies is loaded.')


load_cookies()

"""
Mode
    0:Daily
    1:weekly
    2:monthly
    3:rookie
    4:male
    5:female
"""

ranking_types = ['daily', 'weekly', 'monthly', 'rookie', 'original', 'male', 'female', 'daily_r18', 'weekly_r18',
                 'male_r18',
                 'female_r18', 'r18g']


def format_pixiv_ranking_url(year_month, day, page, mode=1):
    tag = 'Ranking_Url_Format'
    ranking_type = "daily"
    if mode < 12:
        ranking_type = ranking_types[mode]
    else:
        print_with_tag(tag, "Unknown Mode")
        exit()
    print_with_tag(tag, ['Type:', ranking_type])
    ranking_url = 'https://www.pixiv.net/ranking.php?mode=' + ranking_type + '&date=' + year_month + str(
        day) + '&p=' + str(
        page) + '&format=json'
    return ranking_url


#
def format_pixiv_illust_url(illust_id):
    illust_url = 'https://www.pixiv.net/artworks/' + str(illust_id)
    return illust_url


def get_pixiv_user_name():
    global login_status
    tag = 'Get_Pixiv_User_Name'
    # Check if cookies works.
    pixiv_www_url = 'https://www.pixiv.net/'
    check_soup = BeautifulSoup(get_text_from_url(pixiv_www_url), 'html.parser')
    try:
        pixiv_user_nick_name = check_soup.find(name='a', attrs={'class': 'user-name js-click-trackable-later'}).string
        print_with_tag(tag, ['Login as', pixiv_user_nick_name])
    except Exception as e:
        print_with_tag(tag,['Error:',e])
        login_status = False
        print_with_tag(tag,'Failed to check the user name.')
        print_with_tag(tag,'Might be the cookies is out of the date or you are using the direct mode?')
    else:
        login_status = True
        print_with_tag(tag,'Login success!')

#
'''
 mode:
    1.single
    2.multiple
'''


def update_database(illustID, illustTitle, illustType, userId, userName, tags, urls):
    tag = 'Update_Database'
    # Connect database
    conn = sqlite3.connect('illust_data.db')
    c = conn.cursor()
    # Create table
    if len(c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ILLUST_DATA'").fetchall()) == 0:
        print_with_tag(tag, 'Creating table..')
        c.execute('''CREATE TABLE ILLUST_DATA
                     (ID INT PRIMARY KEY NOT NULL, TITLE TEXT NOT NULL, TYPE INT NOT NULL, USER_ID INT NOT NULL,USER_NAME TEXT NOT NULL,TAGS TEXT NOT NULL,IMG_SRC TEXT NOT NULL)''')
        print_with_tag(tag, 'Done.')
    if len(c.execute("SELECT ID FROM ILLUST_DATA WHERE ID = ?", (str(illustID),)).fetchall()) == 0:
        print_with_tag(tag, ['Ready to insert data for ID:', str(illustID)])
        # Insert a row of data
        sql = "INSERT INTO ILLUST_DATA(ID,TITLE,TYPE,USER_ID,USER_NAME,TAGS,IMG_SRC)VALUES(?,?,?,?,?,?,?)"
        c.execute(sql, (str(illustID), str(illustTitle), str(illustType),
                        str(userId), str(userName), str(tags), str(urls)))
        print_with_tag(tag, 'Insert done.')
        # Save (commit) the changes
        conn.commit()
        print_with_tag(tag, 'Committed.')
    else:
        print_with_tag(tag, ['ID exist:', str(illustID)])
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()


def format_pixiv_illust_original_url(id_url, mode=1):
    tag = 'Format_Pixiv_Illust_Original_Url'
    if mode == 1:
        contents = get_text_from_url(id_url)
        try:
            img_src_re = re.compile(r'\"urls\":{.*?}')
            img_src = img_src_re.findall(contents)
            final_dict = json.loads("{" + img_src[0] + "}")
            return final_dict['urls']['original']
        except Exception as e:
            print_with_tag(tag, "An error occurred when parsing the json file.")
            print_with_tag(tag, e)
    elif mode == 2:
        data_list = []
        json_datas = get_text_from_url(id_url)
        json_datas_format = json.loads(json_datas)['body']
        for urls in json_datas_format:
            data_list.append(urls['urls']['original'])
        return data_list


def format_pixiv_user_profile_all_url(target_user_id):
    profile_all_url = "https://www.pixiv.net/ajax/user/" + str(target_user_id) + "/profile/all"
    return profile_all_url


def get_illust_infos_from_illust_url(url):
    data_dict = {}
    illust_url_content = get_text_from_url(url)
    # illust_url_content.encoding = 'unicode_escape'
    new_soup = BeautifulSoup(illust_url_content,'html.parser')
    json_data = new_soup.find(name='meta',attrs={'name':'preload-data'}).attrs['content']
    format_json_data = demjson.decode(json_data)
    pre_catch_id = list(format_json_data['illust'].keys())[0]
    illust_info = format_json_data['illust'][pre_catch_id]
    # get each value
    data_dict['illustId'] = illust_info['illustId']
    data_dict['illustTitle'] = illust_info['illustTitle']
    data_dict['illustComment'] = illust_info['illustComment']
    data_dict['createDate'] = illust_info['createDate']
    data_dict['illustType'] = illust_info['illustType']
    data_dict['urls'] = illust_info['urls']
    # data_dict['tags']=illust_info['tags']
    data_dict['userId'] = illust_info['userId']
    data_dict['userName'] = illust_info['userName']
    data_dict['userAccount'] = illust_info['userAccount']
    data_dict['likeData'] = illust_info['likeData']
    data_dict['width'] = illust_info['width']
    data_dict['height'] = illust_info['height']
    data_dict['pageCount'] = illust_info['pageCount']
    data_dict['bookmarkCount'] = illust_info['bookmarkCount']
    data_dict['likeCount'] = illust_info['likeCount']
    data_dict['commentCount'] = illust_info['commentCount']
    data_dict['viewCount'] = illust_info['viewCount']
    data_dict['isOriginal'] = illust_info['isOriginal']
    per_tags = illust_info['tags']['tags']
    tags_list = []
    for tag in range(len(per_tags)):
        tags_list.append(per_tags[tag]['tag'])
    data_dict['tags'] = tags_list
    ###########################################################
    update_database(data_dict['illustId'], data_dict['illustTitle'], data_dict['illustType'], data_dict['userId'],
                    data_dict['userName'], data_dict['tags'], data_dict['urls'])
    return data_dict


def format_multi_illust_json_url(multi_illust_id):
    multi_illust_json_url = 'https://www.pixiv.net/ajax/illust/' + str(multi_illust_id) + '/pages'
    return multi_illust_json_url


def dynamic_download_and_Synthesizing(illust_id, title=None, prefix=None):
    tag = 'Dynamic_Download_And_Synthesizing'
    d_json_data = 'https://www.pixiv.net/ajax/illust/' + str(illust_id) + '/ugoira_meta'
    d_json_decoded = json.loads(get_text_from_url(d_json_data))['body']
    src_zip_url = d_json_decoded['originalSrc']
    src_mime_type = d_json_decoded['mime_type']
    src_img_delay = int(d_json_decoded['frames'][0]['delay']) / 1000
    src_saved_path = save_path + 'TEMP' + global_symbol + str(illust_id) + global_symbol + \
                     src_zip_url.split('/')[-1]
    src_saved_dir = save_path + 'TEMP' + global_symbol + str(illust_id) + global_symbol
    src_final_dir = save_path + 'Dynamic' + global_symbol
    download_thread(src_zip_url, save_path, None, 'TEMP' + global_symbol + str(illust_id))
    while not os.path.exists(src_saved_path + '.done'):
        time.sleep(1)
        print_with_tag(tag, 'Waiting for complete...')
    print_with_tag(tag, ['Zip target downloaded:', src_saved_path])
    with zipfile.ZipFile(src_saved_path, 'r') as zip_file:
        zip_file.extractall(path=src_saved_dir)
    # get each frame
    sort_by_num = []
    frames = []
    for root, dirs, files in os.walk(src_saved_dir):
        for file in files:
            if file.endswith('jpg') or file.endswith('png'):
                sort_by_num.append(src_saved_dir + global_symbol + file)
    sort_by_num.sort()
    print_with_tag(tag, 'Reading each frame..')
    for each_frame in sort_by_num:
        frames.append(imageio.imread(each_frame))
    gif_save_dir = save_path + str(prefix) + global_symbol + year_month + str(
        day) + global_symbol + 'D-' + str(illust_id) + global_symbol
    gif_name_format = re.sub('[\/:*?"<>|]', '_', str(title)) + '-' + str(illust_id) + '.gif'
    if not os.path.exists(gif_save_dir):
        os.makedirs(gif_save_dir)
    print_with_tag(tag, 'Synthesizing dynamic images..')
    try:
        imageio.mimsave(gif_save_dir + gif_name_format, frames, duration=src_img_delay)
    except Exception as e:
        print_with_tag(tag, [gif_save_dir + gif_name_format])
        print_with_tag(tag, e)
        exit()


def download_file(url, path, sign=False):
    tag = 'Download_File'
    print_with_tag(tag, ['Original Download URL:', url])
    download_proxy = s.proxies
    global current_threads, download_params
    current_threads += 1
    host_dl = ''
    temp_headers = download_params
    if d_dtrp_enable:
        url = url.replace('i.pximg.net', d_dtrp_address)
        host_dl = d_dtrp_address
        download_proxy = None
        print_with_tag(tag, ['DTRP URL =>', url])
        print_with_tag(tag, ['DTRP HOST =>', host_dl])

    else:
        if sni_bypass:
            url = url.replace('i.pximg.net', dl_server_ip)
            host_dl = 'i.pximg.net'
            print_with_tag(tag, ['SNI HOST =>', host_dl])
            print_with_tag(tag, ['SNI URL =>', url])
            download_proxy = None
            temp_headers['host'] = host_dl

    print_with_tag(tag, ["Thread ID:" + str(_thread.get_ident())])
    path_output = path
    retry = 0
    while True:
        try:
            if retry == 3:
                print_with_tag(tag, 'Max retried reached')
                exit()
            retry += 1
            with s.get(url, stream=True, proxies=download_proxy, headers=temp_headers) as pic:
                pic.raise_for_status()
                if os.path.exists(path_output):
                    current_threads -= 1
                    print_with_tag(tag, ["File exists:" + path_output, "Skip!"])
                    return False
                try:
                    with open(path_output, 'wb') as f:
                        for chunk in pic.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                except Exception as e:
                    print_with_tag(tag, 'An error occurred when saving files.')
                    print_with_tag(tag, e)
                else:
                    print_with_tag(tag, ["File Saved:" + path_output])
                    if sign:
                        with open(path_output + '.done', 'w+') as f:
                            f.write('\nDone!')
                            print_with_tag(tag, 'Created a sign for main thread.')
        except Exception as e:
            print_with_tag(tag, 'An error occurred when Downloading files.')
            print_with_tag(tag, e)
        else:
            current_threads -= 1
            return True


def download_thread(url, path, exfile_name=None, exfile_dir=None):
    tag = 'Download_Thread'
    wait_for_limit()
    local_path = path
    give_it_a_sign = False
    local_filename = url.split('/')[-1]
    if local_filename.endswith('zip'):
        give_it_a_sign = True
    if exfile_dir is not None:
        local_path += exfile_dir + global_symbol
    if exfile_name is not None:
        local_filename = exfile_name + "-" + local_filename
    path_output = local_path + local_filename
    print_with_tag(tag, ["File Location:" + path_output])
    if not os.path.exists(local_path):
        print_with_tag(tag, "Folder doesn't exists!!")
        os.makedirs(local_path)
        print_with_tag(tag, "Folder Created.")

    retry_count = 0
    while True:
        try:
            _thread.TIMEOUT_MAX = 60
            _thread.start_new_thread(download_file, (url, path_output, give_it_a_sign))
        except:
            print_with_tag(tag, "Error.")
            if retry_count == 3:
                print_with_tag(tag, "Not wokring..")
                print_with_tag(tag, "Skip!!")
            else:
                print_with_tag(tag, "Starting retry..")
                retry_count += 1
        else:
            print_with_tag(tag, "Download thread successfully started!")
            break
    print_with_tag(tag, ['Threads_count:', str(current_threads)])


def wait_for_limit():
    tag = 'Limit_Lock'
    while current_threads >= subthreads_limit:
        print_with_tag(tag, 'Max Threads Reached,Waiting for release..')
        time.sleep(1)


while (True):
    tag = 'Main_Stage'
    current_threads = 0
    get_pixiv_user_name()
    print_with_tag(tag, 'What do you want to do?')
    print_with_tag(tag, "Download the selected ranking pics(1)")
    print_with_tag(tag, "Download the pics from a user(2)")
    print_with_tag(tag, 'Download the pics that you marked(3)')
    print_with_tag(tag, 'Update the user cookies(4)')
    print_with_tag(tag, 'Parse an illust info with given illust id(5)')
    print_with_tag(tag, 'Search something via single key word(6)')
    print_with_tag(tag, 'Download the illusts from recommender(7)')
    print_with_tag(tag, 'Exit(8)')
    choose = input("Your choose[1-8]:")
    if choose == '1':
        tag = 'Download_Ranking_Pics'
        mode_asked = int(input('Please choose the ranking type(0-11):'))
        # 倒序取出可用日期
        if input_yn('Do you want to choose a date?'):
            choose_date = input('Please enter the date like 2019-01-01:')
            date_dict = choose_date.split('-')
            year_month = date_dict[0] + date_dict[1]
            day = date_dict[2]
        else:
            print_with_tag(tag, 'Testing available day of mode 1..')
            for i in reversed(range(1, int(day) + 1)):
                if i == 1:
                    last_month = int(time.strftime('%m', time.localtime())) - 1
                    print_with_tag(tag, ['Changing the month to', str(last_month)])
                    if last_month < 10:
                        last_month = '0' + str(last_month)
                    year_minus_month = time.strftime('%Y', time.localtime()) + str(last_month)
                    for last_i in reversed(range(1, 32)):
                        print_with_tag(tag, ["Changing the day param to :", last_i])
                        ranking_daily_json = get_text_from_url(
                            format_pixiv_ranking_url(year_minus_month, str(last_i), page))
                        if get_text_from_url(
                                format_pixiv_ranking_url(year_minus_month, str(last_i), page), 2) == 200:
                            print_with_tag(tag, ["Found the available Day at day " + str(last_i)])
                            print_with_tag(tag, ['Final ranking date:', year_minus_month + str(last_i)])
                            year_month = year_minus_month
                            day = last_i
                            break
                        else:
                            print_with_tag(tag, ["Error Status code:", get_text_from_url(
                                format_pixiv_ranking_url(year_minus_month, str(last_i), page), 2), "at day " + str(i)])
                    break
                if i < 10:
                    print_with_tag(tag, 'Auto add zero..')
                    i = '0' + str(i)
                print_with_tag(tag, ["Changing day param to :", str(i)])
                ranking_daily_json = get_text_from_url(format_pixiv_ranking_url(year_month, i, page))
                ranking_json_status_code = get_text_from_url(format_pixiv_ranking_url(year_month, i, page), 2)
                if ranking_json_status_code == 200:
                    print_with_tag(tag, "Found the available Day at day " + str(i))
                    day = i
                    break
                else:
                    print_with_tag(tag, ["Error Status code:", str(ranking_json_status_code), "at day " + str(i)])

        start_time = time.time()
        #
        # 共10页json
        for i in range(1, max_page + 1):
            print_with_tag(tag, ["Catching Page:", str(i)])
            print_with_tag(tag, ['You selected:', mode_asked])
            url = format_pixiv_ranking_url(year_month, day, i, mode_asked)
            print_with_tag(tag, ["URL TARGET: " + url])
            json_source_contents = get_text_from_url(url)
            json_data = json.loads(json_source_contents)
            temp_header = s.headers
            temp_header['referer'] = url
            s.headers = temp_header
            for item in range(50):
                single_data = json_data['contents'][item]
                title = single_data['title']
                date = single_data['date']
                tagd = single_data['tags']
                user_name = single_data['user_name']
                user_id = single_data['user_id']
                illust_id = single_data['illust_id']
                rank = single_data['rank']
                rating_count = single_data['rating_count']
                view_count = single_data['view_count']
                illust_type_code = single_data['illust_type']
                illust_type = "Unknown"
                if illust_type_code == '0':
                    illust_type = 'Single'
                elif illust_type_code == '1':
                    illust_type = 'Multiple'
                elif illust_type_code == '2':
                    illust_type = 'Dynamic'
                if print_info:
                    print('-----Index of:', i, "Count", item)
                    print('Title:', title)
                    print('Date:', date)
                    print('Tag:', tagd)
                    print('User_name:', user_name)
                    print('User_id:', user_id)
                    print('illust_id:', illust_id)
                    print('Rank:', rank)
                    print('Rating_count:', rating_count)
                    print('View_count:', view_count)
                    print('Type:', illust_type)
                info_data = get_illust_infos_from_illust_url(format_pixiv_illust_url(illust_id))
                if int(bookmarked_filter) > 0:
                    current_marked = int(info_data['bookmarkCount'])
                    if current_marked < int(bookmarked_filter):
                        print_with_tag(tag, [illust_id, 'current_marked:', current_marked, 'pass!!'])
                        continue
                if illust_type_code == '0':
                    print_with_tag(tag, 'Single Download start!!')
                    # pic_url = format_pixiv_illust_original_url(format_pixiv_illust_url(illust_id))
                    pic_url = info_data['urls']['original']

                    print_with_tag(tag, ['Picture source address:', pic_url])
                    download_thread(pic_url, save_path, re.sub('[\/:*?"<>|]', '_', title),
                                    ranking_types[mode_asked] + global_symbol + year_month + str(day))
                elif illust_type_code == '1':
                    if not download_manga_enable:
                        continue
                    print_with_tag(tag, 'Multiple Download start!!')
                    data_listed = format_pixiv_illust_original_url(format_multi_illust_json_url(illust_id), 2)
                    for each_one in data_listed:
                        print_with_tag(tag, ['One of Multiple Picture source address:', each_one])
                        download_thread(each_one, save_path, re.sub('[\/:*?"<>|]', '_', title),
                                        ranking_types[mode_asked] + global_symbol + year_month + str(
                                            day) + global_symbol + 'M-' + str(illust_id))
                elif illust_type_code == '2':
                    if not download_gif_enable:
                        continue
                    print_with_tag(tag, 'Dynamic Download start!')
                    time_start_d_s = time.time()
                    dynamic_download_and_Synthesizing(illust_id, title, ranking_types[mode_asked])
                    print_with_tag(tag, 'Dynamic saved.')
                    print_with_tag(tag, ['Synthesizing cost:', time.time() - time_start_d_s])
        print('Job finished!')
        print('Total cost:', time.time() - start_time)
    elif choose == '2':
        tag = 'Download_Pics_From_A_User'
        target_user_id = int(input("Please enter the target user id(like 17300903):"))
        profile_all = get_text_from_url(format_pixiv_user_profile_all_url(target_user_id))
        profile_all_json = json.loads(profile_all)
        all_illusts = profile_all_json['body']['illusts']
        illusts_ids = all_illusts.keys()
        total_ids = len(illusts_ids)
        download_count = 0
        for single_illust in illusts_ids:
            download_count += 1
            print_with_tag(tag, ["Downloading", str(download_count), "of", total_ids])
            download_thread(format_pixiv_illust_original_url(format_pixiv_illust_url(single_illust)),
                            save_path,
                            re.sub('[\/:*?"<>|]', '_',
                                   get_illust_infos_from_illust_url(format_pixiv_illust_url(single_illust))[
                                       'illustTitle']),
                            str(target_user_id))
        print_with_tag(tag, 'ALL Done')
    elif choose == '3':
        tag = 'Download_From_Bookmark'
        print_with_tag(tag, 'Catching your bookmark..')
        bookmark = get_text_from_url('https://www.pixiv.net/bookmark.php')
        soup = BeautifulSoup(bookmark, 'html.parser')

        book_pages = soup.find(name='ul', attrs={'class': 'page-list'})
        book_total_page = len(book_pages)

        format_book_page_url = 'https://www.pixiv.net/bookmark.php?rest=show&p='

        for single_page in range(1, book_total_page + 1):
            print_with_tag(tag, ['Starting bookmark download for page', str(single_page), 'of', book_total_page])
            per_page = get_text_from_url(format_book_page_url + str(single_page))
            per_soup = BeautifulSoup(per_page, 'html.parser')
            bookmark_datas = per_soup.find(name='ul', attrs={'class': '_image-items js-legacy-mark-unmark-list'})
            for marked_illust_id in bookmark_datas:
                switch = marked_illust_id.a['class']
                start_time = time.time()
                if switch == ['work', '_work']:
                    illust_type = 'Single'
                    # Info1
                    each_marked_illust = marked_illust_id.find(name='a', attrs={'class': "work _work"})
                    each_info1 = each_marked_illust.find(name='div', attrs={'class': '_layout-thumbnail'})
                    single_img_arrtrs_dict = each_info1.find(name='img').attrs
                    illust_id = single_img_arrtrs_dict['data-id']
                    tag = single_img_arrtrs_dict['data-tags']
                    user_id = single_img_arrtrs_dict['data-user-id']
                    # Info2
                    title_class = marked_illust_id.find(name="h1", attrs={'class': 'title'}).attrs
                    title = title_class['title']
                    user_name_class = marked_illust_id.find(name="a", attrs={'class': 'user ui-profile-popup'}).attrs
                    user_name = user_name_class['data-user_name']
                    if print_info:
                        print('----- ')
                        print('Title:', title)
                        print('User_id:', user_id)
                        print('User_name:', user_name)
                        print('illust_id:', illust_id)
                        print('Tag:', tag)
                        print('Type:', illust_type)
                    download_thread(format_pixiv_illust_original_url(format_pixiv_illust_url(illust_id)), save_path,
                                    re.sub('[\/:*?"<>|]', '_', title),
                                    'Bookmark')

                elif switch == ['work', '_work', 'multiple']:
                    illust_type = 'Multiple'
                    each_marked_illust = marked_illust_id.find(name='a', attrs={'class': 'work _work multiple'})
                    each_info1 = each_marked_illust.find(name='div', attrs={'class': '_layout-thumbnail'})
                    single_img_arrtrs_dict = each_info1.find(name='img').attrs
                    illust_id = single_img_arrtrs_dict['data-id']
                    tag = single_img_arrtrs_dict['data-tags']
                    user_id = single_img_arrtrs_dict['data-user-id']
                    # Info2
                    title_class = marked_illust_id.find(name="h1", attrs={'class': 'title'}).attrs
                    title = title_class['title']
                    user_name_class = marked_illust_id.find(name="a", attrs={'class': 'user ui-profile-popup'}).attrs
                    user_name = user_name_class['data-user_name']
                    if print_info:
                        print('----- ')
                        print('Title:', title)
                        print('User_id:', user_id)
                        print('User_name:', user_name)
                        print('illust_id:', illust_id)
                        print('Tag:', tag)
                        print('Type:', illust_type)

                    data_listed = format_pixiv_illust_original_url(format_multi_illust_json_url(illust_id), 2)
                    for each_one in data_listed:
                        print_with_tag(tag, 'Start downloading multiple picture..')
                        print_with_tag(tag, ['Single_URL:', each_one])
                        download_thread(each_one, save_path, re.sub('[\/:*?"<>|]', '_', title),
                                        'Bookmark/M-' + illust_id)
                print_with_tag(tag, ['Total cost:', time.time() - start_time])
        print_with_tag(tag, 'ALL DONE!')
    elif choose == '4':
        update_user_cookies()
    elif choose == '5':
        tag = 'Parse_Illust_Info'
        single_illust = input('Please enter the single illust id(like 76073572):')
        illust_infos = get_illust_infos_from_illust_url(format_pixiv_illust_url(single_illust))
        print_with_tag(tag, ['---------INFO-of-ID:' + single_illust + '---------'])
        for each_info in list(dict.keys(illust_infos)):
            print_with_tag(tag, [each_info + ':', str(illust_infos[each_info])])
        if input_yn('Do you want to download it?'):
            illust_type = illust_infos['illustType']
            illust_id = illust_infos['illustId']
            illust_title = illust_infos['illustTitle']
            if illust_type == 0:
                print_with_tag(tag, 'Starting Download!')
                download_thread(illust_infos['urls']['original'], save_path,
                                re.sub('[\/:*?"<>|]', '_', illust_title),
                                'manual' + global_symbol + year_month + str(day))
            elif illust_type == 1:
                print_with_tag(tag, 'Parsing datas...')
                data_listed = format_pixiv_illust_original_url(format_multi_illust_json_url(illust_id), 2)
                for each_one in data_listed:
                    print_with_tag(tag, ['One of Multiple Picture source address:', each_one])
                    print_with_tag(tag, 'Starting Download!')
                    download_thread(each_one, save_path, re.sub('[\/:*?"<>|]', '_', illust_title),
                                    'manual' + global_symbol + year_month + str(
                                        day) + global_symbol + 'M-' + str(illust_id))
            elif illust_type == 2:
                dynamic_download_and_Synthesizing(illust_id, illust_title, 'manual')
        print_with_tag(tag, 'Done!')
    elif choose == '6':
        tag = 'Search_Via_Key_Word'
        '''
        mode 
            0:all
            1:safe
            2:r18
        type
            0:search.php?s_mode=s_tag_full(illust and manga)[word]
            1:novel/search.php?(novel)[word]
            2:search_user.php?s_mode=s_usr(user)[nick]<no global filter>
        filter global 0
            0:date_d    (latest)
            1:data      (older)
            2:popular_d
            3:popular_male_d
            4:popular_female_d    
        filter 1 (type=1)
            0:tags.php?(tag)
            1:search.php?s_mode=s_tag(key word)   
            2:search.php?s_mode=s_tc(full text)
        filter 2:0 (type=2)
            0:&i=0(all)
            1:&i=1(has works)
        filter 2:1
            0:&nick_mf=1(full match)
            1:&nick_mf=0(parts match)           

        path_url=home_url+type_url+key+filter+[filter_sec]+page+mode        
        '''
        search_type_list = ['search.php?', 'novel/', 'search_user.php?s_mode=s_usr']
        search_filter_0_list = ['date_d', 'date', 'popular_d', 'popular_male_d', 'popular_female_d']
        search_filter_1_list = ['tags.php?', 'search.php?s_mode=s_tag', 'search.php?s_mode=s_tc']

        search_mode_list = ['all', 'safe', 'r18']
        # home_url
        search_url = 'https://www.pixiv.net/'
        # type_url
        type_int = int(input('Please enter the search type[0-2]:'))
        search_type = search_type_list[type_int]
        # key
        search_key_word = 'word='
        if type_int == 2:
            search_key_word = 'nick='
        search_key_word += input('Please enter the single key word:')
        # filter 0
        search_filter_0 = ''
        if type_int != 2:
            search_filter_0 = '&order=' + search_filter_0_list[int(input('Please enter the global filter[0-4]:'))]
        # filter 1 x extra check
        search_filter_1 = ''
        if type_int == 1:
            search_filter_1 = search_filter_1_list[int(input('Please enter the second filter[0-2]:'))]
        # filter 2 0
        search_filter_2_0 = ''
        # filyer 2 1
        search_filter_2_1 = ''
        if type_int == 2:
            search_filter_2_0 = '&i=' + input('Want a artist?[0-1]')
            search_filter_2_1 = '&nick_mf=' + input('Full match?[0-1]')
        # page
        search_page = '&p=' + input('Please enter the page num[1-1000]:')
        # mode
        search_mode = ''
        if type_int != 2:
            search_mode = '&mode=' + search_mode_list[int(input('Please enter the search mode[0-2]:'))]
        # path_url
        prefix = '&'
        search_target_url = ''
        while True:
            if type_int == 0:
                search_target_url = search_url + search_type + search_key_word + search_filter_0 + search_page + search_mode
                print_with_tag(tag, ['Search URL:', search_target_url])
                search_single_page_data = json.loads(
                    BeautifulSoup(get_text_from_url(search_target_url), 'html.parser').find(name='input', attrs={
                        'id': 'js-mount-point-search-result-list'}).attrs['data-items'])
                print_with_tag(tag, ['-------Search result start!-------'])
                illust_count = len(search_single_page_data)
                for single_illust_count in range(0, illust_count):
                    print_with_tag(tag, ['#', single_illust_count])
                    for per_info in list(dict.keys(search_single_page_data[single_illust_count])):
                        print_with_tag(tag, [per_info + ':', search_single_page_data[single_illust_count][per_info]])
                print_with_tag(tag, ['-------End search result for page', search_page.split('=')[1] + '-------'])
                if input_yn('Do you want to download one?'):
                    download_target = int(input('Which one you want to download?[0-' + str(illust_count - 1) + ']:'))
                    illust_id = search_single_page_data[download_target]['illustId']
                    illust_infos = get_illust_infos_from_illust_url(format_pixiv_illust_url(illust_id))
                    illust_type = illust_infos['illustType']
                    illust_title = illust_infos['illustTitle']
                    if illust_type == 0:
                        print_with_tag(tag, 'Starting Download!')
                        download_thread(illust_infos['urls']['original'], save_path,
                                        re.sub('[\/:*?"<>|]', '_', illust_title),
                                        'search' + global_symbol + year_month + str(day))
                    elif illust_type == 1:
                        print_with_tag(tag, 'Parsing datas...')
                        data_listed = format_pixiv_illust_original_url(format_multi_illust_json_url(illust_id), 2)
                        for each_one in data_listed:
                            print_with_tag(tag, ['One of Multiple Picture source address:', each_one])
                            print_with_tag(tag, 'Starting Download!')
                            download_thread(each_one, save_path, re.sub('[\/:*?"<>|]', '_', illust_title),
                                            'search' + global_symbol + year_month + str(
                                                day) + global_symbol + 'M-' + str(illust_id))
                    elif illust_type == 2:
                        dynamic_download_and_Synthesizing(illust_id, illust_title, 'search')
                    print_with_tag(tag, 'Select done.')
                if input_yn('Do you want to switch to next page?'):
                    search_page = search_page.split('=')[0] + '=' + str(int(search_page.split('=')[1]) + 1)
                else:
                    break
            elif type_int == 1:
                search_target_url = search_url + search_type + prefix + search_filter_1 + search_key_word + search_filter_0 + search_page + search_mode
            elif type_int == 2:
                search_target_url = search_url + search_type + prefix + search_filter_1 + search_key_word + search_filter_2_0 + search_filter_2_1 + search_page


    elif choose == '7':
        tag = 'Download_From_Recommender'
        if not login_status:
            print_with_tag(tag,'You must login before start this function.')
            continue
        illust_download_limit = int(input('Set a limit for downloading?[1-1000]:'))
        # recommender_user_and_illust_url='https://www.pixiv.net/rpc/index.php?mode=get_recommend_users_and_works_by_user_ids&user_ids=211974,6148565,11&user_num=30&work_num=5'
        recommender_illust_url = 'https://www.pixiv.net/rpc/recommender.php?type=illust&sample_illusts=auto&num_recommendations=1000&page=discovery&mode=all'
        illusts_ids = json.loads(get_text_from_url(recommender_illust_url))['recommendations']
        print_with_tag(tag, ['illust_count:', len(illusts_ids)])
        for single_id in range(0, illust_download_limit):
            illust_infos = get_illust_infos_from_illust_url(format_pixiv_illust_url(illusts_ids[single_id]))
            illust_type = illust_infos['illustType']
            illust_id = illust_infos['illustId']
            illust_title = illust_infos['illustTitle']
            if illust_type == 0:
                print_with_tag(tag, 'Starting Download!')
                download_thread(illust_infos['urls']['original'], save_path,
                                re.sub('[\/:*?"<>|]', '_', illust_title),
                                'recommender' + global_symbol + year_month + str(day))
            elif illust_type == 1:
                print_with_tag(tag, 'Parsing datas...')
                data_listed = format_pixiv_illust_original_url(format_multi_illust_json_url(illust_id), 2)
                for each_one in data_listed:
                    print_with_tag(tag, ['One of Multiple Picture source address:', each_one])
                    print_with_tag(tag, 'Starting Download!')
                    download_thread(each_one, save_path, re.sub('[\/:*?"<>|]', '_', illust_title),
                                    'recommender' + global_symbol + year_month + str(
                                        day) + global_symbol + 'M-' + str(illust_id))
            elif illust_type == 2:
                dynamic_download_and_Synthesizing(illust_id, illust_title, 'recommender')

    elif choose == '8':
        tag = 'Exit'
        print_with_tag(tag, 'Bye!!')
        exit()
