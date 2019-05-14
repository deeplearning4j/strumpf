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

from .utils import _BASE_DIR, get_dir

import platform
import os
import warnings
import os
import json
import gzip
import hashlib
import shutil
import sys
from azure.storage.blob import BlockBlobService, PublicAccess
from azure.storage.common import CloudStorageAccount


REF = ".resource_reference"
ZIP = ".gzx"


def mkdir(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)


def decompress_file(file_name, clean=True):
    if not file_name.endswith(ZIP):
        raise ValueError(
            'File name is expected to have "{}" signature.'.format(ZIP))

    with open(file_name.strip(ZIP), 'wb') as dest, gzip.open(file_name, 'rb') as source:
        dest.write(source.read())
    if clean:
        os.remove(file_name)


def get_reference_and_version(ref_file_name):
    current_version = 0
    ref = {}
    if os.path.exists(ref_file_name):
        with open(ref_file_name, 'r') as ref_file:
            ref = json.loads(ref_file.read())
            current_version = ref['current_version']
    return ref, current_version


def hash_bytestr_iter(bytesiter, hasher, ashexstr=True):
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
            'file_size_limit_in_mb': '1',
            'container_name': 'resources'
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

    def load_config(self, config=None):
        if not config:
            config = self.config_file
        with open(config, 'r') as f:
            return json.load(f)

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
        self._write_config(os.path.join(
            _BASE_DIR, '{}.json'.format(self.get_context_from_config())))

    def get_config(self):
        return self.config

    def get_limit_in_bytes(self):
        limit = self.config['file_size_limit_in_mb']
        return float(limit) * 1024 * 1024

    def get_local_resource_dir(self):
        return self.config['local_resource_folder']

    def get_cache_dir(self):
        return self.config['cache_directory']

    def get_context_from_config(self):
        if 'project_name' in self.config.keys():
            return self.config['project_name']
        else:
            raise Exception(
                "No project name found. Did you run 'strumpf configure' before?")

    def validate_config(self, config=None):
        if config is None:
            config = self.config

    def get_all_contexts(self):
        base_files = os.listdir(_BASE_DIR)
        json_files = [x for x in base_files if x.endswith(".json")]
        json_files.remove('config.json')
        return [j.replace('.json', '') for j in json_files]

    def get_total_file_size(self):
        local_dir = self.get_local_resource_dir()
        sizes = []
        for path, _, filenames in os.walk(local_dir):
            for name in filenames:
                full_path = os.path.join(path, name)
                sizes.append(os.path.getsize(full_path))
        return sum(sizes), len(sizes)

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
                if full_path.endswith(REF):
                    original_file = full_path.replace(REF, "")
                    tracked_files.append(original_file)
        return tracked_files

    def full_path(self, path):
        local_dir = self.get_local_resource_dir()
        if local_dir not in path:
            path = os.path.join(local_dir, path)
        return path

    def is_file(self, path):
        full_path = self.full_path(path)
        return os.path.isfile(path)

    def add_file(self, file_path):
        local_dir = self.get_local_resource_dir()
        full_file_path = self.full_path(file_path)
        if not os.path.isfile(full_file_path):
            raise Exception("Could not find local resource {} in resource folder {}, aborting".format(
                full_file_path, local_dir))
        limit = self.get_limit_in_bytes()
        size = os.path.getsize(full_file_path)
        full_file_path = full_file_path.replace("\\","/")
        if size > limit:
            self.stage_data = self.stage_data | set([full_file_path])
            self._write_stage_files()

    def add_path(self, path):
        path = os.path.abspath(path)
        path = path.replace("\\","/")
        large_files = self.get_large_files(path)
        large_files = [f[0] for f in large_files]
        self.stage_data = self.stage_data | set(large_files)
        self._write_stage_files()

    def compress_staged_files(self):
        files = self.get_staged_files()
        for f in files:
            with open(f, 'rb') as source, gzip.open(f + ZIP, 'wb') as dest:
                dest.write(source.read())

    def compute_and_store_hashes(self):
        files = self.get_staged_files()
        for file_name in files:
            self.compute_and_store_hash(file_name)

    def compute_and_store_hash(self, file_name):
        ref, version = get_reference_and_version(file_name + REF)
        new_version = version + 1
        ref['current_version'] = new_version

        f_hash = hash_bytestr_iter(file_as_blockiter(
            open(file_name, 'rb')), hashlib.sha256())
        gzip_hash = hash_bytestr_iter(file_as_blockiter(
            open(file_name + ZIP, 'rb')), hashlib.sha256())
        local_dir = self.get_local_resource_dir()
        rel_name = os.path.relpath(file_name, local_dir)
        rel_name = rel_name.replace("\\","/")

        azure_base = 'https://{}.blob.core.windows.net/{}'.format(self.config['azure_account_name'], self.config['container_name'])
        full_remote_path = os.path.join(azure_base, rel_name)
        full_remote_path += ZIP + '.v' + str(new_version)
        full_remote_path = full_remote_path.replace("\\","/")


        hashes = {
            'full_remote_path': full_remote_path,
            rel_name + '_hash': f_hash,
            rel_name + '_compressed_hash': gzip_hash
        }
        version_hash = {'v' + str(new_version): hashes}
        ref.update(version_hash)

        with open(file_name + REF, 'w') as ref_file:
            json.dump(ref, ref_file)

    def service_from_config(self):
        name = self.config['azure_account_name']
        key = self.config['azure_account_key']
        container = self.config['container_name']
        try:
            service = Service(name, key, container)
        except Exception:
            raise Exception("Could not establish Azure connection. Are your credentials valid? Run 'strumpf configure' again with proper credentials.")
        return Service(name, key, container)

    def upload_compressed_files(self):
        num_staged_files = len(self.get_staged_files())
        container = self.config['container_name']
        print('>>> Starting upload to Azure blob storage')
        print('>>> A total of {} large files will be uploaded to container "{}"'.format(
            num_staged_files, container))

        service = self.service_from_config()

        blobs = service.get_all_blob_names()
        files = self.get_staged_files()
        local_dir = self.get_local_resource_dir()

        for path, _, file_names in os.walk(local_dir):
            for name in file_names:
                if name.endswith(ZIP):
                    full_path = os.path.join(path, name)
                    ref_path = full_path.replace(ZIP, REF)
                    ref, version = get_reference_and_version(ref_path)

                    upload = True
                    # azure auto-generates intermediate paths, strip the local dir
                    name = os.path.relpath(full_path, local_dir)
                    versioned_name = name + '.v' + str(version)

                    if versioned_name in blobs:
                        confirm = input("File {} already available on Azure,".format(versioned_name) +
                                        "are you sure you want to override it? [y/n]: ") or 'yes'
                        upload = to_bool(confirm)
                    if upload:
                        print('   >>> uploading file {}, version {}'.format(
                            full_path, version))
                        service.upload_blob(versioned_name, full_path)
                        # upload reference as well
                        service.upload_blob(name.replace(
                            ZIP, REF), full_path.replace(ZIP, REF))
        print('>>> Upload finished')

    def roll_back(self):
        staged = self.get_staged_files()
        local_dir = self.get_local_resource_dir()
        cache_dir = self.get_cache_dir()
        mkdir(cache_dir)
        for source_dir, dirs, files in os.walk(local_dir):
            for file_name in files:
                src_file = os.path.join(source_dir, file_name)
                dst_file = os.path.join(dest_dir, file_name)
                if src_file in staged:
                    # remove zipped files
                    os.remove(src_file + ZIP)
                    os.remove(src_file + REF)

    def cache_and_delete(self):
        staged = self.get_staged_files()
        local_dir = self.get_local_resource_dir()
        cache_dir = self.get_cache_dir()
        mkdir(cache_dir)
        for source_dir, dirs, files in os.walk(local_dir):
            dest_dir = source_dir.replace(local_dir, cache_dir)
            mkdir(dest_dir)
            for file_name in files:
                src_file = os.path.join(source_dir, file_name)
                dst_file = os.path.join(dest_dir, file_name)
                if src_file in staged:
                    # move original file to cache
                    os.rename(src_file, dst_file)
                    # remove zipped files
                    os.remove(src_file + ZIP)
                    # copy resource references to cache
                    shutil.copyfile(src_file + REF, dst_file + REF)

    def clear_staging(self):
        empty_staging = []
        self.set_staged_files(empty_staging)

    def _clear_cache(self):
        cache_dir = self.get_cache_dir()
        for file_name in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, file_name)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)


