# Compatibility
from __future__ import absolute_import

# Python
from argparse import ArgumentParser
import logging
import os
from downloaders import CartoonSmartDownloader

# Local
import settings

logging.basicConfig(level=logging.WARNING, 
    filename='logs/{0}.log'.format(__file__), filemode='w')

logger = logging.getLogger(__name__)

def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('-l', nargs='?', default=settings.DEFAULT_LOGIN, 
        help='Login username')
    arg_parser.add_argument('-p', nargs='?', default=settings.DEFAULT_PASSWORD, 
        help='Password')
    arg_parser.add_argument('-o', nargs='?', default=os.getcwd(), 
        help='Output filepath')
    arg_parser.add_argument('--async', action='store_true', default=False, 
        help='Asynchronous downloads')

    group = arg_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-list', help='List URL')
    group.add_argument('-video', help='Video URL')

    return arg_parser.parse_args()

def main():
    args = parse_args()

    login, password, out_path, async = args.l, args.p, args.o, args.async
    list_, video = args.list, args.video

    msg = 'login    {0}\npassword {1}\nout_path {2}'.format(login, password, 
        out_path)
    logger.info(msg)
    msg = 'list     {0}\nvideo    {1}'.format(list_, video)
    logger.info(msg)

    cdl = CartoonSmartDownloader(login, password, async)
    if list_:
        cdl.download_list(list_, out_path)
    else:
        cdl.download_video_page(video, out_path, get_title=True)

if __name__ == '__main__':
    main()
