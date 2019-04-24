## Installing

### Running celery as a daemon

##### Download generic celeryd init-script
```
$ sudo wget -P /etc/init.d/ https://github.com/celery/celery/blob/master/extra/generic-init.d/celeryd
$ sudo chmod 755 /etc/init.d/celeryd
$ sudo chown root:root /etc/init.d/celeryd
```

##### Setting configuration file (Options and template can be found in the [docs](http://docs.celeryproject.org/en/3.1/tutorials/daemonizing.html)
```
$ sudo cp celeryd /etc/default/celeryd
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
#### Logs
```
sudo nano /var/log/celery/worker1.log
```

### Running django app

#### Create root user for app
```
$ python manage.py create superuser
```
#### Run server
```
$ python manage.py makemigrations home get_model sniff
$ python manage.py migrate
$ python manage.py runserver
```