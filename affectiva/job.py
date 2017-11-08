import requests
import json


ACCEPT_JSON = {'Accept': 'application/json'}


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

    def add_representation(self, entry, media_path, mimetype):
        """Upload an additional representation to the provided entry.

        Args:
            entry: A dict containing the entry to which the
              representation will be attached.
            media_path: Path to local media file to be uploaded.  The
              entry must not already have a representation with this
              filename.
            mimetype: A string with the representation's media type.

        Example:
        >>> from affectiva.api import EmotionAPI
        >>> e = EmotionAPI()
        >>> j = e.create_job('video1.mp4')
        >>> e.add_representation(j['input'],'video2.mp4','application/vnd.affectiva.example+mp4')

        """
        metadata = {'media': (media_path, open(media_path, 'rb'), mimetype)}
        resp = requests.post(entry['representation_self'], auth=self._auth, headers=ACCEPT_JSON, files=metadata)
        resp.raise_for_status()
        return resp.json()
