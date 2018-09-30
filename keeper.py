#!/usr/bin/env python3

import os, sys
import urllib2, json


ENTRY = os.environ.get('GITLAB_URL')
TOKEN = os.environ.get('GITLAB_TOKEN')

# ToDo: get project by url


class Gitlab:
    api_url_issues = '/api/v4/projects/228/issues?page=1&per_page=100&state=opened'

    def __init__(self, gitlab_url, gitlab_token):
        self.gitlab_url, self.gitlab_token = gitlab_url, gitlab_token

    def req_api(self, path):
        r = urllib2.urlopen(urllib2.Request(
            f'{self.gitlab_url}{path}',
            headers={'PRIVATE-TOKEN', self.gitlab_token}))
        return json.loads(r.read())

    def list_issues(self):
        return self.req_api()

    def labels_map(self):
        labels = self.req_api('/api/v4/projects/228/labels') or []
        return dict((x['id'], x['name']) for x in labels)



if '__main__' == __name__:
    exit(0)
