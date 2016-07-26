# Logfile Notifications

### Requirements
- python3

### Install

1. Create and use virtual environment (optional):
   `virtualenv venv; source venv/bin/activate`
   
2. Install requirements:
   `pip install -r requirements.txt`

3. Copy config file
   `cp sample-config.yaml config.yaml`

4. Run
   - `python notifications.py config.yaml`
   Or with virtual environment
   - `venv/bin/python notifications.py config.yaml`

### Using the docker image
   `docker pull ttobias/logfile-notifications`
   
   https://hub.docker.com/r/ttobias/logfile-notifications/
