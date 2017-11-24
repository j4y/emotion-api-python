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

    def _details(self):
        """Get the entry details from API.
        """
        return self._get(self._url)

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

        return self._get(self._annotation_url)

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
        return self._entry_details()['representations']

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
            self._post(self._annotation_url, {"annotation": annotation})

    def delete_annotation(self, annotation=dict()):
        """Remove an annotation from an entry.
        Args:
            annotation: the annotation to be removed
        """

        annotations = self.annotations()
        for a in annotations:
            if (a['source'] == annotation['source'] and
                    a['key'] == annotation['key'] and
                    a['value'] == annotation['value']):

                self._delete(a['self'])
                break


class Representation(Base):
    _media_url = ''
    _file_name = ''
    _file_size = 0
    _content_type = ''

    def __init__(self, media_url='', **kwargs):
        super(Representation, self).__init__(**kwargs)
        self._media_url = media_url
        self._file_name = self._details['file_name']
        self._file_size = self._details['file_size']
        self._content_type = self._details['content_type']

    def file_name(self):
        """Get the file name of the media
        Returns:
             return str representation of the uploaded filename
        """
        return self._file_name

    def file_size(self):
        """Get the media file size
        Returns:
             return the media file size in bytes
        """
        return self._file_size

    def content_type(self):
        """Get the media content type
        Returns:
             return a str representation of the content type
        """
        return self._content_type

    def save_media(self, file_path):
        """Download media representation and save it as file.
        Args:
            file_path: the path to save media on disk
        """
        resp = requests.get(self._media_url, stream=True, auth=self._auth)
        with open(file_path, 'wb') as out_file:
            shutil.copyfileobj(resp.raw, out_file)
