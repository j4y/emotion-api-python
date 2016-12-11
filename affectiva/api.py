import requests
import os


class EmotionAPI:
    """Class to handle interfacing with Affectiva's Emotion as a Service API.

    Example usage:

    api = EmotionAPI( 'username', 'password' )
    resp = api.create_job( 'path/to/local/video.mp4' )     # Upload video
    job_url = resp['self']

    api.retrieve_results( job_url )                        # Download results (results may not be available immediately)
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

        headers = {'Accept': 'application/json'}
        resp = requests.get(self.INDEX_SERVICE_URL, headers=headers)
        return resp.json()[version][self.JOB_SERVICE_KEY]

    def create_job(self, media_path, job_name='current-pack'):
        """Upload a media file (e.g. video) for processing.

        Args:
            media_path: Path to local media file to be uploaded
            job_name: (optional) Which classifier set to use. See: http://developer.affectiva.com/eaasapi/

        Returns:
             JSON response with keys: 'status', 'updated', 'name', 'author', 'self', 'published', 'input'
        """
        headers = {'Accept': 'application/json'}
        with open(media_path, 'rb') as video:
            files = {'entry_job[name]': (None, job_name),
                     'entry_job[input]': (os.path.basename(media_path), video)}
            resp = requests.post(self._job_url, auth=self._auth, headers=headers, files=files)
            return resp.json()

    def query_job(self, job_url):
        """Connect to a created job and return job status.

        Args:
            job_url: URL returned from create_job used to retrieve results

        Returns:
            JSON response
        """
        headers = {'Accept': 'application/json'}
        resp = requests.get(job_url, auth=self._auth, headers=headers)

        assert resp.status_code == 200
        resp_json = resp.json()
        return resp_json

    def retrieve_results(self, job_url, content_type='application/csv', output_dir='.'):
        """Retrieve results from a job and save locally.

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
                fout.write(media_resp.content)
            return local_path

    def list_jobs(self):
        """List all the jobs in an account.

        Returns:
            JSON response containing all the jobs.
            ['status', 'updated', 'author', 'self', 'filename', 'published']
        """
        headers = {'Accept': 'application/json'}
        resp = requests.get(self._job_url, auth=self._auth, headers=headers)
        return resp.json()
