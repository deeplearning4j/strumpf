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
import sys
reload(sys)
sys.setdefaultencoding("ISO-8859-1")

if sys.version_info[0] == 2:
    input = raw_input

from .utils import _BASE_DIR
from .storage import Service

import platform
import os
import warnings
import os
import json
import gzip
import hashlib
from shutil import copyfile


def compute_and_store_hash(file_name):
    f_hash = hash_bytestr_iter(file_as_blockiter(open(file_name, 'rb')), hashlib.sha256())
    gzip_hash = hash_bytestr_iter(file_as_blockiter(open(file_name + '.gzx', 'rb')), hashlib.sha256())
    hashes = {
        file_name + '_hash': f_hash.encode('utf-8'), 
        file_name + '_compressed_hash': gzip_hash.encode('utf-8')
        }
    with open(file_name + '.resource_reference', 'w') as ref:
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


def to_bool(string):
    if type(string) is bool:
        return string
    return True if string[0] in ["Y", "y"] else False


class Strumpf:
    
    def __init__(self):
        self.stage_file = os.path.join(_BASE_DIR, 'stage.txt')
        self.stage_data = set()
        self.config_file = os.path.join(_BASE_DIR, 'config.json')
        self.config = {
            'azure_account_name': 'dl4jtestresources',
            'file_size_limit_in_mb': '2',
            'container_name': 'resources',
            'cache_directory': _BASE_DIR + '/src'
        }
        self.service = None

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

    def set_service(self, service):
        self.service = service

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
        return float(limit) * 1000 * 1000

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

    def get_total_file_size(self):
        local_dir = self.get_local_resource_dir()
        sizes = []
        for path, _, filenames in os.walk(local_dir):
            for name in filenames:
                full_path = os.path.join(path, name)
                sizes.append(os.path.getsize(full_path))
        return  sum(sizes), len(sizes)

    def get_large_files(self, path=None):
        large_files = []
        local_dir = self.get_local_resource_dir()
        if path:
            local_dir = path
        
        limit = self.get_limit_in_bytes()
        for path, _, filenames in os.walk(local_dir):
            for name in filenames:
                full_path = os.path.join(path, name)
                size = os.path.getsize(full_path)
                if size > limit:
                    large_files.append((full_path, size))
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


    def add_file(self, full_file_path):
        local_dir = self.get_local_resource_dir()
        self.stage_data = self.stage_data | set([full_file_path])
        self._write_stage_files()


    def add_path(self, path):
        path = os.path.abspath(path)
        large_files = self.get_large_files(path)
        large_files = [f[0] for f in large_files]
        self.stage_data = self.stage_data | set(large_files)
        self._write_stage_files()


    def compress_staged_files(self):
        files = self.get_staged_files()
        for f in files:
            with open(f) as source, gzip.open(f + '.gzx', 'wb') as dest:        
                dest.write(source.read())

    def decompress_file(self, file_name, clean=True):
        if not file_name.endswith('.gzx'):
            raise ValueError('File name is expected to have ".gzx" signature.')
        with open(file_name.strip('.gzx'), 'wb') as dest, gzip.open(file_name, 'rb') as source:
            dest.write(source.read())

    def compute_and_store_hashes(self):
        files = self.get_staged_files()
        for f in files:
            compute_and_store_hash(f)

    def service_from_config(self):
        name = self.config['azure_account_name']
        key = self.config['azure_account_key']
        container = self.config['container_name']
        return Service(name, key, container)

    def upload_compressed_files(self):
        num_staged_files = len(self.get_staged_files())
        container = self.config['container_name']
        print('>>> Starting upload to Azure blob storage')
        print('>>> A total of {} large files will be uploaded to container "{}"'.format(num_staged_files, container))
        if self.service is None:
            self.service = self.service_from_config()

        blobs = self.service.get_all_blob_names()
        files = self.get_staged_files()
        local_dir = self.get_local_resource_dir()

        for path, _, file_names in os.walk(local_dir):
            for name in file_names:
                if name.endswith('.gzx'):
                    full_path = os.path.join(path, name)
                    upload = True
                    # azure auto-generates intermediate paths
                    name = full_path.replace(local_dir + '/', '')
                    if name in blobs:
                        confirm = input("File {} already available on Azure,".format(name) + \
                                        "do you want to override it? (default 'n') [y/n]: ") or 'yes'
                        upload = to_bool(confirm)
                    if upload:
                        print('   >>> uploading file {}'.format(full_path))
                        name = full_path.replace(local_dir + '/', '')
                        self.service.upload_blob(name, full_path)
        print('>>> Upload finished')
        
    def cache_and_delete(self):
        staged = self.get_staged_files()
        local_dir = self.get_local_resource_dir()
        cache_dir = self.config['cache_directory']
        if not os.path.exists(cache_dir):
                os.mkdir(cache_dir)
        for source_dir, dirs, files in os.walk(local_dir):
            dest_dir = source_dir.replace(local_dir, cache_dir)
            if not os.path.exists(dest_dir):
                os.mkdir(dest_dir)
            for file_name in files:
                src_file = os.path.join(source_dir, file_name)
                dst_file = os.path.join(dest_dir, file_name)
                if src_file in staged:
                    os.rename(src_file, dst_file)
                    os.remove(src_file + '.gzx')
                    copyfile(src_file + ".resource_reference", dst_file + ".resource_reference")

    def clear_staging(self):
        self.set_staged_files([])
