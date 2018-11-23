import os, uuid, sys
from azure.storage.blob import BlockBlobService, PublicAccess
from azure.storage.common import CloudStorageAccount


class Service:

    def __init__(self, account_name, account_key, container_name):
        self.account_name = account_name
        self.account_key = account_key
        self.blob_service = BlockBlobService(account_name, account_key)
        self.container_name = container_name

    def _create_container(self, container_name):
        self.blob_service.create_container(container_name)
        self.blob_service.set_container_acl(container_name, public_access=PublicAccess.Container)

    def _delete_container(self, container_name):
        # danger zone
        self.blob_service.delete_container(container_name)

    def upload_blob(self, file_name, full_local_file_path):
        self.blob_service.create_blob_from_path(
            self.container_name, file_name, full_local_file_path)

    def list_all_blobs(self):
        generator = self.blob_service.list_blobs(self.container_name)
        for blob in generator:
            print("\t File name: " + blob.name)

    def get_all_blob_names(self):
        blob_gen = self.blob_service.list_blobs(self.container_name)
        return [blob.name for blob in blob_gen]

    def download_blob(self, file_name, local_path):
        download_location = os.path.join(local_path, file_name)
        self.blob_service.get_blob_to_path(self.container_name, file_name, download_location)

    def bulk_download(self, local_path):
        blobs = self.get_all_blobs()
        for blob in blobs:
            self.download_blob(blob, local_path)     