class Service:

    def __init__(self, account_name, account_key, container_name):
        self.account_name = account_name
        self.account_key = account_key
        self.blob_service = BlockBlobService(account_name, account_key)
        self.container_name = container_name
        self.blobs = self.get_all_blob_names()
        self.strumpf = None

    def _create_container(self, container_name):
        self.blob_service.create_container(container_name)
        self.blob_service.set_container_acl(
            container_name, public_access=PublicAccess.Container)

    def _delete_container(self, container_name):
        # danger zone
        self.blob_service.delete_container(container_name)

    def upload_blob(self, file_name, full_local_file_path):
        self.blob_service.create_blob_from_path(
            self.container_name, file_name, full_local_file_path)
        self.blobs.append(file_name)

    def list_all_blobs(self):
        generator = self.blob_service.list_blobs(self.container_name)
        for blob in generator:
            print("\t File name: " + blob.name)

    def get_all_blob_names(self):
        blob_gen = self.blob_service.list_blobs(self.container_name)
        return [blob.name for blob in blob_gen]

    def download_blob(self, original_file_name, local_path):

        # download zipped version and file reference
        ref_name = original_file_name + REF
        file_name = original_file_name + ZIP

        if not self.strumpf:
            self.strumpf = Strumpf()
        local_res_dir = self.strumpf.get_local_resource_dir()
        ref_location = os.path.join(local_res_dir, ref_name)
        download_location = os.path.join(local_path, file_name)
        ref, version = get_reference_and_version(ref_location)
        str_version = 'v' + str(version)

        if os.sep in file_name:
            parts = file_name.split(os.sep)[:-1]
            temp_path = local_path
            for part in parts:
                temp_path = os.path.join(temp_path, part)
                # Note: Azure automatically creates subfolders, Python doesn't.
                # we need to carefully create them first.
                mkdir(temp_path)

        download_again = True
        if os.path.isfile(ref_location) and os.path.isfile(download_location.strip(ZIP)):
            print(
                '>>> Found local reference and file in cache, compare to original reference.')
            with open(ref_location, 'r') as ref_file:
                dup_ref = json.loads(ref_file.read())
            local_resource_path = self.strumpf.get_local_resource_dir()
            original_ref_location = os.path.join(local_resource_path, ref_name)
            with open(original_ref_location, 'r') as original_file:
                original_ref = json.loads(original_file.read())
            if original_ref[str_version] == dup_ref[str_version]:
                download_again = False

        if download_again:
            print('>>> Downloading blob {}, version {}'.format(file_name, version))
            self.blob_service.get_blob_to_path(
                # download correct version
                self.container_name, file_name + '.' + str_version, download_location)
            # Unzip file and delete compressed version
            decompress_file(download_location, clean=True)
            # Update file reference as well
            self.blob_service.get_blob_to_path(
                self.container_name, ref_name, ref_location)
        else:
            print(
                '>>> Resource file and reference already up to date, no download necessary.')

        return download_again, version

    def bulk_download(self, local_path):
        blobs = self.get_all_blob_names()
        for blob in blobs:
            self.download_blob(blob, local_path)
