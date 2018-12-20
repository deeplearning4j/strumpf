from .core import *
import os


def get_file(file_name):
    strumpf = Strumpf()
    cache = strumpf.get_cache_dir()
    cache_file = os.path.join(cache, file_name)
    # Check for file in cache
    if not os.path.exists(cache_file):
        # download latest version from azure to cache, check hashes, unzip, clean up
        strumpf.download_blob(file_name, cache)
    return cache_file
