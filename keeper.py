#!/usr/bin/env python3

import os, sys
import urllib2, json


ENTRY = os.environ.get('GITLAB_URL')
TOKEN = os.environ.get('GITLAB_TOKEN')
DOING_LABEL = 'Doing'

# ToDo: get project by url
# ToDO: by milestone


class Gitlab:

    def __init__(self, gitlab_url, gitlab_token):
        self.gitlab_url, self.gitlab_token = gitlab_url, gitlab_token

    def req_api(self, path):
        r = urllib2.urlopen(urllib2.Request(
            f'{self.gitlab_url}{path}',
            headers={'PRIVATE-TOKEN', self.gitlab_token}))
        return json.loads(r.read())

    def get_issue_notes(self, iid):
        r = self.req_api(f'/api/v4/projects/228/issues/{iid}/notes')
        return r

    def get_doing_close_date(self, iid):
        label_id = self.labels_map[DOING_LABEL]
        starts = [
            x for x in self.get_issue_notes(iid)
            if x['system'] and x['body'] == f'added ~{label_id} label']
        ends = [
            x for x in self.get_issue_notes(iid)
            if x['system'] and x['body'] in ['closed', f'removed ~{label_id} label']]

    def list_issues(self):
        r = self.req_api('/api/v4/projects/228/issues?page=1&per_page=100&state=opened')
        for issue in r:
            pass

    @property
    def labels_map(self):
        labels = self.req_api('/api/v4/projects/228/labels') or []
        return dict((x['name'], x['id']) for x in labels)


if '__main__' == __name__:
    exit(0)
