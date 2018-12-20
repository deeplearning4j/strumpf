from .core import *
import os

def get_url(file_name):
    strumpf = Strumpf()
    cache = strumpf.get_cache_dir()
    cache_file = os.path.join(cache, file_name)
    if not os.path.exists(cache_file):
        strumpf.download_blob(file_name, cache)
    print(cache_file)
    return cache_file
