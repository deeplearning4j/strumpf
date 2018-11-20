################################################################################
# Copyright (c) 2015-2018 Skymind, Inc.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
################################################################################

from .utils import _BASE_DIR, get_dir
import platform
import os
import warnings
import os
from subprocess import call as py_call
import json


def call(arglist):
    error = py_call(arglist)
    if error:
        raise Exception('Subprocess error for command: ' + str(arglist))


_CONFIG_FILE = os.path.join(_BASE_DIR, 'config.json')
_CONFIG = {
    'azure_account_name': 'dl4jtestresources',
    'file_size_limit_in_mb': '2',
    'container_name': 'resources',
}

def target_dir():
    return get_dir()

def _write_config(filepath=None):
    if not filepath:
        filepath = _CONFIG_FILE
    with open(filepath, 'w') as f:
        json.dump(_CONFIG, f)


if os.path.isfile(_CONFIG_FILE):
    with open(_CONFIG_FILE, 'r') as f:
        _CONFIG.update(json.load(f))
else:
    _write_config()


def set_config(config):
    _CONFIG.update(config)
    _write_config()


def get_config():
    return _CONFIG

def get_limit_in_bytes():
    limit = _CONFIG['file_size_limit_in_mb']
    return int(limit) * 1000

def get_local_resource_dir():
    return _CONFIG['local_resource_folder']

def get_context_from_config():
    local_resource_folder = _CONFIG['local_resource_folder']
    resource_name = local_resource_folder.split('/')[-1]
    return resource_name


def validate_config(config=None):
    if config is None:
        config = _CONFIG

def _get_all_contexts():
    c = os.listdir(_BASE_DIR)
    return [x for x in c if x.startswith('strumpf')]


def get_large_files(relative_path=None):
    large_files = []
    local_dir = get_local_resource_dir()
    if relative_path:
        local_dir = os.path.join(local_dir, relative_path)
    
    limit = get_limit_in_bytes()
    for path, _, filenames in os.walk(local_dir):
        for name in filenames:
            full_path = os.path.join(path, name)
            if  os.path.getsize(full_path) > limit:
                large_files.append(full_path)
    return large_files


def get_tracked_files(relative_path=None):
    tracked_files = []
    local_dir = get_local_resource_dir()
    if relative_path:
        local_dir = os.path.join(local_dir, relative_path)
    for path, _, filenames in os.walk(local_dir):
        for name in filenames:
            full_path = os.path.join(path, name)
            if full_path.endswith(".resource_reference"):
                original_file = full_path.replace(".resource_reference", "")
                tracked_files.append(original_file)
    return tracked_files


def is_file(path):
    local_dir = get_local_resource_dir()
    full_path = os.path.join(local_dir, path)
    return os.path.isfile(full_path)
