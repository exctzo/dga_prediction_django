### Configure DO VPS

- Setup SSH (change default port to 9999, generate ssh key)
```
$ nano /etc/ssh/sshd_config
$ service ssh restart
$ ssh-keygen
```

- Firewall
```
$ ufw allow 9999,9981,9980,53
$ ufw enable
```
- Add public ssh key to Github setting page
- ...

### Installing

#### Get Python, Redis as celery "Broker" and additional packages 
```
$ apt install python3 python3-dev python3-distutils python3-pip redis-server
$ git clone https://github.com/exctzo/dga_prediction_django.git
$ pip3 install -r requirements.txt
```

#### Running celery as a daemon

#### Download generic celeryd init-script
```
$ wget -P /etc/init.d/ https://raw.githubusercontent.com/celery/celery/master/extra/generic-init.d/celeryd
$ chmod 755 /etc/init.d/celeryd
$ chown root:root /etc/init.d/celeryd
```

##### Setting configuration files (Options and template for celery can be found in the [docs](http://docs.celeryproject.org/en/3.1/tutorials/daemonizing.html))
```
$ cp celeryd /etc/default/celeryd
$ cp redis.conf /etc/redis
```

##### Create user for celery
```
$ useradd -ou 0 -g 0 celery
$ passwd celery
```
#### Usage daemon
```
$ /etc/init.d/celeryd {start|stop|restart|status}
```
##### *or run as not a daemon
```
$ celery -A dga_prediction_django worker -l info
```
#### Logs
```
$ cat /var/log/celery/worker1.log
```

### Running django app
#### Make db migrations
```
$ python3 manage.py makemigrations home get_model sniff
$ python3 manage.py migrate
```
#### Create root user for app
```
$ python3 manage.py createsuperuser
```
#### Run server
```
$ python3 manage.py runserver exctzo.tech:9980
```

#### Testing from local machine
```
$ dig @exctzo.tech -p 9981 ajdhgalksfnwkenglk.com
```
