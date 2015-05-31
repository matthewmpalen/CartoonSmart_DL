import os
import sys
import settings
from utils.CartoonsmartDownloader import CartoonsmartDownloader     


args = sys.argv[1:]

if (not args or (len(sys.argv) == 2 and sys.argv[1] in ['-help', '--h'])):
    print("""
Usage:
    python %s [-l login] [-p password] [-o output_dir] (-list url | -video url)
    
List url or video url must be provided. If login/password not given, info
from settings.py will be used. If output_dir is not given, current
working directory will be used.

Example usage:
    python %s -list http://cartoonsmart.com/maze-game-with-swift-and-sprite-kit-subscriber-access/
""" % (sys.argv[0], sys.argv[0]))
    sys.exit()


out_path = os.getcwd()
login = settings.DEFAULT_LOGIN
password = settings.DEFAULT_PASSWORD


arg_name = None
is_arg_name = True
list_ = None
video = None
for arg in sys.argv[1:]:
    if is_arg_name:
        if arg not in ['-l', '-p', '-o', '-list', '-video']:
            print('Unknown argument: %s' % arg)
            sys.exit(1)
        is_arg_name = False
        arg_name = arg
    else:
        if arg_name == '-l':
            login = arg
        elif arg_name == '-p':
            password = arg
        elif arg_name == '-o':
            out_path = arg
        elif arg_name == '-list':
            list_ = arg
        elif arg_name == '-video':
            video = arg
            
        is_arg_name = True

if list_ and video:
    print("List and video cannot be set at the same time")
    sys.exit(1)
if not list_ and not video:
    print("Not enough arguments")
    sys.exit(1)

cdl = CartoonsmartDownloader(login, password)
if list_:
    cdl.download_list(list_, out_path)
else:
    cdl.download_video_page(video, out_path, get_title=True)
    

