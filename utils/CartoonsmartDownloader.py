import os
import re
import json
import string
import requests
from bs4 import BeautifulSoup


class CartoonsmartDownloaderException(Exception):
    pass


class CartoonsmartDownloader(object):
    
    PRIORITY = ["hd", "sd", "mobile"]
    
    
    def __init__(self, login, password):
        self._login = login
        self._password = password
        self._logged_in = False
        
        
    def _format_filename(self, s):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c if c in valid_chars else "_" for c in s)
        return filename
    
    
    def _ensure_dir(self, dir_):
        try:
            os.stat(dir_)
        except:
            os.mkdir(dir_) 
    
    
    def _auth(self):
        print("Logging in")
        
        self._s = requests.Session()
        #self._s.proxies={
        #    "http"  : "http://127.0.0.1:8008", 
        #    "https" : "https://127.0.0.1:8008", 
        #}
        self._s.verify = False
        self._s.headers.update({
            "Host": "cartoonsmart.com",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        })
        s = self._s
        
        # this will also set cookies
        r = s.get("http://cartoonsmart.com/checkout-2/my-account/")
        
        # login...
        bs = BeautifulSoup(r.text)
        form = bs.find("form", {"id": "edd_login_form"})
        post_data = dict()
        for input_el in form.find_all("input"):
            try:
                post_data[input_el["name"]] = input_el["value"]
            except KeyError:
                pass
        
        post_data["edd_user_login"] = self._login
        post_data["edd_user_pass"] = self._password
            
        r = s.post("http://cartoonsmart.com/checkout-2/my-account/", post_data)
        if 'Log Out</a>' not in r.text:
            raise CartoonsmartDownloaderException('Failed to login')
        
        self._logged_in = True
        print('Login successful')
        
    
    def _check_auth(self):
        if not self._logged_in:
            self._auth()
        
    
    def download_list(self, url, dest):
        self._check_auth()
        print("Getting info from page: %s" % url)
        
        s = self._s
        r = s.get(url)
        bs = BeautifulSoup(r.text)
        
        title = bs.find("div", {"class": "wpcw_fe_course_title"}).text.strip()
        
        sections = dict()
        for m in bs.find_all("tr", {"class": "wpcw_fe_module "}):
            tds = m.find_all("td")
            key = "%s - %s" % (tds[0].text.strip(), tds[1].text.strip())
            sections[key] = []
            for l in bs.find_all("tr", {"class": m["id"]}):
                tds = l.find_all('td')
                sections[key].append({
                    'name': "%s - %s" %
                        (tds[0].text.strip(), tds[1].text.strip()),
                    'url': tds[1].find("a")["href"]
                })
                
        if len(sections) == 0:
            raise CartoonsmartDownloaderException(
                'Failed to find list of sections')
        
        
        dest = os.path.join(dest, self._format_filename(title))
        self._ensure_dir(dest)
    
        for section_name in sorted(sections.keys()):
            print("Current section: %s" % section_name)
            cur_dest = os.path.join(dest, self._format_filename(section_name))
            self._ensure_dir(cur_dest)
            
            for video in sections[section_name]:
                print("Current video: %s" % video["name"])
                cur_dest_2 = os.path.join(cur_dest,
                    self._format_filename(video["name"]))
                try:
                    self.download_video_page(video["url"], cur_dest_2)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    raise
                    print("DOWNLOAD FAIL: %s" % str(e))
        
    
    def download_video_page(self, url, dest, get_title=False):
        self._check_auth()
        print("Downloading video page: %s" % url)
        
        s = self._s
        r = s.get(url)
        bs = BeautifulSoup(r.text)
        
        a = bs.find("a", {"class": "fw-video-link", "data-video": True})
        
        if a is None:
            print("Downloading archive...")
            return self._download_materials(bs, dest)
        
        if get_title:
            title = bs.find("h1", {"class": "entry-title"}).text.strip()
            print("Video title: %s" % title)
            dest = os.path.join(dest, title) 
        
        #getting video links
        print("Getting video links")
        r = s.get(a["data-video"], headers={
                "Host": "player.vimeo.com",
                "Referer": url,
            })
        m = re.search(r"var a=({\"[\s\S]*?);if\(", r.text)
        
        j = json.loads(m.group(1))
        files = j["request"]["files"]["h264"]
        
        url = None
        for quality in self.PRIORITY:
            if quality in files:
                url = files[quality]["url"]
                break
        
        if url is None:
            raise CartoonsmartDownloaderException(
                'Failed to find video url')
        
        print("Downloading video: %s" % url)
        _, ext = os.path.splitext(url)
        if "?" in ext:
            ext = ext[:ext.index("?")]
        
        dest = dest + ext
        if os.path.exists(dest):
            print("File exists: %s" % dest)
            print("Skipping")
            return
        
        r = requests.get(url, stream=True)
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*256): 
                if chunk:
                    f.write(chunk)
                    f.flush()
                    
                    
    def _download_materials(self, bs, dest):
        self._ensure_dir(dest)
        
        links = bs.find_all("a", {"class": "sf-button"})
        print("Downloading archives INSTEAD OF video")
        
        for link in links:
            url = link["href"] 
            dir_, ext = os.path.splitext(url)
            if "?" in ext:
                ext = ext[:ext.index("?")]
            
            cur_dest = os.path.join(dest, os.path.basename(dir_) + ext)
            
            if os.path.exists(cur_dest):
                print("File exists: %s" % cur_dest)
                print("Skipping")
                continue
                
            r = requests.get(url, stream=True)
            with open(cur_dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk:
                        f.write(chunk)
                        f.flush()
    
    
    
    
    
    