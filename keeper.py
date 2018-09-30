#!/usr/bin/env python3

import os, sys
import urllib2


ENTRY = os.environ.get('GITLAB_URL')



class Gitlab:
    api_url_issues = '/api/v4/projects/228/issues?page=1&per_page=100&state=opened'

    def 