#!/usr/bin/python3
import _thread
import configparser
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

sys_platform = sys.platform

print('Welcome to use Pixiv ranking collector !!')
print('This program is powered by Starx.')
print('Your are using', sys_platform, "platform.")

# symbol_win='\\'
# symbol_linux='/'
global_symbol = '/'
# if sys_platform == 'linux':
#     global_symbol = symbol_linux
# elif sys_platform == 'win32':
#     global_symbol = symbol_win
# elif sys_platform == 'win64':
#     global_symbol = symbol_win
# else:
#     global_symbol = symbol_linux
# #

program_path = os.path.abspath('.') + global_symbol

save_path = os.path.abspath('.') + global_symbol + "Pixiv_Download" + global_symbol

proxy_enable = False
proxy_host = ''
proxy_port = ''
pixiv_user_name = ''
pixiv_user_pass = ''
pixiv_user_cookies = ''
piviv_user_cookies_is_not_empty = False
cust_path_enable = False

#
if not os.path.exists('config.ini'):
    if input('Do you want to use socks5 proxy? (Y/N):') == 'Y':
        proxy_enable = True
        proxy_host = input('Please enter the socks5 server host ip address:')
        proxy_port = input('Please enter the socks5 server host port number:')
    else:
        print('Not using the proxy..')
        proxy_enable = False
    pixiv_user_name = input("Please enter your own pixiv account name:")
    pixiv_user_pass = input("Please enter your own pixiv account password:")
    if input('Do you want to change default save path? (Y/N):') == 'Y':
        cust_path_enable = True
        save_path = input("Please enter the full path to save the data:") + global_symbol
    if input('Are you sure about that account information correct? (Y/N):') == 'Y':
        if input('Do you want to save this configuration as a file? (Y/N):') == 'Y':
            path = program_path
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
            config.add_section('Data')
            config.set('Data', 'CUST_PATH_ENABLE', cust_path_enable)
            config.set('Data', 'SAVE_PATH', save_path)
            with open(abs_path, 'w+') as f:
                config.write(f)
        print('Done!')
else:
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config['Proxy']['Enable'] == 'True':
        proxy_enable = True
    proxy_host = config['Proxy']['IP']
    proxy_port = config['Proxy']['PORT']
    pixiv_user_name = config['Account']['User_name']
    pixiv_user_pass = config['Account']['User_pass']
    cust_path_enable = config['Data']['CUST_PATH_ENABLE']
    if cust_path_enable:
        save_path = config['Data']['SAVE_PATH']

if os.path.exists("cookies"):
    with open('cookies', 'r') as f:
        cookies = f.read()
        if len(cookies) > 0:
            piviv_user_cookies_is_not_empty = True
            pixiv_user_cookies = json.loads(cookies)
else:
    print('Can not to find the Cookies.')
#

# init get param
params = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/75.0.3770.142 Safari/537.36',
    'authority': 'www.pixiv.net',
    'upgrade-insecure-requests': '1',
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
print('Changing Request params..')
datas['pixiv_id'] = pixiv_user_name
datas['password'] = pixiv_user_pass
print('Done!')

login_url = 'https://accounts.pixiv.net/login'
post_url = 'https://accounts.pixiv.net/api/login?lang=en'

s = requests.Session()


