gunicorn -w 4 -b 0.0.0.0:2333 app:app --log-file log.txt --access-logfile access.log --log-level debug --daemon --preload --timeout 0
#!/bin/bash
PORT=2333

# 查找占用端口的进程
PID=$(lsof -t -i :$PORT)

if [ -n "$PID" ]; then
    echo "Killing process with PID $PID"
    kill -9 $PID
else
    echo "No process found on port $PORT"
fi
uwsgi --ini uwsgi.ini
uwsgi --stop /tmp/arxiv_connect-master.pid
uwsgi --reload /tmp/arxiv_connect-master.pid