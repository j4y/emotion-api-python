import requests
import json
import shutil


class Base(object):
    _url = ''
    _user = ''
    _password = ''

    def __init__(self, url=None, user=None, password=None):
        self._url = url
        self._user = user
        self._password = password
        self._auth = (self._user, self._password)
        self._headers = {'Accept': 'application/json',
                         'Content-Type': 'application/json'}
        self._details = self._details()

    def delete(self):
        """Delete a base type.
        """
        self._delete(self._url)

    def _details(self):
        """Get the entry details from API.
        """
        return self._get(self._url) if self._url is not None else dict()

    def _get(self, url):
        resp = requests.get(url, auth=self._auth, headers=self._headers)
        return resp.json()

    def _post(self, url, payload):
        resp = requests.post(url, auth=self._auth, headers=self._headers, data=json.dumps(payload))
        return resp.json()

    def _delete(self, url):
        requests.delete(url, auth=self._auth)


class Entry(Base):
    _annotation_url = ''
    _media_seconds = 0
    _list_annotations = list()

    def __init__(self, **kwargs):
        super(Entry, self).__init__(**kwargs)
        self._annotation_url = self._details['annotations']

    def _annotations(self):
        """Get the annotations of an entry.

        Args:
            annotations_url: Annotations URL returned from job entry
        """

        return [Annotation(url=annotation['self'], user=self._user,
                           password=self._password) for annotation in self._get(self._annotation_url)]

    def annotations(self):
        """Get the list of annotations.
        Returns:
             return list of annotations.
        """

        self._list_annotations = self._annotations()
        return self._list_annotations

    def representations(self):
        """Get the list of representations.
        Returns:
             return list of representations.
        """
        return [Representation(url=representation['self'], user=self._user,
                               password=self._password) for representation in self._details['representations']]

    def length(self):
        """Get length of media in seconds.
        Returns:
             return double representing media in seconds.
        """
        return self._media_seconds

    def add_annotations(self, annotations=list()):
        """Add an annotation to an account.
        Args:
            annotations: list of annotations to be added
        """

        for annotation in annotations:
            self._post(self._annotation_url, {"annotation": dict(annotation)})

class Representation(Base):

    def __init__(self, **kwargs):
        super(Representation, self).__init__(**kwargs)

    def file_name(self):
        """Get the file name of the media
        Returns:
             return str representation of the uploaded filename
        """
        return self._details['file_name']

    def file_size(self):
        """Get the media file size
        Returns:
             return the media file size in bytes
        """
        return self._details['file_size']

    def content_type(self):
        """Get the media content type
        Returns:
             return a str representation of the content type
        """
        return self._details['content_type']

    def save_media(self, file_path):
        """Download media representation and save it as file.
        Args:
            file_path: the path to save media on disk
        """
        resp = requests.get(self._url+'/media', stream=True, auth=self._auth)
        with open(file_path, 'wb') as out_file:
            shutil.copyfileobj(resp.raw, out_file)

class Annotation(Base):
    def __init__(self, key=None, value=None, source=None, **kwargs):
        super(Annotation, self).__init__(**kwargs)
        if len(self._details) is 0:
            self._details['source'] = source
            self._details['key'] = key
            self._details['value'] = value

    def __iter__(self):
        yield 'source', self._details['source']
        yield 'key', self._details['key']
        yield 'value', self._details['value']

    def source(self):
        """Get the annotation source
        Returns:
             return a str representation of the annotation source
        """
        return self._details['source']

    def key(self):
        """Get the annotation key
        Returns:
             return a str representation of the annotation key
        """
        return self._details['key']

    def value(self):
        """Get the annotation value
        Returns:
             return a str representation of the annotation value
        """
        return self._details['value']