def update_user_cookies():
    s.cookies.clear()
    # 获取登录页面
    res = s.get(login_url, params=params, timeout=10)
    res.raise_for_status()

    pattern = re.compile(r'name="post_key" value="(.*?)">')
    r = pattern.findall(res.text)

    datas['post_key'] = r[0]
    print('Post_Key:', datas['post_key'])

    result = s.post(post_url, data=datas, timeout=10)
    result_check = json.loads(result.text)['body']
    print(result_check)
    if 'success' in result_check:
        print('Login success!')
        with open(program_path + 'cookies', 'w+') as f:
            f.write(json.dumps(result.cookies))
    else:
        print("Login Error!")
        global piviv_user_cookies_is_not_empty
        if input('Do you want to try to login with your own cookies?(Y/N):') == 'Y':
            cookies = input('Please enter the cookies:')
            cookies_dict = {}
            lst = cookies.split(';')
            # print(lst)
            for each_key in lst:
                name = each_key.split('=')[0]
                value = each_key.split('=')[1]
                cookies_dict[name] = value
            # print(cookies_dict)
            with open('cookies', 'w+') as f:
                f.write(json.dumps(cookies_dict))
            s.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            piviv_user_cookies_is_not_empty = True
        else:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--proxy-server=socks5://192.168.31.105:10808')
            pixiv_login_web = webdriver.Chrome(options=chrome_options)
            pixiv_login_web.get(login_url)
            pixiv_login_web.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[1]/input').send_keys(
                pixiv_user_name)
            pixiv_login_web.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[2]/input').send_keys(
                pixiv_user_pass)
            pixiv_login_web.find_element_by_xpath('//*[@id="LoginComponent"]/form/button').click()
            while pixiv_login_web.current_url == 'https://accounts.pixiv.net/login':
                time.sleep(1)
                print(time.localtime())
                print("The web page haven't redirected..")
                print('If the Google reCaptcha show up,Please finish it.')
            print('Redirected!')
            final_cookies = pixiv_login_web.get_cookies()
            for cookie in final_cookies:
                s.cookies.set(cookie['name'], cookie['value'])
            with open('cookies', 'w+') as f:
                f.write(json.dumps(requests.utils.dict_from_cookiejar(s.cookies)))

            piviv_user_cookies_is_not_empty = True


if proxy_enable:
    print('Gonna connect to your socks5 server...')
    try:
        # socks.set_default_proxy(socks.SOCKS5, proxy_host, int(proxy_port))
        # socket.socket = socks.socksocket
        # socket.timeout = 500
        proxies = {
            "http": "socks5://" + proxy_host + ":" + proxy_port,
            'https': "socks5://" + proxy_host + ":" + proxy_port
        }
        s.proxies = proxies
        #print(proxies)
    except Exception as e:
        print('When processing the socks5 server an error occurred.')
        print(e)
        exit()
    else:
        print('Proxy connection seems successfully created!!')
else:
    print('Not using the proxy..')
s.headers = params
if not piviv_user_cookies_is_not_empty:
    update_user_cookies()
else:
    pixiv_user_cookies_dict = dict(pixiv_user_cookies)
    s.cookies = requests.utils.cookiejar_from_dict(pixiv_user_cookies_dict)

#print(s.cookies)

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
    0:Daily
    1:weekly
    2:monthly
    3:rookie
    4:male
    5:female
