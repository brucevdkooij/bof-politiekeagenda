import os

import locale
locale.setlocale(locale.LC_ALL, "nl_NL.utf8")

root_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)))
cache_directory = os.path.join(root_directory, "../data/cache/")

bypass_cache = False
