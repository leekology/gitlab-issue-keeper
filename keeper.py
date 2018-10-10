#!/usr/bin/env python3

import os, sys
import json
from urllib import request
from urllib.parse import urlencode


ENTRY = os.environ.get('GITLAB_URL')
TOKEN = os.environ.get('GITLAB_TOKEN')
DOING_LABEL = 'Doing'
GANTT_START = 'GanttStart:'
GANTT_END = 'GanttDue:'

# ToDo: get project by url
# ToDO: group by milestone
# ToDo: issue start date by /spend


class Gitlab:

    def __init__(self, gitlab_url, gitlab_token):
        self.gitlab_url, self.gitlab_token = gitlab_url, gitlab_token

    def req_api(self, path, data=None):
        headers = {
            'PRIVATE-TOKEN': self.gitlab_token,
            'Access-Control-Request-Headers': 'private-token',
            'User-Agent': 'gitlab-issue-keeper',
        }
        if data is None:
            r = request.Request(f'{self.gitlab_url}{path}', headers=headers)
        else:
            params = urlencode(data)
            # stupid RESTful
            r = request.Request(f'{self.gitlab_url}{path}?{params}', headers=headers, method='PUT')
        return json.loads(request.urlopen(r, timeout=4).read())

    def get_projects(self):
        r = self.req_api('/api/v4/projects/?membership=true&per_page=100')
        return dict((
            p["path_with_namespace"], {
                "path": p["path_with_namespace"],
                "name": p["name"],
                "namespace": p["namespace"].get("path"),
                "last_activity_at": p["last_activity_at"],
                "description": p["description"],
                "url": p["web_url"],
                "id": p["id"],
            }
        ) for p in r if
            p["archived"] is False and p["namespace"].get("kind") == "group")

    @classmethod
    def guess_progress(cls, issue):
        total = issue["time_stats"].get("time_estimate")
        if not total or total <= 0:
            return
        spent = issue["time_stats"].get("total_time_spent") or 0
        return spent / total * 100


class GitlabProject:
    def __init__(self, gitlab_obj, project_id):
        self.project_id = project_id
        self.gitlab_obj = gitlab_obj

    @property
    def labels_map(self):
        labels = getattr(self, '_labels', None)
        self.labels = labels or dict((x['name'], x['id']) for x in
            self.gitlab_obj.req_api(f'/api/v4/projects/{self.project_id}/labels') or [])  # noqa
        return self.labels

    def get_issue_notes(self, iid):
        r = self.gitlab_obj.req_api(f'/api/v4/projects/{self.project_id}/issues/{iid}/notes')
        return r

    def get_doing_close_date(self, iid):
        label_id = self.labels_map[DOING_LABEL]
        issue_notes = list(self.get_issue_notes(iid))
        starts = sorted([x for x in issue_notes if
            x['system'] and x['body'] == f'added ~{label_id} label'  # noqa
        ], key=lambda x: x['id']) or issue_notes[-2:]
        if not starts:
            return None, None

        ends1 = sorted([x for x in issue_notes if
            x['system'] and x['body'] == 'closed'  # noqa
        ], key=lambda x: x['id'])

        ends2 = sorted([x for x in issue_notes if
            x['system'] and x['body'] == f'removed ~{label_id} label'  # noqa
        ], key=lambda x: x['id'])

        ends = ends1[-2:] + ends2[-2:]

        return starts[0]['updated_at'], min(ends, key=lambda x: x['id'])['updated_at'] if ends else None

    def list_issues(self):
        r = self.gitlab_obj.req_api(f'/api/v4/projects/{self.project_id}/issues?page=1&per_page=100&state=all')
        for issue in r:
            start, end = self.get_doing_close_date(issue['iid'])
            yield issue, start, end

    def update_issue(self, issue, start, end):
        """issue =  {iid: 1, description: "", project_id: 0}"""
        gantt_str = ''
        if start:
            gantt_str = '%s\n%s%s' % (gantt_str, GANTT_START, start)
        if end:
            gantt_str = '%s\n%s%s' % (gantt_str, GANTT_END, end)
        if start or end:
            # remove old str
            lines = []
            inline_edit = False
            for l in issue['description'].splitlines():
                if l.startswith(GANTT_START) and start:
                    lines.append(f'{GANTT_START}{start}')
                    inline_edit = True
                elif l.startswith(GANTT_END) and end:
                    lines.append(f'{GANTT_END}{end}')
                    inline_edit = True
            desc_back = '\n'.join(lines)
            desc = '%s\n\n<!--\n下面是issue耗时跟踪不要删\n%s\n-->' % (desc_back, gantt_str)
            r = self.gitlab_obj.req_api(f'/api/v4/projects/{issue["project_id"]}/issues/{issue["iid"]}', {"description": desc})


def output_json(data, padding=None):
    if padding:
        # @ToDo: add sanitize padding
        return '%s(%s)' % (padding, json.dumps(data))
    else:
        return json.dumps(data)


if '__main__' == __name__:
    exit(0)
