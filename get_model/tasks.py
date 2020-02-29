from __future__ import absolute_import, unicode_literals
from celery.decorators import task
from celery import current_task

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
    training_data['legit'] = domain_list.sample(100000)

    domain_list = pd.read_csv('get_model/input_data/dga.csv', names=['domain', 'family', 'data'], skiprows = 14, index_col=False)
    domain_list['domain'] = domain_list['domain'].map(lambda x: x.split('.')[0])
    domain_list['family'] = domain_list['family'].fillna('Untitled').map(lambda x: x.split(' ')[3] if (x != 'Untitled') else x)
    domain_list['type'] = 1
    domain_list['subtype'] = pd.factorize(domain_list.family)[0]
    training_data['dga'] = domain_list.sample(100000)

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving data...'})
    with open('get_model/input_data/training_data.pkl', 'wb') as f:
        pickle.dump(training_data, f, pickle.HIGHEST_PROTOCOL)
    
    return {'step' : 'training data is prepared.'}


@task(name="train_model")
def task_train_model(output_dim, gru_units, drop_rate, act_func, epochs, batch_size):

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading training data...'})
    # Подгрузка данных о доменных именах с диска.
    with open('get_model/input_data/training_data.pkl', 'rb') as f:
        training_data = pickle.load(f)

    # Общая коллекция данных.
    all_data_dict = pd.concat([training_data['legit'], training_data['dga']], ignore_index=False, sort=True)
    dga_data_dict = pd.concat([training_data['dga']], ignore_index=True)
    
    # Равномерное распределение по семьям
    dga_data_dict = dga_data_dict.groupby('family').apply(lambda x: x.sample(5000, replace=True))

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
    X_dga_train, X_dga_test, y_dga_train, y_dga_test = train_test_split(X_dga, y_dga, test_size=0.2, random_state=0)

    # Построение модели.
    model = Sequential()
    model.add(Embedding(max_features, output_dim, input_length=maxlen))
    model.add(GRU(gru_units))
    model.add(Dropout(rate=drop_rate))
    model.add(Dense(1))
    model.add(Activation(act_func))
    model.compile(loss='binary_crossentropy', optimizer='rmsprop')

    # Построение модели.
    model_dga = Sequential()
    model_dga.add(Embedding(max_features, output_dim, input_length=maxlen))
    model_dga.add(GRU(gru_units))
    model_dga.add(Dropout(rate=drop_rate))
    model_dga.add(Dense(classes))
    model_dga.add(Activation(act_func))
    model_dga.compile(loss='sparse_categorical_crossentropy', optimizer='rmsprop')

    current_task.update_state(state='PROGRESS', meta={'step' : 'training dga prediction model...'})
    best_auc = 0.0
    for ep in range(epochs):

        # Обучение модели.
        model.fit(X_train, y_train, epochs=1, batch_size=batch_size)

        y_score = model.predict_proba(X_test)
        auc = roc_auc_score(y_test, y_score)

        if auc > best_auc:
            best_auc = auc

        status = 'training dga prediction model... Epoch %d (auc = %f, best = %f)' % (ep+1, auc, best_auc)
        current_task.update_state(state='PROGRESS', meta={'step' : status})

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving dga prediction model...'})

    # Сохранение модели на диск.
    model.save('get_model/input_data/dga_prediction_model.h5')

    current_task.update_state(state='PROGRESS', meta={'step' : 'training family prediction model...'})

    # Обучение модели.
    model_dga.fit(X_dga_train, y_dga_train, epochs=epochs, batch_size=batch_size)

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving family prediction model...'})

    # Сохранение модели на диск.
    model_dga.save('get_model/input_data/family_prediction_model.h5')

    return {'step' : 'models are prepared.'}
