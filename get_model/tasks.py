from __future__ import absolute_import, unicode_literals
from celery.decorators import task
from celery import current_task
from . import models

import warnings
warnings.filterwarnings('ignore',category=FutureWarning)

import os
import pickle
import random
import shutil
import pandas as pd
import math
import numpy as np
from io import BytesIO
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile
from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Embedding, GRU
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from tensorflow.keras.callbacks import EarlyStopping


@task(name="get_data")
def task_get_data():
    current_task.update_state(state='PROGRESS', meta={'step' : 'downloading legit...'})
    # Загрузка Cisco Umbrella Popularity List (legit).
    if os.path.isdir('get_model/input_data'):
        shutil.rmtree('get_model/input_data', ignore_errors=True)

    lv_resp = urlopen('http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip')
    lv_zipfile = ZipFile(BytesIO(lv_resp.read()))
    lv_zipfile.extractall("get_model/input_data")
    
    current_task.update_state(state='PROGRESS', meta={'step' : 'downloading dga...'})
    # Загрузка Malware Domain by John Bambenek of Bambenek Consulting (dga).
    urlretrieve('http://osint.bambenekconsulting.com/feeds/dga-feed.txt', 'get_model/input_data/dga.csv')

    lv_training_data = {'legit': [], 'dga': []}

    current_task.update_state(state='PROGRESS', meta={'step' : 'inserting domains lists...'})
    # Выделение второго уровная доменного имени.
    lv_domain_list = pd.read_csv('get_model/input_data/top-1m.csv', names=['domain'])
    lv_domain_list['domain'] = lv_domain_list['domain'].map(lambda x: x.split('.')[-2:]).map(lambda x: x[0])
    lv_domain_list['type'] = 0
    lv_training_data['legit'] = lv_domain_list.sample(100000)
    lv_legit_size = lv_training_data['legit'].size

    lv_domain_list = pd.read_csv('get_model/input_data/dga.csv', names=['domain', 'family', 'data'], skiprows = 14, index_col=False)
    lv_domain_list['domain'] = lv_domain_list['domain'].map(lambda x: x.split('.')[0])
    lv_domain_list['family'] = lv_domain_list['family'].fillna('Untitled').map(lambda x: x.split(' ')[3] if (x != 'Untitled') else x)
    lv_domain_list = lv_domain_list.sample(100000)
    lv_domain_list['type'] = 1
    lv_domain_list['subtype'] = pd.factorize(lv_domain_list.family)[0]
    lv_training_data['dga'] = lv_domain_list
    lv_dga_size = lv_training_data['dga'].size
    lv_family_size = lv_training_data['dga'].groupby('family').ngroups

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving data...'})
    with open('get_model/input_data/training_data.pkl', 'wb') as lv_f:
        pickle.dump(lv_training_data, lv_f, pickle.HIGHEST_PROTOCOL)
    
    lv_db_dataset = models.PreparedDataset(legit_size=lv_legit_size, dga_size=lv_dga_size, family_size=lv_family_size)
    lv_db_dataset.save()
    
    return {'step' : 'training data is prepared.'}


