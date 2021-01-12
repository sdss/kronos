# encoding: utf-8
#
# conftest.py

import os

prod_dir = os.path.abspath(__file__).split("/tests")[0]

os.environ["QUART_APP"] = prod_dir + "/python/kronos/app:app"