"""

ranking_types = ['daily', 'weekly', 'monthly', 'rookie', 'male', 'female']


def format_pixiv_ranking_url(year_month, day, page, mode=1):
    ranking_type = "daily"
    if mode == 0:
        ranking_type = ranking_types[0]
    elif mode == 1:
        ranking_type = ranking_types[1]
    elif mode == 2:
        ranking_type = ranking_types[2]
    elif mode == 3:
        ranking_type = ranking_types[3]
    elif mode == 4:
        ranking_type = ranking_types[4]
    elif mode == 5:
        ranking_type = ranking_types[5]
    else:
        print("Unknown Mode")
        exit()

    ranking_url = 'https://www.pixiv.net/ranking.php?mode=' + ranking_type + '&date=' + year_month + str(
        day) + '&p=' + str(
        page) + '&format=json'
    print(ranking_url)
    return ranking_url


#
def format_pixiv_illust_url(illust_id):
    illust_url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(illust_id)
    return illust_url


#
'''
 mode:
    1.single
    2.multiple
'''


def format_pixiv_illust_original_url(id_url, mode=1):
    if mode == 1:
        contents = s.get(id_url, params=params)
        contents.raise_for_status()
        try:
            img_src_re = re.compile(r'\"urls\":{.*?}')
            img_src = img_src_re.findall(contents.text)
            final_dict = json.loads("{" + img_src[0] + "}")
            return final_dict['urls']['original']
        except:
            print("Error")
            print(contents.text)
    elif mode == 2:
        data_list = []
        json_datas = s.get(id_url, params=params)
        json_datas.raise_for_status()
        json_datas_format = json.loads(json_datas.text)['body']
        for urls in json_datas_format:
            data_list.append(urls['urls']['original'])
        # print(data_list)
        return data_list


def format_pixiv_user_profile_all_url(target_user_id):
    profile_all_url = "https://www.pixiv.net/ajax/user/" + str(target_user_id) + "/profile/all"
    return profile_all_url


def get_illust_name_from_illust_url(url):
    print(url)
    illust_url_content = s.get(url, timeout=10)
    illust_url_content.raise_for_status()
    illust_url_content.encoding = 'unicode_escape'
    img_name_re = re.compile(r'\"userIllusts\":{.*?}')
    img_info = img_name_re.findall(illust_url_content.text)[0]
    illust_title_re = re.compile(r'\"illustTitle\":\".*?\"')
    illust_title = illust_title_re.findall(img_info)[0]
    # img_info_f = "{" + img_info + "}}"
    # final_dict = json.loads(img_info_f)
    illust_title_f = '{' + illust_title + "}"
    illust_title_f_dict = json.loads(illust_title_f)
    print(illust_title_f_dict['illustTitle'])
    return illust_title


def format_multi_illust_json_url(multi_illust_id):
    multi_illust_json_url = 'https://www.pixiv.net/ajax/illust/' + str(multi_illust_id) + '/pages'
    return multi_illust_json_url


def download_file(url, path):
    print("\nThread ID:" + str(_thread.get_ident()))
    path_output = path

    with s.get(url, stream=True) as pic:
        pic.raise_for_status()
        if os.path.exists(path_output):
            print("File exists:" + path_output, "\nSkip!")
            return False
        try:
            with open(path_output, 'wb') as f:
                for chunk in pic.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except:
            return False
        else:
            print("File Saved:" + path_output)
        return True


def download_thread(url, path, exfile_name=None, exfile_dir=None):
    local_path = path
    local_filename = url.split('/')[-1]
    if exfile_dir is not None:
        local_path += global_symbol + exfile_dir + global_symbol
    if exfile_name is not None:
        local_filename = global_symbol + exfile_name + "-" + local_filename
    path_output = local_path + local_filename
    print("File Location:" + path_output)
    if not os.path.exists(local_path):
        print("Folder doesn't exists!!")
        os.makedirs(local_path)
        print("Folder Created.")
    retry_count = 0
    try:
        _thread.TIMEOUT_MAX = 10000
        _thread.start_new_thread(download_file, (url, path_output))
    except:
        print("Error..")
        if retry_count >= 3:
            print("Not wokring..")
            print("Skip!!")
        else:
            print("Starting retry..")
            retry_count += 1
    else:
        print("Download thread successfully started!")


while (True):
    print('What do you want to do?')
    print("Download the selected ranking pics(1)")
    print("Download the pics from a user(2)")
    print('Download the pics that you marked(3)')
    print('Update the user cookies(4)')
    print('Exit(5)')
    choose = input("Your choose[1-5]:")
    if choose == '1':
        mode_asked = int(input('Please choose the ranking type(0-5):'))
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
        # 共10页json
        for i in range(1, max_page + 1):
            print("Catching Page:", i)
            url = format_pixiv_ranking_url(year_month, day, i, mode_asked)
            print("URL TARGET: " + url)
            json_source_contents = s.get(url)
            json_source_contents.raise_for_status()
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
                illust_type_code = single_data['illust_type']
                illust_type = "Unknown"
                if illust_type_code == '0':
                    illust_type = 'Single'
                elif illust_type_code == '1':
                    illust_type = 'Multiple'
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
                print('Type:', illust_type)

                if illust_type_code == '0':
                    print('Single Download start!!')
                    pic_url = format_pixiv_illust_original_url(format_pixiv_illust_url(illust_id))
                    print('Picture source address:', pic_url)
                    download_thread(pic_url, save_path, title, ranking_types[mode_asked])
                elif illust_type_code == '1':
                    print('Multiple Download start!!')
                    data_listed = format_pixiv_illust_original_url(format_multi_illust_json_url(illust_id), 2)
                    for each_one in data_listed:
                        print('One of Multiple Picture source address:', each_one)
                        download_thread(each_one, save_path, title, ranking_types[mode_asked] + '/M-' + str(illust_id))

        print('Job finished!')
        print('Total cost:', time.time() - start_time)
    elif choose == '2':
        target_user_id = int(input("Please enter the target user id(like 17300903):"))
        profile_all = s.get(format_pixiv_user_profile_all_url(target_user_id))
        profile_all.raise_for_status()
        profile_all_json = json.loads(profile_all.text)
        all_illusts = profile_all_json['body']['illusts']
        illusts_ids = all_illusts.keys()
        total_ids = len(illusts_ids)
        download_count = 0
        for single_illust in illusts_ids:
            # illust_name = get_illust_name_frome_illust_url(format_pixiv_illust_url(single_illust))
            download_count += 1
            print("Downloading", str(download_count), "of", total_ids)
            download_thread(format_pixiv_illust_original_url(format_pixiv_illust_url(single_illust)),
                            save_path,get_illust_name_from_illust_url(format_pixiv_illust_url(single_illust)) , str(target_user_id))
        print('\nALL Done')
        # print(type(illusts_ids),len(illusts_ids))
    elif choose == '3':
        print('Catching your bookmark..')
        bookmark = s.get('https://www.pixiv.net/bookmark.php', timeout=10)
        bookmark.raise_for_status()
        # bookmark_data=json.loads(bookmark.text)
        soup = BeautifulSoup(bookmark.text, 'html.parser')

        book_pages = soup.find(name='ul', attrs={'class': 'page-list'})
        book_total_page = len(book_pages)

        format_book_page_url = 'https://www.pixiv.net/bookmark.php?rest=show&p='

        for single_page in range(1, book_total_page + 1):
            print('Starting bookmark download for page', str(single_page), 'of', book_total_page)
            per_page = s.get(format_book_page_url + str(single_page))
            per_soup = BeautifulSoup(per_page.text, 'html.parser')
            bookmark_datas = per_soup.find(name='ul', attrs={'class': '_image-items js-legacy-mark-unmark-list'})
            print(len(bookmark_datas))
            for marked_illust_id in bookmark_datas:
                # each_marked_illust = marked_illust_id.find(name='a', attrs={'class': 'work _work'})
                switch = marked_illust_id.a['class']
                # print(type(marked_illust_id))
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
                    print('----- ')
                    print('Title:', title)
                    print('User_id:', user_id)
                    print('User_name:', user_name)
                    print('illust_id:', illust_id)
                    print('Tag:', tag)
                    print('Type:', illust_type)
                    download_thread(format_pixiv_illust_original_url(format_pixiv_illust_url(illust_id)), save_path,
                                    title,
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
                    print('----- ')
                    print('Title:', title)
                    print('User_id:', user_id)
                    print('User_name:', user_name)
                    print('illust_id:', illust_id)
                    print('Tag:', tag)
                    print('Type:', illust_type)

                    data_listed = format_pixiv_illust_original_url(format_multi_illust_json_url(illust_id), 2)
                    for each_one in data_listed:
                        print('Start downloading multiple picture..')
                        print('Single_URL:', each_one)
                        download_thread(each_one, save_path, title, 'Bookmark/M-' + illust_id)
                    print('Total cost:', time.time() - start_time)
                    print('ALL DONE!')
        print('ALL DONE!')
    elif choose == '4':
        update_user_cookies()
    elif choose == '5':
        print('Bye!!')
        exit()