@task(name="train_model")
def task_train_model(iv_output_dim, iv_gru_units, iv_drop_rate, iv_act_func, iv_epochs, iv_batch_size):

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading training data...'})
    # Подгрузка данных о доменных именах с диска.
    with open('get_model/input_data/training_data.pkl', 'rb') as lv_f:
        lv_training_data = pickle.load(lv_f)

    lv_datasetd_id = models.PreparedDataset.objects.latest('id')

    # Общая коллекция данных.
    lv_all_data_dict = pd.concat([lv_training_data['legit'], lv_training_data['dga']], ignore_index=False, sort=True)
    lv_dga_data_dict = pd.concat([lv_training_data['dga']], ignore_index=True)
    
    # Равномерное распределение по семьям
    lv_dga_data_dict = lv_dga_data_dict.groupby('family').apply(lambda x: x.sample(5000, replace=True))

    # Словарь с семьями DGA
    lv_family_dict = {idx+1:x for idx, x in enumerate(lv_training_data['dga']['family'].unique())}
    lv_classes = len(lv_family_dict)

    # Массив x хранит образцы обучения.
    # В массиве y хранятся целевые значения (метки типов) для образцов обучения.
    lv_X = np.array(lv_all_data_dict['domain'].tolist())
    lv_y = np.array(lv_all_data_dict['type'].tolist())
    lv_X_family = np.array(lv_dga_data_dict['domain'].tolist())
    lv_y_family = np.array(lv_dga_data_dict['subtype'].tolist())

    # Создание словаря действительных символов.
    lv_valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(lv_X)))}

    # Количество уникальных символов.
    lv_max_features = len(lv_valid_chars) + 1

    # Макс последовательность символов.
    lv_maxlen = np.max([len(x) for x in lv_X])

    # Преобразование символов в int и pad (последовательности одиннаковой длины).
    lv_X = [[lv_valid_chars[y] for y in x] for x in lv_X]
    lv_X = sequence.pad_sequences(lv_X, maxlen=lv_maxlen)
    lv_X_family = [[lv_valid_chars[y] for y in x] for x in lv_X_family]
    lv_X_family = sequence.pad_sequences(lv_X_family, maxlen=lv_maxlen)

    lv_X_train, lv_X_test, lv_y_train, lv_y_test = train_test_split(lv_X, lv_y, test_size=0.2, random_state=0)
    lv_X_family_train, lv_X_family_test, lv_y_family_train, lv_y_family_test = train_test_split(lv_X_family, lv_y_family, test_size=0.2, random_state=0)

    # Построение модели.
    lv_model = Sequential()
    lv_model.add(Embedding(lv_max_features, iv_output_dim, input_length=lv_maxlen))
    lv_model.add(GRU(iv_gru_units))
    lv_model.add(Dropout(rate=iv_drop_rate))
    lv_model.add(Dense(1))
    lv_model.add(Activation(iv_act_func))
    lv_model.compile(loss='binary_crossentropy', optimizer='rmsprop')

    # Построение модели.
    lv_model_family = Sequential()
    lv_model_family.add(Embedding(lv_max_features, iv_output_dim, input_length=lv_maxlen))
    lv_model_family.add(GRU(iv_gru_units))
    lv_model_family.add(Dropout(rate=iv_drop_rate))
    lv_model_family.add(Dense(lv_classes))
    lv_model_family.add(Activation(iv_act_func))
    lv_model_family.compile(loss='sparse_categorical_crossentropy', optimizer='rmsprop')

    lv_db_model = models.PreparedModel(model_type='binary', model='GRU', id_dataset=lv_datasetd_id, max_features=lv_max_features, model_units=iv_gru_units, 
        drop_rate=iv_drop_rate, classes='2', act_func=iv_act_func, test_size='0.2', epochs=iv_epochs, batch_size=iv_batch_size)
    lv_db_model.save()

    current_task.update_state(state='PROGRESS', meta={'step' : 'training dga prediction model...'})
    lv_best_auc = 0.0
    for ep in range(iv_epochs):

        # Обучение модели.
        lv_model.fit(lv_X_train, lv_y_train, epochs=1, batch_size=iv_batch_size)

        lv_y_score = lv_model.predict_proba(lv_X_test)
        lv_y_pred = lv_y_score.round()

        lv_auc = roc_auc_score(lv_y_test, lv_y_score)
        lv_accuracy = accuracy_score(lv_y_test, lv_y_pred)
        lv_precision = precision_score(lv_y_test, lv_y_pred)
        lv_recall = recall_score(lv_y_test, lv_y_pred)
        lv_f1 = f1_score(lv_y_test, lv_y_pred)

        if lv_auc > lv_best_auc:
            lv_best_auc = lv_auc

        lv_status = 'training dga prediction model... Epoch %d (auc = %f, best = %f)' % (ep+1, lv_auc, lv_best_auc)
        current_task.update_state(state='PROGRESS', meta={'step' : lv_status})

        lv_db_model_stat = models.ModelLearningStat(id_model=lv_db_model, epoch=ep+1, auc=lv_auc, accuracy=lv_accuracy, 
            precision=lv_precision, recall=lv_recall, f1=lv_f1)
        lv_db_model_stat.save()

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving dga prediction model...'})

    if os.path.exists('get_model/input_data/dga_prediction_model.h5'):
        os.remove('get_model/input_data/dga_prediction_model.h5')

    # Сохранение модели на диск.
    lv_model.save('get_model/input_data/dga_prediction_model.h5')

    current_task.update_state(state='PROGRESS', meta={'step' : 'training family prediction model...'})

    # Обучение модели.
    lv_model_family.fit(lv_X_family_train, lv_y_family_train, epochs=iv_epochs, batch_size=iv_batch_size)

    current_task.update_state(state='PROGRESS', meta={'step' : 'counting model scores...'})
    
    lv_y_family_pred = lv_model_family.predict_classes(lv_X_family_test)

    lv_accuracy = accuracy_score(lv_y_family_test, lv_y_family_pred)
    lv_precision = precision_score(lv_y_family_test, lv_y_family_pred, average='macro')
    lv_recall = recall_score(lv_y_family_test, lv_y_family_pred, average='macro')
    lv_f1 = f1_score(lv_y_family_test, lv_y_family_pred, average='macro')

    lv_db_model = models.PreparedModel(model_type='multiclass', model='GRU', id_dataset=lv_datasetd_id, max_features=lv_max_features, model_units=iv_gru_units, 
        drop_rate=iv_drop_rate, classes=lv_classes, act_func=iv_act_func, test_size='0.2', epochs=iv_epochs, batch_size=iv_batch_size)
    lv_db_model.save()

    lv_db_model_stat = models.ModelLearningStat(id_model=lv_db_model, epoch=iv_epochs, accuracy=lv_accuracy, 
        precision=lv_precision, recall=lv_recall, f1=lv_f1)
    lv_db_model_stat.save()

    if os.path.exists('get_model/input_data/family_prediction_model.h5'):
        os.remove('get_model/input_data/family_prediction_model.h5')

    current_task.update_state(state='PROGRESS', meta={'step' : 'saving family prediction model...'})

    # Сохранение модели на диск.
    lv_model_family.save('get_model/input_data/family_prediction_model.h5')

    os.path.exists("/home/el/myfile.txt")

    return {'step' : 'models are prepared.'}
