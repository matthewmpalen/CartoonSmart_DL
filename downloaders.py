# Python
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import re
import json
import string
import sys

# External
from bs4 import BeautifulSoup
import requests

# Local
import exceptions
from utils import convert_byte_size

logging.basicConfig(level=logging.INFO, 
    filename='logs/cartoonsmart_dl.py.log', filemode='w')
logger = logging.getLogger(__name__)

class Downloader(object):
    def __init__(self, async=False):
        self._is_async = async

    def _create_directory(self, dir_name):
        if not dir_name:
            raise TypeError('Must provide a directory name')

        try:
            os.makedirs(dir_name)
        except OSError:
            if not os.path.isdir(dir_name):
                raise

    def _format_filename(self, s):
        if not s:
            raise TypeError('Must provide a filename')

        valid_chars = '-_.() {0}{1}'.format(string.ascii_letters, string.digits)
        filename = ''.join(c if c in valid_chars else '_' for c in s)
        return filename

    def _save_file(self, dest, response):
        content_length = int(response.headers['content-length'])
        msg = '[?] {0} length = {1}'.format(dest, 
            convert_byte_size(content_length))
        print(msg)
        logger.info(msg)

        with open(dest, 'wb') as f:
            dl = 0
            for chunk in response.iter_content(chunk_size=1024*256):
                if chunk:
                    dl += len(chunk)
                    done = int(50 * dl / content_length)
                    f.write(chunk)
                    f.flush()
                    if not self._is_async:
                        self.print_progress_bar(done, dl, content_length)
        print()
        msg = '\n[+] Finished downloading {0}'.format(dest)
        logging.info(msg)
        print(msg)

    def print_progress_bar(self, done, dl, content_length):
        if not done:
            return
        if not dl:
            return
        if not content_length:
            return

        msg = '\r[{0}{1}] {2:.3%}'.format('=' * done, 
            ' ' * (50 - done), float(dl)/content_length)
        sys.stdout.write(msg)
        sys.stdout.flush()

