import mock
import os
import unittest

from affectiva.api import EmotionAPI


class TestApi(unittest.TestCase):

    def test_init_without_username(self):
        with mock.patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegexp(ValueError, "No username provided."):
                EmotionAPI(None, 'pass')()

    def test_init_without_password(self):
        with mock.patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegexp(ValueError, "No password provided."):
                EmotionAPI('user', None)()

    @mock.patch('requests.get')
    def test_init_default_service_url(self, mockget):
        mockresponse = mock.Mock()
        mockget.return_value = mockresponse
        expected_job_url = 'https://blah/jobs'
        mockresponse.json.return_value = {"v1": {EmotionAPI.JOB_SERVICE_KEY: expected_job_url}}

        expected_service_url = 'https://index.affectiva.com'

        api = EmotionAPI('user', 'pass')
        self.assertEqual(api._index[EmotionAPI.JOB_SERVICE_KEY], expected_job_url)
        mockget.assert_called_once_with(expected_service_url, headers={'Accept': 'application/json'})

    @mock.patch('requests.get')
    def test_init_other_service_url(self, mockget):
        mockresponse = mock.Mock()
        mockget.return_value = mockresponse
        expected_job_url = 'https://blah/jobs'
        mockresponse.json.return_value = {"v1": {EmotionAPI.JOB_SERVICE_KEY: expected_job_url}}

        expected_service_url = 'http://localhost:3001'
        # set environment variable to overide service url
        os.environ["AFFECTIVA_API_SERVICE_URL"] = expected_service_url

        api = EmotionAPI('user', 'pass')
        self.assertEqual(api._index[EmotionAPI.JOB_SERVICE_KEY], expected_job_url)
        mockget.assert_called_once_with(expected_service_url, headers={'Accept': 'application/json'})


if __name__ == '__main__':
    unittest.main()
