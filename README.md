## Installing

### Some prep staff
```
$ sudo apt install python3
$ sudo apt install python3-dev
$ sudo apt install python3-distutils
$ git clone https://github.com/exctzo/dga_prediction_django.git
$ pip install -r requirements.txt
```

### Installing Redis as a Celery “Broker”
```
$ sudo apt install redis-server
```

#### Running celery as a daemon

#### Download generic celeryd init-script
```
$ sudo wget -P /etc/init.d/ https://raw.githubusercontent.com/celery/celery/master/extra/generic-init.d/celeryd
$ sudo chmod 755 /etc/init.d/celeryd
$ sudo chown root:root /etc/init.d/celeryd
```

##### Setting configuration file (Options and template can be found in the [docs](http://docs.celeryproject.org/en/3.1/tutorials/daemonizing.html))
```
$ sudo cp celeryd /etc/default/celeryd
$ sudo cp redis.conf /etc/redis
```

##### Create user for celery
```
$ sudo useradd -ou 0 -g 0 celery
$ sudo passwd celery
```
#### Usage daemon
```
sudo /etc/init.d/celeryd {start|stop|restart|status}
```
##### *or run as not a daemon
```
celery -A dga_prediction_django worker -l info
```
#### Logs
```
sudo nano /var/log/celery/worker1.log
```

### Running django app
#### Make db migrations
```
$ python manage.py makemigrations home get_model sniff
$ python manage.py migrate
```
#### Create root user for app
```
$ python manage.py createsuperuser
```
#### Run server
```
$ python manage.py runserver exctzo.tech:9980
```

#### Testing
```
dig @exctzo.tech -p 9981 ajdhgalksfnwkenglk.com
```
