from django.test import TestCase


import warnings
warnings.filterwarnings('ignore')

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


class GetDataModelTest(TestCase):

    def test_prepare_data(self):
        # Загрузка Cisco Umbrella Popularity List (legit).
        resp = urlopen('http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip')
        zipfile = ZipFile(BytesIO(resp.read()))
        zipfile.extractall("get_model/input_data/test")
        
        # Загрузка Malware Domain by John Bambenek of Bambenek Consulting (dga).
        urlretrieve('http://osint.bambenekconsulting.com/feeds/dga-feed.txt', 'get_model/input_data/test/dga.csv')

        training_data = {'legit': [], 'dga': []}

        # Выделение второго уровная доменного имени.
        domain_list = pd.read_csv('get_model/input_data/test/top-1m.csv', names=['domain'])
        domain_list['domain'] = domain_list['domain'].map(lambda x: x.split('.')[-2:]).map(lambda x: x[0])
        domain_list['type'] = 0
        training_data['legit'] = domain_list.sample(10000)

        domain_list = pd.read_csv('get_model/input_data/test/dga.csv', names=['domain', 'family', 'data'], skiprows = 14, index_col=False)
        domain_list['domain'] = domain_list['domain'].map(lambda x: x.split('.')[0])
        domain_list['family'] = domain_list['family'].fillna('Untitled').map(lambda x: x.split(' ')[3] if (x != 'Untitled') else x)
        domain_list = domain_list.sample(10000)
        domain_list['type'] = 1
        domain_list['subtype'] = pd.factorize(domain_list.family)[0]
        training_data['dga'] = domain_list

        with open('get_model/input_data/test/training_data.pkl', 'wb') as f:
            pickle.dump(training_data, f, pickle.HIGHEST_PROTOCOL)
        
    def test_get_model(self):
        # Подгрузка данных о доменных именах с диска.
        with open('get_model/input_data/test/training_data.pkl', 'rb') as f:
            training_data = pickle.load(f)

        # Общая коллекция данных.
        all_data_dict = pd.concat([training_data['legit'], training_data['dga']], ignore_index=False, sort=True)
        dga_data_dict = pd.concat([training_data['dga']], ignore_index=True)
        
        # Равномерное распределение по семьям
        dga_data_dict = dga_data_dict.groupby('family').apply(lambda x: x.sample(100, replace=True))

        # Словарь с семьями DGA
        family_dict = {idx+1:x for idx, x in enumerate(training_data['dga']['family'].unique())}
        classes = len(family_dict)

        # Массив x хранит образцы обучения.
        # В массиве y хранятся целевые значения (метки типов) для образцов обучения.
        X = np.array(all_data_dict['domain'].tolist())
        y = np.array(all_data_dict['type'].tolist())
        X_dga = np.array(dga_data_dict['domain'].tolist())
        y_dga = np.array(dga_data_dict['subtype'].tolist())

        # Создание словаря действительных символов.
        valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(X)))}

        # Количество уникальных символов.
        max_features = len(valid_chars) + 1

        # Макс последовательность символов.
        maxlen = np.max([len(x) for x in X])

        # Преобразование символов в int и pad (последовательности одиннаковой длины).
        X = [[valid_chars[y] for y in x] for x in X]
        X = sequence.pad_sequences(X, maxlen=maxlen)
        X_dga = [[valid_chars[y] for y in x] for x in X_dga]
        X_dga = sequence.pad_sequences(X_dga, maxlen=maxlen)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

        # Построение модели.
        model = Sequential()
        model.add(Embedding(max_features, 128, input_length=maxlen))
        model.add(GRU(128))
        model.add(Dropout(rate=0.5))
        model.add(Dense(1))
        model.add(Activation('sigmoid'))
        model.compile(loss='binary_crossentropy', optimizer='rmsprop')

        # Построение модели.
        model_dga = Sequential()
        model_dga.add(Embedding(max_features, 128, input_length=maxlen))
        model_dga.add(GRU(128))
        model_dga.add(Dropout(rate=0.5))
        model_dga.add(Dense(classes))
        model_dga.add(Activation('sigmoid'))
        model_dga.compile(loss='sparse_categorical_crossentropy', optimizer='rmsprop')

        # Обучение модели 1.
        model.fit(X_train, y_train, epochs=1, batch_size=128)

        # Сохранение модели на диск.
        model.save('get_model/input_data/test/dga_prediction_model.h5')

        # Обучение модели.
        model_dga.fit(X_dga, y_dga, epochs=1, batch_size=128)

        # Сохранение модели на диск.
        model_dga.save('get_model/input_data/test/family_prediction_model.h5')

    def delete_test_data():
        shutil.rmtree('get_model/input_data/test', ignore_errors=True)