class CartoonSmartDownloader(Downloader):
    AUTH_URL = 'http://cartoonsmart.com/checkout-2/my-account/'
    VIDEO_REGEX = r'\"url\":"https://pdlvimeocdn-a.akamaihd.net/\d+/\d+/\d+\.mp4\?token2=\d+_\w+&aksessionid=\w+\"'
 
    def __init__(self, login, password, async):
        super(CartoonSmartDownloader, self).__init__(async)
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._session = None
        self._is_logged_in = False
        self._authenticate(login, password)
   
    def _authenticate(self, login, password):
        msg = '[?] Logging in'
        print(msg)
        logger.info(msg)

        self._session = requests.Session()
        self._session.verify = False
        self._session.headers.update({
            'Host': 'cartoonsmart.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0', 
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        session = self._session
        
        # This will also set cookies
        response = session.get(CartoonSmartDownloader.AUTH_URL)
        
        # Login...
        bs = BeautifulSoup(response.text)
        form_attrs = {'id': 'edd_login_form'}
        form = bs.find('form', form_attrs)

        post_data = {}
        for input_elem in form.find_all('input'):
            try:
                post_data[input_elem['name']] = input_elem['value']
            except KeyError:
                pass
        
        post_data['edd_user_login'] = login
        post_data['edd_user_pass'] = password
            
        response = session.post(CartoonSmartDownloader.AUTH_URL, post_data)
        if 'Log Out</a>' not in response.text:
            msg = 'Failed to login'
            logger.exception(msg)
            raise exceptions.CartoonSmartAuthError(msg)
        
        self._is_logged_in = True
        msg = '[+] Login successful'
        print(msg)
        logger.info(msg)
    
    def download_list(self, url, dest):
        msg = '[?] Getting info from page: {0}'.format(url)
        print(msg)
        logger.info(msg)
        
        session = self._session
        response = session.get(url)
        bs = BeautifulSoup(response.text)
        
        div_attrs = {'class': 'wpcw_fe_course_title'}
        title = bs.find('div', div_attrs).text.strip()
        
        sections = {}
        for m in bs.find_all('tr', {'class': 'wpcw_fe_module '}):
            tds = m.find_all('td')
            key = '{0} - {1}'.format(tds[0].text.strip(), tds[1].text.strip())

            sections[key] = []
            for l in bs.find_all('tr', {'class': m['id']}):
                tds = l.find_all('td')
                item = {
                    'name': '{0} - {1}'.format(tds[0].text.strip(), 
                        tds[1].text.strip()), 
                    'url': tds[1].find('a')['href']
                }
                sections[key].append(item)
                
        if not sections:
            msg = 'Failed to find list of sections'
            logger.exception(msg)
            raise exceptions.CartoonSmartDownloadError(msg)
        
        dest = os.path.join(dest, self._format_filename(title))
        self._create_directory(dest)
    
        for section_name in sorted(sections.keys()):
            msg = '[?] Current section: {0}'.format(section_name)
            print(msg)
            logger.info(msg)

            cur_dest = os.path.join(dest, self._format_filename(section_name))
            self._create_directory(cur_dest)
            
            for video in sections[section_name]:
                msg = '[?] Current video: {0}'.format(video['name'])
                print(msg)
                logger.info(msg)

                cur_dest_2 = os.path.join(cur_dest,
                    self._format_filename(video['name']))

                if self._is_async:
                    # Asynchronous
                    self._executor.submit(self.download_video_page, 
                        video['url'], cur_dest_2)
                else:
                    try:
                        # Synchronous
                        self.download_video_page(video['url'], cur_dest_2)
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        raise
                        msg = '[-] DOWNLOAD FAIL: {0}'.format(e)
                        print(msg)
                        logger.exception(msg)
    
    def download_video_page(self, url, dest, get_title=False):
        msg = '[?] Downloading video page: {0}'.format(url)
        print(msg)
        logger.info(msg)
        
        session = self._session
        response = session.get(url)
        bs = BeautifulSoup(response.text)
        
        link_attrs = {'class': 'fw-video-link', 'data-video': True}
        link = bs.find('a', link_attrs)
        
        if link is None:
            msg = '[?] Downloading archive'
            print(msg)
            logger.info(msg)
            return self._download_archive(bs, dest)
        
        if get_title:
            title_attrs = {'class': 'entry-title'}
            title = bs.find('h1', title_attrs).text.strip()
            msg = '[?] Video title: {0}'.format(title)
            print(msg)
            logger.info(msg)
            dest = os.path.join(dest, title) 
        
        # Getting video links
        msg = '[?] Getting video links: {0}'.format(link['data-video'])
        print(msg)
        logger.info(msg)

        headers = {'Host': 'player.vimeo.com', 'Referer': url}
        response = session.get(link['data-video'], headers=headers)

        matches = re.findall(CartoonSmartDownloader.VIDEO_REGEX, response.text)

        if not matches:
            msg = '[-] Failed to find video URL!'
            logger.error(msg)
            raise exceptions.CartoonSmartDownloadError(msg)
        
        # Only pick the last/largest in matches
        url = matches[-1].split('"url":')[1].replace('"', '')
        msg = '[?] Downloading video: {0}'.format(url)
        print(msg)
        logger.info(msg)

        _, ext = os.path.splitext(url)
        if '?' in ext:
            ext = ext[:ext.index('?')]
        
        dest = dest + ext
        if os.path.exists(dest):
            msg = '[-] File exists: {0}'.format(dest)
            print(msg)
            logger.info(msg)
            print('[-] Skipping')
            return
        
        response = requests.get(url, stream=True)
        self._save_file(dest, response)

    def _download_archive(self, bs, dest):
        self._create_directory(dest)
        
        links_attrs = {'class': 'sf-button'}
        links = bs.find_all('a', links_attrs)
        msg = '[?] Downloading archives INSTEAD OF video'
        print(msg)
        logger.info(msg)
        
        for link in links:
            url = link['href'] 
            dir_name, ext = os.path.splitext(url)
            if '?' in ext:
                ext = ext[:ext.index('?')]
            
            cur_dest = os.path.join(dest, os.path.basename(dir_name) + ext)
            
            if os.path.exists(cur_dest):
                msg = '[-] File exists: {0}'.format(cur_dest)
                print(msg)
                logger.info(msg)
                print('[-] Skipping')
                continue
                
            response = requests.get(url, stream=True)
            self._save_file(cur_dest, response)
