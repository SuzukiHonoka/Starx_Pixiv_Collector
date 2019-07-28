#!/usr/bin/python3
import re
import socket
import socks
import requests
import time
import json
import os
import _thread
import configparser

print('Welcome to use Pixiv ranking collector !!')
print('This program is powered by Starx.')

proxy_enable = False
proxy_host = ''
proxy_port = ''
pixiv_user_name = ''
pixiv_user_pass = ''
#
if not os.path.exists('config.ini'):
    if input('Did you want to use socks5 proxy? (Y/N):') == 'Y':
        proxy_host = input('Please enter the socks5 server host ip address:')
        proxy_port = int(input('Please enter the socks5 server host port number:'))
    else:
        print('Not using the proxy..')
        proxy_enable = False
    pixiv_user_name = input("Please enter your own pixiv account name:")
    pixiv_user_pass = input("Please enter your own pixiv account password:")
    if input('Are you sure about that account information correct? (Y/N):') == 'Y':
        if input('Do you want to save this configuration as a file? (Y/N):') == 'Y':
            path = os.path.abspath('.') + "\\"
            config_name = "config.ini"
            abs_path = path + config_name
            if os.path.exists(abs_path):
                with open(abs_path, 'w'):
                    print('Creating empty config file')
            config = configparser.RawConfigParser()
            config.add_section('Proxy')
            config.set('Proxy', 'Enable', str(proxy_enable))
            config.set('Proxy', 'IP', proxy_host)
            config.set('Proxy', 'PORT', proxy_port)
            config.add_section("Account")
            config.set('Account', 'User_name', pixiv_user_name)
            config.set('Account', 'User_pass', pixiv_user_pass)
            with open(abs_path, 'w+') as f:
                config.write(f)
        print('Done!')
else:
    config = configparser.ConfigParser()
    config.read('config.ini')
    proxy_enable = bool(config['Proxy']['Enable'])
    proxy_host = config['Proxy']['IP']
    proxy_port = config['Proxy']['PORT']
    pixiv_user_name = config['Account']['User_name']
    pixiv_user_pass = config['Account']['User_pass']
#
if proxy_enable:
    print('Gonna connect to your socks5 server...')
    try:
        socks.set_default_proxy(socks.SOCKS5, proxy_host, int(proxy_port))
        socket.socket = socks.socksocket
        socket.timeout = 500
    except:
        print('When processing the socks5 server an error occurred.')
        exit()
    else:
        print('Proxy connection seems successfully created!!')
else:
    print('Not using the proxy..')

# init get param
params = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/75.0.3770.142 Safari/537.36',
    'authority': 'www.pixiv.net',
    'upgrade-insecure-requests': '1',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6',
    'dnt': '1',
    'referer': 'https://www.pixiv.net/'
}
# init post param
datas = {
    'pixiv_id': 'user_name',
    'password': 'user_password',
    'captcha': '',
    'g_reaptcha_response': '',
    'post_key': '',
    'source': 'accounts',
    'ref': '',
    'return_to': 'https://www.pixiv.net/'
}
print('Changing Request params..')
datas['pixiv_id'] = pixiv_user_name
datas['password'] = pixiv_user_pass
print('Done!')

login_url = 'https://accounts.pixiv.net/login'  # 登陆的URL
post_url = 'https://accounts.pixiv.net/api/login?lang=en'  # 提交POST请求的URL

s = requests.Session()

s.headers = params

# 获取登录页面
res = s.get(login_url, params=params,timeout=10)

# print(res.text)
# 获取post_key
pattern = re.compile(r'name="post_key" value="(.*?)">')
r = pattern.findall(res.text)

datas['post_key'] = r[0]

# 模拟登录
result = s.post(post_url, data=datas,timeout=10)

result_check=json.loads(result.text)

if bool(result_check['error']):
    print("Login Error!!")
    exit()


# 当前日期
year_month = time.strftime("%Y%m", time.localtime())
day = int(time.strftime("%d", time.localtime()))

# param
p_date = '&date='
p_page = '&p='
#
page = 1
max_page = 10

# Finding the available Day
ranking_daily_json = ""

#
"""
Mode
    1:Daily
    2:weekly
    3:monthly
    4:rookie
    5:male
    6:female
"""

