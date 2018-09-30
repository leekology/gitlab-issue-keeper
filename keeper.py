#!/usr/bin/env python3

import os, sys
import json
from urllib import request


ENTRY = os.environ.get('GITLAB_URL')
TOKEN = os.environ.get('GITLAB_TOKEN')
DOING_LABEL = 'Doing'

# ToDo: get project by url
# ToDO: by milestone


class Gitlab:

    def __init__(self, gitlab_url, gitlab_token):
        self.gitlab_url, self.gitlab_token = gitlab_url, gitlab_token
        self.labels = {}

    def req_api(self, path):
        r = request.urlopen(request.Request(f'{self.gitlab_url}{path}', headers={
            'PRIVATE-TOKEN': self.gitlab_token,
            'Access-Control-Request-Headers': 'private-token',
            'User-Agent': 'gitlab-issue-keeper',
        }), timeout=2)
        return json.loads(r.read())

    def get_issue_notes(self, iid):
        r = self.req_api(f'/api/v4/projects/228/issues/{iid}/notes')
        return r

    def get_doing_close_date(self, iid):
        label_id = self.labels_map[DOING_LABEL]
        issue_notes = list(self.get_issue_notes(iid))
        starts = sorted([x for x in issue_notes if
            x['system'] and x['body'] == f'added ~{label_id} label'  # noqa
        ], key=lambda x: x['id']) or issue_notes[-2:]

        ends1 = sorted([x for x in issue_notes if
            x['system'] and x['body'] == 'closed'  # noqa
        ], key=lambda x: x['id'])

        ends2 = sorted([x for x in issue_notes if
            x['system'] and x['body'] == f'removed ~{label_id} label'  # noqa
        ], key=lambda x: x['id'])

        ends = ends1[-2:] + ends2[-2:]

        return starts[0]['updated_at'], min(ends, key=lambda x: x['id'])['updated_at'] if ends else None

    def list_issues(self):
        r = self.req_api('/api/v4/projects/228/issues?page=1&per_page=100&state=all')
        for issue in r:
            iid = issue['iid']
            start, end = self.get_doing_close_date(issue['iid'])
            print('%04d: %s %s' % (iid, start, end))

    @property
    def labels_map(self):
        self.labels = self.labels or dict((x['name'], x['id']) for x in
            self.req_api('/api/v4/projects/228/labels') or [])  # noqa
        return self.labels


if '__main__' == __name__:
    exit(0)
