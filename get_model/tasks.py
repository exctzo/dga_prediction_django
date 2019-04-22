from __future__ import absolute_import, unicode_literals
from celery.decorators import task
from celery import current_task

import os
import pickle
from io import BytesIO
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile
import pandas as pd

import math
import numpy as np

from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Embedding, LSTM
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping



@task(name="get_data")
def task_get_data():

    current_task.update_state(state='PROGRESS', meta={'step' : 'downloading legit...'})
    # Загрузка Cisco Umbrella Popularity List (legit).
    resp = urlopen('http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip')
    zipfile = ZipFile(BytesIO(resp.read()))
    zipfile.extractall("get_model/input_data")
    
    current_task.update_state(state='PROGRESS', meta={'step' : 'downloading dga...'})
    # Загрузка Malware Domain by John Bambenek of Bambenek Consulting (dga).
    urlretrieve('http://osint.bambenekconsulting.com/feeds/dga-feed.txt', 'get_model/input_data/dga.csv')

    training_data = {'legit': [], 'dga': []}

    current_task.update_state(state='PROGRESS', meta={'step' : 'inserting domains lists...'})
    # Выделение второго уровная доменного имени.
    domain_list = pd.read_csv('get_model/input_data/top-1m.csv', names=['domain'])
    domain_list['domain'] = domain_list['domain'].map(lambda x: x.split('.')[-2:]).map(lambda x: x[0])
    domain_list['type'] = 0
    training_data['legit'] = domain_list

    domain_list = pd.read_csv('get_model/input_data/dga.csv', names=['domain', 'family', 'data'], skiprows = 14, index_col=False)
    domain_list['domain'] = domain_list['domain'].map(lambda x: x.split('.')[0])
    domain_list['family'] = domain_list['family'].map(lambda x: x.split(' ')[3])
    domain_list['type'] = 1
    training_data['dga'] = domain_list

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving data...'})
    with open('get_model/input_data/training_data.pkl', 'wb') as f:
        pickle.dump(training_data, f, pickle.HIGHEST_PROTOCOL)
    
    return {'step' : 'training data is prepared.'}


@task(name="train_model")
def task_train_model(output_dim, lstm_units, drop_rate, act_func, epochs, batch_size):

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading training data...'})
    # Подгрузка данных о доменных именах с диска.
    with open('get_model/input_data/training_data.pkl', 'rb') as f:
        training_data = pickle.load(f)

    # Общая коллекция данных.
    all_data_dict = pd.concat([training_data['legit'], training_data['dga']], ignore_index=False, sort=True)

    # Массив x хранит образцы обучения.
    # В массиве y хранятся целевые значения (метки типов) для образцов обучения.
    X = np.array(all_data_dict['domain'].tolist())
    y = np.array(all_data_dict['type'].tolist())

    # Создание словаря действительных символов.
    valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(X)))}

    # Количество уникальных символов.
    max_features = len(valid_chars) + 1

    # Макс последовательность символов.
    maxlen = np.max([len(x) for x in X])

    # Преобразование символов в int и pad (последовательности одиннаковой длины).
    X = [[valid_chars[y] for y in x] for x in X]
    X = sequence.pad_sequences(X, maxlen=maxlen)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.99, random_state=0)

    # Построение модели.
    model = Sequential()
    model.add(Embedding(max_features, output_dim, input_length=maxlen))
    model.add(LSTM(lstm_units))
    model.add(Dropout(rate=drop_rate))
    model.add(Dense(1))
    model.add(Activation(act_func))
    model.compile(loss='binary_crossentropy', optimizer='rmsprop')
    model.summary()

    current_task.update_state(state='PROGRESS', meta={'step' : 'training model...'})
    # Обучение модели.
    model.fit(X_train, y_train, epochs=epochs, batch_size=1024)

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving model...'})
    # Сохранение модели на диск.
    model.save('get_model/input_data/model.h5')

    return {'step' : 'model is prepared.'}