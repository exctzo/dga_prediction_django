from django.test import TestCase

import warnings
warnings.filterwarnings('ignore',category=FutureWarning)

import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='3'

import shutil
import pickle
import random
from io import BytesIO
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile
import pandas as pd

import math
import numpy as np
import tensorflow as tf

from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Embedding, GRU
from sklearn.model_selection import train_test_split


class GetDataModelTest(TestCase):

    def Test_prepare_data(self):
        # Загрузка Cisco Umbrella Popularity List (legit).
        lv_resp = urlopen('http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip')
        lv_zipfile = ZipFile(BytesIO(lv_resp.read()))
        lv_zipfile.extractall("get_model/input_data/test")
        
        # Загрузка Malware Domain by John Bambenek of Bambenek Consulting (dga).
        urlretrieve('http://osint.bambenekconsulting.com/feeds/dga-feed.txt', 'get_model/input_data/test/dga.csv')

        lv_training_data = {'legit': [], 'dga': []}

        # Выделение второго уровная доменного имени.
        lv_domain_list = pd.read_csv('get_model/input_data/test/top-1m.csv', names=['domain'])
        lv_domain_list['domain'] = lv_domain_list['domain'].map(lambda x: x.split('.')[-2:]).map(lambda x: x[0])
        lv_domain_list['type'] = 0
        lv_training_data['legit'] = lv_domain_list.sample(10000)

        lv_domain_list = pd.read_csv('get_model/input_data/test/dga.csv', names=['domain', 'family', 'data'], skiprows = 14, index_col=False)
        lv_domain_list['domain'] = lv_domain_list['domain'].map(lambda x: x.split('.')[0])
        lv_domain_list['family'] = lv_domain_list['family'].fillna('Untitled').map(lambda x: x.split(' ')[3] if (x != 'Untitled') else x)
        lv_domain_list = lv_domain_list.sample(10000)
        lv_domain_list['type'] = 1
        lv_domain_list['subtype'] = pd.factorize(lv_domain_list.family)[0]
        lv_training_data['dga'] = lv_domain_list

        with open('get_model/input_data/test/training_data.pkl', 'wb') as lv_f:
            pickle.dump(lv_training_data, lv_f, pickle.HIGHEST_PROTOCOL)
        
    def Test_get_model(self):
        # Подгрузка данных о доменных именах с диска.
        with open('get_model/input_data/test/training_data.pkl', 'rb') as lv_f:
            lv_training_data = pickle.load(lv_f)

        # Общая коллекция данных.
        lv_all_data_dict = pd.concat([lv_training_data['legit'], lv_training_data['dga']], ignore_index=False, sort=True)
        lv_dga_data_dict = pd.concat([lv_training_data['dga']], ignore_index=True)
        
        # Равномерное распределение по семьям
        lv_dga_data_dict = lv_dga_data_dict.groupby('family').apply(lambda x: x.sample(100, replace=True))

        # Словарь с семьями DGA
        lv_family_dict = {idx+1:x for idx, x in enumerate(lv_training_data['dga']['family'].unique())}
        lv_classes = len(lv_family_dict)

        # Массив x хранит образцы обучения.
        # В массиве y хранятся целевые значения (метки типов) для образцов обучения.
        lv_X = np.array(lv_all_data_dict['domain'].tolist())
        lv_y = np.array(lv_all_data_dict['type'].tolist())
        lv_X_dga = np.array(lv_dga_data_dict['domain'].tolist())
        lv_y_dga = np.array(lv_dga_data_dict['subtype'].tolist())

        # Создание словаря действительных символов.
        lv_valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(lv_X)))}

        # Количество уникальных символов.
        lv_max_features = len(lv_valid_chars) + 1

        # Макс последовательность символов.
        lv_maxlen = np.max([len(x) for x in lv_X])

        # Преобразование символов в int и pad (последовательности одиннаковой длины).
        lv_X = [[lv_valid_chars[y] for y in x] for x in lv_X]
        lv_X = sequence.pad_sequences(lv_X, maxlen=lv_maxlen)
        lv_X_dga = [[lv_valid_chars[y] for y in x] for x in lv_X_dga]
        lv_X_dga = sequence.pad_sequences(lv_X_dga, maxlen=lv_maxlen)

        lv_X_train, lv_X_test, lv_y_train, lv_y_test = train_test_split(lv_X, lv_y, test_size=0.2, random_state=0)

        tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

        # Построение модели.
        lv_model = Sequential()
        lv_model.add(Embedding(lv_max_features, 128, input_length=lv_maxlen))
        lv_model.add(GRU(128))
        lv_model.add(Dropout(rate=0.5))
        lv_model.add(Dense(1))
        lv_model.add(Activation('sigmoid'))
        lv_model.compile(loss='binary_crossentropy', optimizer='rmsprop')

        # Построение модели.
        lv_model_dga = Sequential()
        lv_model_dga.add(Embedding(lv_max_features, 128, input_length=lv_maxlen))
        lv_model_dga.add(GRU(128))
        lv_model_dga.add(Dropout(rate=0.5))
        lv_model_dga.add(Dense(lv_classes))
        lv_model_dga.add(Activation('sigmoid'))
        lv_model_dga.compile(loss='sparse_categorical_crossentropy', optimizer='rmsprop')

        # Обучение модели 1.
        lv_model.fit(lv_X_train, lv_y_train, epochs=1, batch_size=128, verbose=0)

        # Сохранение модели на диск.
        lv_model.save('get_model/input_data/test/dga_prediction_model.h5')

        # Обучение модели.
        lv_model_dga.fit(lv_X_dga, lv_y_dga, epochs=1, batch_size=128, verbose=0)

        lv_seq = 'hchmemmrsivu'
        lv_X_dga_pred = [lv_valid_chars[y] for y in lv_seq]
        lv_X_dga_pred = sequence.pad_sequences([lv_X_dga_pred], maxlen=lv_maxlen)
        lv_pred_class = lv_model_dga.predict_classes(lv_X_dga_pred)
        lv_pred_proba = lv_model_dga.predict_proba(lv_X_dga_pred)
                
        # Проверка валидности классификации
        assert lv_pred_class is not None
        assert lv_pred_proba is not None

    def test_prepare_for_sniff(self):
        self.Test_prepare_data()
        self.Test_get_model()
        shutil.rmtree('get_model/input_data/test', ignore_errors=True)
