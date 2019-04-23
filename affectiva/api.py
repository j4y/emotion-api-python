import os
import mimetypes
import requests

ACCEPT_JSON = {'Accept': 'application/json'}


class EmotionAPI(object):
    """Class to handle interfacing with Affectiva's Emotion as a Service API.

    Example usage:

    api = EmotionAPI( 'username', 'password' )
    resp = api.create_job( 'path/to/local/video.mp4' )     # Upload video
    job_url = resp['self']

    api.results( job_url )                        # Get the results (results may not be available immediately)
    """

    EAAS_USER_ENV_VAR = 'AFFECTIVA_API_USER'  # Environment variable from which we will attempt to user (for authentication)
    EAAS_PASS_ENV_VAR = 'AFFECTIVA_API_PASSWORD'  # Environment variable from which we will attempt to password (for authentication)
    EAAS_SERVICE_URL_ENV_VAR = 'AFFECTIVA_API_SERVICE_URL'  # Environment variable to overide the index server url. (only used for testing)
    INDEX_SERVICE_URL = 'https://index.affectiva.com'  # default index server url
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
        # allow index service URL to be overridden with an environment variable for testing
        self.INDEX_SERVICE_URL = os.environ.get(self.EAAS_SERVICE_URL_ENV_VAR, self.INDEX_SERVICE_URL)
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
        resp.raise_for_status()
        return resp.json()[version][self.JOB_SERVICE_KEY]

    def create_job(self, media_path, job_name='multiface', extra_params={}):
        """Upload a media file (e.g. video) for processing.

        Args:
            media_path: Path to local media file to be uploaded
            job_name: (optional) Which classifier set to use. See: http://developer.affectiva.com/eaasapi/
            extra_params: (optional) A dictionary of additional parameters to pass to the API

        Returns:
             JSON response with keys: 'status', 'updated', 'name', 'author', 'self', 'published', 'input'
        """
        mime_type = mimetypes.guess_type(media_path)[0]
        with open(media_path, 'rb') as video:
            files = {'entry_job[name]': (None, job_name),
                     'entry_job[input]': (os.path.basename(media_path), video, mime_type)}
            resp = requests.post(self._job_url, auth=self._auth, headers=ACCEPT_JSON, files=files, data=extra_params)
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

    def update_job(self, job_url, job_name=None):
        """Update the job.

        Args:
            job_name: (optional) Which classifier set to use. See: http://developer.affectiva.com/eaasapi/

        Returns:
            JSON response with keys ['status', 'updated', 'name', 'author', 'self', 'published', 'input']
        """
        data = {}
        if job_name is not None:
            data['entry_job[name]'] = job_name
        resp = requests.patch(job_url, auth=self._auth, data=data, headers=ACCEPT_JSON)
        resp.raise_for_status()
        return resp.json()

    def download_representation(self, representation, output_dir='.'):
        """download a representation and save locally.

        Args:
            representation: dict containing the representation data
            content_type:  Content type to retrieve e.g. 'application/csv'
            output_dir: (optional) Local folder where we will save the asset.

        Returns:
            Path to local file
        """
        file_name = representation['file_name']
        local_path = os.path.join(output_dir, file_name)
        with open(local_path, 'wb') as fout:
            media_url = representation['media']
            media_resp = requests.get(media_url, auth=self._auth)
            media_resp.raise_for_status()
            fout.write(media_resp.content)
        return local_path

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

        all_representations_json = job_json['result']['representations']
        for representation_json in all_representations_json:
            if representation_json['content_type'] == content_type:
                return self.download_representation(representation_json, output_dir)

        all_content_types = [x['content_type'] for x in all_representations_json]
        raise ValueError("Could not match content_type '%s'.\n"
                         "Available content-types: %s" % (content_type, str(all_content_types)))

    def download_media_input(self, job_url, content_type='video/mp4', output_dir='.', filename=None, add_job_id=False):
        """
        The function downloads media file attached to the job url passed.
        filename is either equal to the passed filename param if passed or 'EaaS_<media_filename>_<job_id>' is add_job_id == True
        or will be saved by default media file name saved in EaaS if no filename is passed and add_job_id == False
        """
        job_json = self.query_job(job_url)

        result_json = None
        all_representations_json = job_json['input']['representations']
        for representation_json in all_representations_json:
            if representation_json['content_type'] == content_type:
                result_json = representation_json
                break

        if result_json is None:
            all_content_types = [x['content_type'] for x in all_representations_json]
            raise ValueError("Could not match content_type '%s'.\n"
                             "Available content-types: %s" % (content_type, str(all_content_types)))
        else:
            if filename:
                dst_file_name = filename
            elif add_job_id:
                media_file_name, ext = os.path.splitext(result_json['file_name'])
                job_id = job_url.split('/')[-1]
                dst_file_name = 'EAAS_' + media_file_name + '_' + job_id + ext
            else:
                dst_file_name = result_json['file_name']

            local_path = os.path.join(output_dir, dst_file_name)

            with open(local_path, 'wb') as fout:
                media_url = result_json['media']
                media_resp = requests.get(media_url, auth=self._auth)
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

    def add_annotations(self, entry, annotations):
        """Add a list of annotations to an entry.  Each annotation is a dict with the keys 'source', 'key', and 'value'.
        """
        for annotation in annotations:
            self.add_annotation(entry, annotation['source'], annotation['key'], annotation['value'])

    def delete_annotation(self, entry, source, key):
        """Delete an annotation from an entry."""
        annotations = self.query_job(entry['annotations'])
        for a in annotations:
            if a['source'] == source and a['key'] == key:
                resp = requests.delete(a['self'], auth=self._auth, headers=ACCEPT_JSON)
                resp.raise_for_status()

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

    def update_representation(self, representation, media_path, mimetype):
        """Update the media attached to the provided representation.
        Args:
            entry: A dict containing the representation to which the
              media will be attached.
            media_path: Path to local media file to be uploaded.
            mimetype: A string with the representation's media type.
        Example:
        >>> from affectiva.api import EmotionAPI
        >>> e = EmotionAPI()
        >>> j = e.create_job('video1.mp4')
        >>> e.update_representation(j['input']['representations'][0],'video2.mp4','application/vnd.affectiva.example+mp4')
        """
        metadata = {'media': (media_path, open(media_path, 'rb'), mimetype)}
        resp = requests.put(representation['self'], auth=self._auth, headers=ACCEPT_JSON, files=metadata)
        resp.raise_for_status()
