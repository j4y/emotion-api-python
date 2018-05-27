import os

import requests

ACCEPT_JSON = {'Accept': 'application/json'}


class EmotionAPI:
    """Class to handle interfacing with Affectiva's Emotion as a Service API.

    Example usage:

    api = EmotionAPI( 'username', 'password' )
    resp = api.create_job( 'path/to/local/video.mp4' )     # Upload video
    job_url = resp['self']

    api.results( job_url )                        # Get the results (results may not be available immediately)
    """

    EAAS_USER_ENV_VAR = 'AFFECTIVA_API_USER'  # Environment variable from which we will attempt to user (for authentication)
    EAAS_PASS_ENV_VAR = 'AFFECTIVA_API_PASSWORD'  # Environment variable from which we will attempt to password (for authentication)

    INDEX_SERVICE_URL = 'https://index.affectiva.com'
    JOB_SERVICE_KEY = 'jobs'

    def __init__(self, user=None, password=None, version='v1'):
        """Initialize.
        If no user and/or password is provided, credentials are retrieved from environment variables.

        Args:
            user: (optional) Authentication username.
            password: (optional) Authentication password.
            version:  (optional) Job service version number. e.g. 'v1','development'
        """
        self._user = user if user else os.environ.get(self.EAAS_USER_ENV_VAR, None)
        self._password = password if password else os.environ.get(self.EAAS_PASS_ENV_VAR, None)
        self._auth = (self._user, self._password)
        if self._user is None:
            raise ValueError("No username provided.")
        if self._password is None:
            raise ValueError("No password provided.")

        self._job_url = self._get_job_service_url(version)

    def _get_job_service_url(self, version):
        """Connect to the index service and retrieve the job service URL.

        Args:
            version:  Job version string (e.g. 'v1')
        """

        resp = requests.get(self.INDEX_SERVICE_URL, headers=ACCEPT_JSON)
        return resp.json()[version][self.JOB_SERVICE_KEY]

    def create_job(self, media_path, job_name='multiface', data_split='unassigned'):
        """Upload a media file (e.g. video) for processing.

        Args:
            media_path: Path to local media file to be uploaded
            job_name: (optional) Which classifier set to use. See: http://developer.affectiva.com/eaasapi/

        Returns:
             JSON response with keys: 'status', 'updated', 'name', 'author', 'self', 'published', 'input'
        """
        with open(media_path, 'rb') as video:
            files = {'entry_job[name]': (None, job_name),
                     'entry_job[input]': (os.path.basename(media_path), video)}
            data = {'entry[data_spli]': data_split}
            resp = requests.post(self._job_url, auth=self._auth, headers=ACCEPT_JSON, files=files, data=data)
            resp.raise_for_status()
            return resp.json()

    def query_job(self, job_url):
        """Connect to a created job and return job status.

        Args:
            job_url: URL returned from create_job used to retrieve results

        Returns:
            JSON response
        """
        resp = requests.get(job_url, auth=self._auth, headers=ACCEPT_JSON)
        resp.raise_for_status()
        return resp.json()

    def download_results(self, job_url, content_type='application/csv', output_dir='.'):
        """download results from a job and save locally.

        Args:
            job_url: URL returned from create_job used to retrieve results
            content_type:  Content type to retrieve e.g. 'application/csv'
            output_dir: (optional) Local folder where we will save the asset.

        Returns:
            Path to local file
        """
        job_json = self.query_job(job_url)

        result_json = None
        all_representations_json = job_json['result']['representations']
        for representation_json in all_representations_json:
            if representation_json['content_type'] == content_type:
                result_json = representation_json
                break

        if result_json is None:
            all_content_types = [x['content_type'] for x in all_representations_json]
            raise ValueError("Could not match content_type '%s'.\n"
                             "Available content-types: %s" % (content_type, str(all_content_types)))
        else:
            file_name = result_json['file_name']
            local_path = os.path.join(output_dir, file_name)
            with open(local_path, 'wb') as fout:
                media_url = result_json['media']
                media_resp = requests.get(media_url, auth=self._auth)
                media_resp.raise_for_status()
                fout.write(media_resp.content)
            return local_path

    def results(self, job_url):
        """Returns the results for a processed image or video.

        Returns:
            JSON response contains the metric results for a processed job
            For more information about output, see application/vnd.affectiva.session.v0+json
            in http://developer.affectiva.com/api/contenttypes/
        """
        metrics = []
        job_json = self.query_job(job_url)
        for representation in job_json['result']['representations']:
            if representation['content_type'] == 'application/vnd.affectiva.session.v0+json':
                media_url = representation['media']
                media_resp = requests.get(media_url, auth=self._auth)
                media_resp.raise_for_status()
                metrics = media_resp.json()
        return metrics

    def jobs(self):
        """List all the jobs in an account.

        Returns:
            JSON response containing all the jobs.
            ['status', 'updated', 'author', 'self', 'filename', 'published']
        """
        resp = requests.get(self._job_url, auth=self._auth, headers=ACCEPT_JSON)
        resp.raise_for_status()
        return resp.json()

    def add_annotation(self, entry, source, key, value):
        resp = requests.post(entry['annotations'], auth=self._auth, headers=ACCEPT_JSON,
                             data={"annotation[source]": source, "annotation[key]": key, "annotation[value]": value})
        resp.raise_for_status()
        return resp.json()

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
