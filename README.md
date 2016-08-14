# Logfile Notifications

[![Dependency Status](https://gemnasium.com/badges/github.com/tripplet/logfile-notifications.svg)](https://gemnasium.com/github.com/tripplet/logfile-notifications)

### Features

- Supports multiple log files
- Trigger lines in logfiles based on regex
- Service can be controlled interactively through the Telegram bot
- Disable notifications for certain time
- Administrator users can change the config through the Telegram bot

#### Supported notification services
- [Notify My Android](http://www.notifymyandroid.com/)
- [Pushover](https://pushover.net/)
- [Telegram bot](https://telegram.org/)


### Install

1. Requires python3

2. Create and use virtual environment (optional):
   `virtualenv venv; source venv/bin/activate`
   
3. Install requirements:
   `pip install -r requirements.txt`

4. Copy sample config
   `cp sample-config.yaml config.yaml`

5. Modify the config file to your needs

6. Run
   - `python notifications.py config.yaml`
   Or with virtual environment
   - `venv/bin/python notifications.py config.yaml`

### Using the docker image

1. Pull the image from dockerhub
   - `docker pull ttobias/logfile-notifications`

   - https://hub.docker.com/r/ttobias/logfile-notifications/

   
   
