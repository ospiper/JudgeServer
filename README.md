# JudgeServer

[Document](http://docs.onlinejudge.me/)

# Requirements
- Python 2.7
- Python 3.4+
- Docker
- Supervisor
- Rsync

# Install
1. Install Docker and Docker-compose
1. Install Supervisor (via apt, not pip)
1. Install Python (3.4+)
1. Install pika via pip3 (not pip2)
1. Install Rsync and xinetd then start rsync via xinetd [Ref](https://blog.csdn.net/foreversunshine/article/details/51670041)
1. Add your judge server's ip into ```/usr/local/sersync2.5.4/confxml.xml``` on your main server
1. Restart Sersync on your main server
1. Back to judge server. Execute ```mkdir /apoj/test_case```
1. Clone this repository to your server
1. Copy ```docker-compose.example.yml``` to ```docker-compose.yml```
1. Set your judger's token
1. Go to ```client/Python```
1. Copy ```config.example.py``` to ```config.py```
1. Set your MQ authentication, judger name and API addresses
1. Go to repository's root folder
1. Execute ```docker build -t apoj_judge_server .``` (do not forget the dot at the and of the command)
1. Wait for it
1. Execute ```docker-compose up -d```
1. Execute ```ls /apoj/test_case``` to check if the sync service works properly
