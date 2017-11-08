# Python Utils for Affectiva Emotion API

Welcome to our repository on GitHub! Here you will find the source code of a python library that can be used to communicate with the Affectiva Emotion API service to process videos or images. For more information, visit our <a href=http://developer.affectiva.com/>Affectiva's Developer Portal</a>.

[![Build Status](https://travis-ci.org/Affectiva/emotion-api-python.svg?branch=master)](https://travis-ci.org/Affectiva/emotion-api-python)

Dependencies
------------

- Python 2.7
- requests

Installation
------------
```bashrc
pip install AffectivaEmotionAPI
```

Usage
-----

**Sign up for credentials: ** http://developer.affectiva.com/apioverview/


**Upload an Image or a Video file for processing ?**

```python
import affectiva.api
username = 'API_USER'
passwd = 'API_PASSWD'
api = affectiva.api.EmotionAPI(username,passwd)

# Upload a file for Processing
filename = '/home/mahmoud/Desktop/test_file.mp4'
job_url = api.create_job(filename)['self']
```

**Get face detection and emotion results **

```python
job_status = api.query_job(job_url)['status']

if status == 'done':
  metrics_json = api.results(job_url)

```

Uploading to PyPI
-----------------
Increment the version in setup.py

```bashrc
rm dist/*.tar.gz
python setup.py sdist
twine upload dist/*
```
