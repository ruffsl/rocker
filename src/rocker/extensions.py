# Copyright 2019 Open Source Robotics Foundation

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import grp
import os
import em
import getpass
import pwd
import pkgutil
from pathlib import Path
from shlex import quote
import subprocess
import sys


def name_to_argument(name):
    return '--%s' % name.replace('_', '-')

from .core import RockerExtension

class DevHelpers(RockerExtension):
    @staticmethod
    def get_name():
        return 'dev_helpers'

    def __init__(self):
        self._env_subs = None
        self.name = DevHelpers.get_name()


    def get_environment_subs(self):
        if not self._env_subs:
            self._env_subs = {}
            self._env_subs['user_id'] = os.getuid()
            self._env_subs['username'] = getpass.getuser()
        return self._env_subs

    def get_preamble(self, cliargs):
        return ''

    def get_snippet(self, cliargs):
        snippet = pkgutil.get_data('rocker', 'templates/%s_snippet.Dockerfile.em' % self.name).decode('utf-8')
        return em.expand(snippet, self.get_environment_subs())

    @staticmethod
    def register_arguments(parser):
        parser.add_argument(name_to_argument(DevHelpers.get_name()),
            action='store_true',
            help="add development tools emacs and byobu to your environment")


class PulseAudio(RockerExtension):
    @staticmethod
    def get_name():
        return 'pulse'

    def __init__(self):
        self._env_subs = None
        self.name = PulseAudio.get_name()


    def get_environment_subs(self):
        if not self._env_subs:
            self._env_subs = {}
            self._env_subs['user_id'] = os.getuid()
            self._env_subs['XDG_RUNTIME_DIR'] = os.getenv('XDG_RUNTIME_DIR')
            self._env_subs['audio_group_id'] = grp.getgrnam('audio').gr_gid
        return self._env_subs

    def get_preamble(self, cliargs):
        return ''

    def get_snippet(self, cliargs):
        snippet = pkgutil.get_data('rocker', 'templates/%s_snippet.Dockerfile.em' % self.name).decode('utf-8')
        return em.expand(snippet, self.get_environment_subs())

    def get_docker_args(self, cliargs):
        args = ' -v /run/user/%(user_id)s/pulse:/run/user/%(user_id)s/pulse --device /dev/snd '\
        ' -e PULSE_SERVER=unix:%(XDG_RUNTIME_DIR)s/pulse/native -v %(XDG_RUNTIME_DIR)s/pulse/native:%(XDG_RUNTIME_DIR)s/pulse/native --group-add %(audio_group_id)s '
        return args % self.get_environment_subs()

    @staticmethod
    def register_arguments(parser):
        parser.add_argument(name_to_argument(PulseAudio.get_name()),
            action='store_true',
            help="mount pulse audio devices")


class HomeDir(RockerExtension):
    @staticmethod
    def get_name():
        return 'home'

    def __init__(self):
        self.name = HomeDir.get_name()

    def get_docker_args(self, cliargs):
        return ' -v %s:%s ' % (Path.home(), Path.home())

    @staticmethod
    def register_arguments(parser):
        parser.add_argument(name_to_argument(HomeDir.get_name()),
            action='store_true',
            help="mount the users home directory")


class User(RockerExtension):
    @staticmethod
    def get_name():
        return 'user'

    def get_environment_subs(self):
        if not self._env_subs:
            user_vars = ['name', 'uid', 'gid', 'gecos','dir', 'shell']
            userinfo = pwd.getpwuid(os.getuid())
            self._env_subs = {
                k: getattr(userinfo, 'pw_' + k)
                for k in user_vars }
        return self._env_subs

    def __init__(self):
        self._env_subs = None
        self.name = User.get_name()

    def get_snippet(self, cliargs):
        snippet = pkgutil.get_data('rocker', 'templates/%s_snippet.Dockerfile.em' % self.name).decode('utf-8')
        return em.expand(snippet, self.get_environment_subs())

    @staticmethod
    def register_arguments(parser):
        parser.add_argument(name_to_argument(User.get_name()),
            action='store_true',
            help="mount the users home directory")


class Environment(RockerExtension):
    @staticmethod
    def get_name():
        return 'env'

    def __init__(self):
        self.name = Environment.get_name()

    def get_snippet(self, cli_args):
        return ''

    def get_docker_args(self, cli_args):
        args = ['']
        for env in cli_args['env']:
            args.append('-e {0}'.format(quote(env)))

        return ' '.join(args)

    @staticmethod
    def register_arguments(parser):
        parser.add_argument('--env',
            metavar='NAME[=VALUE]',
            type=str,
            nargs='+',
            help='set environment variables')
