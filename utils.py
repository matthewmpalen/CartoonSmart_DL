import math

def convert_byte_size(size):
    if size < 0:
        raise ValueError('Size must be greater than or equal to 0')

    if size == 0:
        return '0B'

    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size, 1000)))
    p = math.pow(1000, i)

    return '{0:.1f}{1}'.format(float(size)/p, size_name[i])
