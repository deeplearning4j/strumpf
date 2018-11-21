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
import json
import gzip
import hashlib


def target_dir():
    return get_dir()


def compute_and_store_hash(file_name):
    f_hash = hash_bytestr_iter(file_as_blockiter(open(file_name, 'rb')), hashlib.sha256())
    gzip_hash = hash_bytestr_iter(file_as_blockiter(open(file_name + '.gz', 'rb')), hashlib.sha256())
    hashes = {file_name + '_hash': f_hash, file_name + '_compressed_hash': gzip_hash}
    with open(file_name + '.resource_reference') as ref:
        json.dump(hashes, ref)


def hash_bytestr_iter(bytesiter, hasher, ashexstr=False):
    for block in bytesiter:
        hasher.update(block)
    return (hasher.hexdigest() if ashexstr else hasher.digest())


def file_as_blockiter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)


class Strumpf:
    
    def __init__(self):
        self.stage_file = os.path.join(_BASE_DIR, 'stage.txt')
        self.stage_data = set()
        self.config_file = os.path.join(_BASE_DIR, 'config.json')
        self.config = {
            'azure_account_name': 'dl4jtestresources',
            'file_size_limit_in_mb': '2',
            'container_name': 'resources',
        }

        if os.path.isfile(self.stage_file):
            with open(self.stage_file, 'r') as f:
                staged_files = f.readlines()
                staged_files = set([x.strip() for x in staged_files])
                self.stage_data = self.stage_data | staged_files
        else:
            self._write_stage_files()

        if os.path.isfile(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config.update(json.load(f))
        else:
            self._write_config()


    def _write_config(self, filepath=None):
        if not filepath:
            filepath = self.config_file
        with open(filepath, 'w') as f:
            json.dump(self.config, f)


    def _write_stage_files(self, filepath=None):
        if not filepath:
            filepath = self.stage_file
        
        f = open(filepath, 'w')
        f.close()
        with open(filepath, 'w') as f:
            f.write("\n".join(self.stage_data))


    def set_staged_files(self, files):
        self.stage_data = set(files)
        self._write_stage_files()


    def get_staged_files(self):
        return self.stage_data


    def set_config(self, config):
        self.config.update(config)
        self._write_config()


    def get_config(self):
        return self.config

    def get_limit_in_bytes(self):
        limit = self.config['file_size_limit_in_mb']
        return int(limit) * 1000

    def get_local_resource_dir(self):
        return self.config['local_resource_folder']

    def get_context_from_config(self):
        local_resource_folder = self.config['local_resource_folder']
        resource_name = local_resource_folder.split('/')[-1]
        return resource_name


    def validate_config(self, config=None):
        if config is None:
            config = self.config

    def _get_all_contexts(self):
        c = os.listdir(_BASE_DIR)
        return [x for x in c if x.startswith('strumpf')]


    def get_large_files(self, relative_path=None):
        large_files = []
        local_dir = self.get_local_resource_dir()
        if relative_path:
            local_dir = os.path.join(local_dir, relative_path)
        
        limit = self.get_limit_in_bytes()
        for path, _, filenames in os.walk(local_dir):
            for name in filenames:
                full_path = os.path.join(path, name)
                if  os.path.getsize(full_path) > limit:
                    large_files.append(full_path)
        return large_files


    def get_tracked_files(self, relative_path=None):
        tracked_files = []
        local_dir = self.get_local_resource_dir()
        if relative_path:
            local_dir = os.path.join(local_dir, relative_path)
        for path, _, filenames in os.walk(local_dir):
            for name in filenames:
                full_path = os.path.join(path, name)
                if full_path.endswith(".resource_reference"):
                    original_file = full_path.replace(".resource_reference", "")
                    tracked_files.append(original_file)
        return tracked_files


    def is_file(self, path):
        local_dir = self.get_local_resource_dir()
        full_path = os.path.join(local_dir, path)
        return os.path.isfile(full_path)


    def add_file(self, filepath):
        local_dir = self.get_local_resource_dir()
        self.stage_data = self.stage_data | set([os.path.join(local_dir, filepath)])
        self._write_stage_files()


    def add_path(self, path):
        large_files = self.get_large_files(path)
        self.stage_data = self.stage_data | set(large_files)


    def compress_staged_files(self):
        files = self.get_staged_files()
        for f in files:
            with open(f) as source, gzip.open(f + '.gz', 'wb') as dest:        
                dest.writelines(source)


    def compute_and_store_hashes(self):
        files = self.get_staged_files()
        for f in files:
            compute_and_store_hash(f)

    def upload_compressed_files(self):
        pass
    
    def cache_and_delete(self):
        pass

    def clear_staging(self):
        pass
