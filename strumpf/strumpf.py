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

from .utils import *
from .utils import _MY_DIR
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


_CONFIG_FILE = os.path.join(_MY_DIR, 'config.json')


# Default config
_CONFIG = {
    'dl4j_version': '1.0.0-SNAPSHOT',
    'dl4j_core': True,
    'datavec': True,
    'spark': True,
    'spark_version': '2',
    'scala_version': '2.11',
    'nd4j_backend': 'cpu',
    'validate_jars': True
}


def _is_sub_set(config1, config2):
    # check if config1 is a subset of config2
    # if config1 < config2, then we can use config2 jar
    # for config1 as well
    if config1['dl4j_version'] != config1['dl4j_version']:
        return False
    if config1['dl4j_core'] > config2['dl4j_core']:
        return False
    if config1['nd4j_backend'] != config2['nd4j_backend']:
        return False
    if config1['datavec']:
        if not config2['datavec']:
            return False
        if config1['spark'] > config2['spark']:
            return False
        if config1['spark_version'] != config2['spark_version']:
            return False
        if config1['scala_version'] != config2['scala_version']:
            return False
    return True


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


def validate_config(config=None):
    if config is None:
        config = _CONFIG
    valid_options = {
        'spark_version': ['1', '2'],
        'scala_version': ['2.10', '2.11'],
        'nd4j_backend': ['cpu', 'gpu']
    }
    for k, vs in valid_options.items():
        v = config.get(k)
        if v is None:
            raise KeyError('Key not found in config : {}.'.format(k))
        if v not in vs:
            raise ValueError(
                'Invalid value {} for key {} in config. Valid values are: {}.'.format(v, k, vs))

    # spark 2 does not work with scala 2.10
    if config['spark_version'] == '2' and config['scala_version'] == '2.10':
        raise ValueError(
            'Scala 2.10 does not work with spark 2. Set scala_version to 2.11 in pydl4j config. ')


def _get_context_from_config(config=None):
    if not config:
        config = _CONFIG
    # e.g pydl4j-1.0.0-SNAPSHOT-cpu-core-datavec-spark2-2.11

    context = 'pydl4j-{}'.format(config['dl4j_version'])
    context += '-' + config['nd4j_backend']
    if config['dl4j_core']:
        context += '-core'
    if config['datavec']:
        context += '-datavec'
        if config['spark']:
            spark_version = config['spark_version']
            scala_version = config['scala_version']
            context += '-spark' + spark_version + '-' + scala_version
    return context


def _get_config_from_context(context):
    config = {}
    backends = ['cpu', 'gpu']
    for b in backends:
        if '-' + b in context:
            config['nd4j_backend'] = b
            config['dl4j_version'] = context.split('-' + b)[0][len('pydl4j-'):]
            break
    config['dl4j_core'] = '-core' in context
    set_defs = False
    if '-datavec' in context:
        config['datavec'] = True
        if '-spark' in context:
            config['spark'] = True
            sp_sc_ver = context.split('-spark')[1]
            sp_ver, sc_ver = sp_sc_ver.split('-')
            config['spark_version'] = sp_ver
            config['scala_version'] = sc_ver
        else:
            config['spark'] = False
            set_defs = True
    else:
        config['datavec'] = False
        set_defs = True
    if set_defs:
        config['spark_version'] = '2'
        config['scala_version'] = '2.11'
    validate_config(config)
    return config


set_context(_get_context_from_config())


def _get_all_contexts():
    c = os.listdir(_MY_DIR)
    return [x for x in c if x.startswith('strumpf')]