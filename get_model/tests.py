from django.test import TestCase


import warnings
warnings.filterwarnings('ignore',category=FutureWarning)

import shutil
import os
import pickle
import random
from io import BytesIO
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile
import pandas as pd

import math
import numpy as np

from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Embedding, GRU
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from tensorflow.keras.callbacks import EarlyStopping


class GetModelTest(TestCase):
    def setUp(self):
        shutil.rmtree('get_model/input_data/test', ignore_errors=True)

    def test_prepare_data(self):
        # Загрузка Cisco Umbrella Popularity List (legit).
        resp = urlopen('http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip')
        zipfile = ZipFile(BytesIO(resp.read()))
        zipfile.extractall("get_model/input_data/test")
        
        # Загрузка Malware Domain by John Bambenek of Bambenek Consulting (dga).
        urlretrieve('http://osint.bambenekconsulting.com/feeds/dga-feed.txt', 'get_model/input_data/dga.csv')

        training_data = {'legit': [], 'dga': []}

        # Выделение второго уровная доменного имени.
        domain_list = pd.read_csv('get_model/input_data/test/top-1m.csv', names=['domain'])
        domain_list['domain'] = domain_list['domain'].map(lambda x: x.split('.')[-2:]).map(lambda x: x[0])
        domain_list['type'] = 0
        training_data['legit'] = domain_list.sample(1000)

        domain_list = pd.read_csv('get_model/input_data/test/dga.csv', names=['domain', 'family', 'data'], skiprows = 14, index_col=False)
        domain_list['domain'] = domain_list['domain'].map(lambda x: x.split('.')[0])
        domain_list['family'] = domain_list['family'].fillna('Untitled').map(lambda x: x.split(' ')[3] if (x != 'Untitled') else x)
        domain_list = domain_list.sample(1000)
        domain_list['type'] = 1
        domain_list['subtype'] = pd.factorize(domain_list.family)[0]
        training_data['dga'] = domain_list

        with open('get_model/input_data/test/training_data.pkl', 'wb') as f:
            pickle.dump(training_data, f, pickle.HIGHEST_PROTOCOL)