def format_pixiv_ranking_url(year_month, day, page, mode=1):
    ranking_type = "daily"
    if mode == 1:
        ranking_type = "daily"
    elif mode == 2:
        ranking_type = "weekly"
    elif mode == 3:
        ranking_type = "monthly"
    elif mode == 4:
        ranking_type = "rookie"
    elif mode == 5:
        ranking_type = "male"
    elif mode == 6:
        ranking_type = "female"
    else:
        print("Unknown Mode")
        exit()

    ranking_url = 'https://www.pixiv.net/ranking.php?mode=' + ranking_type + '&date=' + year_month + str(
        day) + '&p=' + str(
        page) + '&format=json'
    return ranking_url

#
def format_pixiv_illust_url(illust_id):
    illust_url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(illust_id)
    return illust_url

#
def format_pixiv_illust_original_url(id_url):
    contents = s.get(id_url)
    img_src_re = re.compile(r'\"urls\":{.*?}')
    img_src = img_src_re.findall(contents.text)
    final_dict = json.loads("{" + img_src[0] + "}")
    return final_dict['urls']['original']


def download_file(url, path, exfile_name=None):
    print("\nThread ID:" + str(_thread.get_ident()))
    local_filename = pic_url.split('/')[-1]
    if exfile_name is not None:
        local_filename = exfile_name + "-" + local_filename

    path_output = path + local_filename
    print("File Location:" + path_output)

    with s.get(url, stream=True) as pic:
        pic.raise_for_status()
        if os.path.exists(path_output):
            print("File exists:" + path_output, "\nSkip!")
            return False
        try:
            with open(path_output, 'wb') as f:
                for chunk in pic.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except:
            return False
        else:
            print("File Saved:" + path_output)
        return True


mode_asked=int(input('Please choose the ranking type(1-6):'))
# 倒序取出可用日期
start_time = time.time()
for i in reversed(range(1, day + 1)):
    print("Changing day param to :", i)
    ranking_daily_json = s.get(format_pixiv_ranking_url(year_month, i, page))
    if ranking_daily_json.status_code == 200:
        print("Found the available Day at day " + str(i))
        day = i
        break
    else:
        print("Error Status code:", ranking_daily_json.status_code, "at day " + str(i))
#
save_path = os.path.abspath('.') + "\\Pixiv_Daily_Ranking\\"
# 共10页json
for i in range(1, max_page + 1):
    print("Catching Page:", i)
    url = format_pixiv_ranking_url(year_month, day, i,mode_asked)
    print("URL TARGET: " + url)
    json_source_contents = s.get(url)
    json_data = json.loads(json_source_contents.text)
    temp_header = s.headers
    temp_header['referer'] = url
    s.headers = temp_header
    # print("Current Page:", i, json_data)
    for item in range(50):
        single_data = json_data['contents'][item]
        title = single_data['title']
        date = single_data['date']
        tag = single_data['tags']
        user_name = single_data['user_name']
        user_id = single_data['user_id']
        illust_id = single_data['illust_id']
        rank = single_data['rank']
        rating_count = single_data['rating_count']
        view_count = single_data['view_count']

        print('-----Index of:', i, "Count", item)
        print('Title:', title)
        print('Date:', date)
        print('Tag:', tag)
        print('User_name:', user_name)
        print('User_id:', user_id)
        print('illust_id:', illust_id)
        print('Rank:', rank)
        print('Rating_count:', rating_count)
        print('View_count:', view_count)

        pic_url = format_pixiv_illust_original_url(format_pixiv_illust_url(illust_id))
        print('Picture source address:', pic_url)

        # s.headers={"refer":"https://www.pixiv.net/ranking.php?mode=daily&date=20190726"}
        retry_count = 0
        try:
            _thread.TIMEOUT_MAX = 10000
            _thread.start_new_thread(download_file, (pic_url, save_path))
        except:
            print("Error..")
            if retry_count >= 3:
                print("Not wokring..")
                print("Skip!!")
                continue
            else:
                print("Starting retry..")
                retry_count += 1
        else:
            print("Download_Thread success!")

print('Job finished!')
print('Total cost:',time.time()-start_time)
# image_contens=s.get(pic_url,)
# print(image_contens,s.cookies,s.headers)
# 打印出json信息
# print(result.json())
