import os, uuid, sys
from azure.storage.blob import BlockBlobService, PublicAccess
from azure.storage.common import CloudStorageAccount

import json
from .core import decompress_file, mkdir REF, ZIP, Strump

class Service:
    # TODO: proper azure logging?

    def __init__(self, account_name, account_key, container_name):
        self.account_name = account_name
        self.account_key = account_key
        self.blob_service = BlockBlobService(account_name, account_key)
        self.container_name = container_name
        self.blobs = self.get_all_blob_names()
        self.strump = None

    def _create_container(self, container_name):
        self.blob_service.create_container(container_name)
        self.blob_service.set_container_acl(container_name, public_access=PublicAccess.Container)

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

    def download_blob(self, file_name, local_path):

        # download zipped version and file reference
        ref_name = file_name + REF
        file_name = file_name + ZIP

        if '/' in file_name:
            parts = file_name.split('/')[:-1]
            temp_path = local_path
            for part in parts:
                temp_path = os.path.join(temp_path, part)
                # Note: Azure automatically creates subfolders, Python doesn't. 
                # we need to carefully create them first.
                mkdir(temp_path)
        
        ref_location = os.path.join(local_path, ref_name)
        download_location = os.path.join(local_path, file_name)

        download_again = True
        if os.path.isfile(ref_location) and os.path.isfile(download_location):
            print('>>> Found local reference and file in cache, compare to original reference.')
            dup_ref = json.load(ref_location)
            if not self.strump:
                self.strump = Strump()
            local_resource_path = self.strump.get_local_resource_dir()
            original_ref_location = os.path.join(local_resource_path, ref_name)
            original_ref = json.load(original_ref_location)
            if original_ref == dup_ref:
                download_again = False

        if download_again:
            print('>>> Downloading blob {}'.format(file_name))
            self.blob_service.get_blob_to_path(self.container_name, file_name, download_location)
            # Unzip file and delete compressed version
            decompress_file(download_location, clean=True)
            # Update file reference as well
            self.blob_service.get_blob_to_path(self.container_name, ref_name, ref_location)
        else:
            print('>>> Resource file and reference already up to date, no download necessary.')


    def bulk_download(self, local_path):
        blobs = self.get_all_blob_names()
        for blob in blobs:
            self.download_blob(blob, local_path)     
