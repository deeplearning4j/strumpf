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
import requests
import json
import os


def mkdir(x):
    if not os.path.isdir(x):
        os.mkdir(x)


_CONTEXT_NAME = None
_CONTEXT_DIR = None
_USER_PATH = os.path.expanduser('~')
_DL4J_DIR = os.path.join(_USER_PATH, '.deeplearning4j')
mkdir(_DL4J_DIR)
_BASE_DIR = os.path.join(_DL4J_DIR, 'strumpf')
mkdir(_BASE_DIR)


def check(f):
    def wrapper(*args, **kwargs):
        if _CONTEXT_NAME is None:
            raise Exception(
                'Context not set! Set context using strumpf.set_context()')
        mkdir(_CONTEXT_DIR)
        return f(*args, **kwargs)
    return wrapper


def set_context(name):
    global _CONTEXT_NAME
    global _CONTEXT_DIR
    _CONTEXT_NAME = name
    if name is None:
        _CONTEXT_DIR = None
    else:
        _CONTEXT_DIR = os.path.join(_BASE_DIR, name)
        mkdir(_CONTEXT_DIR)


@check
def context():
    return _CONTEXT_NAME


@check
def get_dir():
    path = os.environ.get('STRUMPF_CLASS_PATH')
    if path is None:
        return _CONTEXT_DIR
    return path
