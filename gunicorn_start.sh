gunicorn -w 4 -b 0.0.0.0:2333 app:app --log-file log.txt --daemon
