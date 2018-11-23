#!/usr/bin python
# -*- coding: utf-8 -*-
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

import argparse
import json
import os
import sys
import pkg_resources
import argcomplete
import traceback
import subprocess
import click
from click.exceptions import ClickException
from dateutil import parser

from . import core
from . import storage
from .utils import set_context

if sys.version_info[0] == 2:
    input = raw_input


def to_bool(string):
    if type(string) is bool:
        return string
    return True if string[0] in ["Y", "y"] else False


class CLI(object):

    def __init__(self):
        self.var_args = None
        self.command = None

        self.strumpf = core.Strumpf()
        self.config = self.strumpf.get_config()
        self.default_account_name = self.config['azure_account_name']
        self.default_file_size_in_mb = self.config['file_size_limit_in_mb']
        self.default_container_name = self.config['container_name']

    def command_dispatcher(self, args=None):
        desc = ('Strumpf, Skymind Test Resource Upload Management for Paunchy Files.\n')
        parser = argparse.ArgumentParser(description=desc)
        parser.add_argument(
            '-v', '--version', action='version',
            version=pkg_resources.get_distribution("strumpf").version,
            help='Print strumpf version'
        )

        subparsers = parser.add_subparsers(title='subcommands', dest='command')
        subparsers.add_parser('configure', help='Configure strumpf')
        subparsers.add_parser('status', help='Get strumpf status')
        file_add_parser = subparsers.add_parser('add', help='Add files to strumpf tracking system')
        file_add_parser.add_argument('-p', '--path', help='Path or file to add to upload.')

        subparsers.add_parser('upload', help='Upload files to remote source')

        download_parser = subparsers.add_parser('download', help='Download file from remote source')
        download_parser.add_argument('-f', '--file', help='File to download.')


        argcomplete.autocomplete(parser)
        args = parser.parse_args(args)
        self.var_args = vars(args)

        if not args.command:
            parser.print_help()
            return

        self.command = args.command

        if self.command == 'configure':
            self.configure()
            return

        if self.command == 'status':
            self.status()
            return

        if self.command == 'add':
            self.add(self.var_args['path'])
            return

        if self.command == 'upload':
            self.upload()
            return

        if self.command == 'download':
            self.download(self.var_args['file'])
            return
        
        if self.command == 'bulk_download':
            self.bulk_download()

        # TODO: strumpf reset

    def configure(self):

        click.echo(click.style(u"""\n███████╗████████╗██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗
██╔════╝╚══██╔══╝██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝
███████╗   ██║   ██████╔╝██║   ██║██╔████╔██║██████╔╝█████╗  
╚════██║   ██║   ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  
███████║   ██║   ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║     ██║     
╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝   \n""", fg='blue', bold=True))

        click.echo(click.style("strumpf", bold=True) +
                   " is Skymind's test resource management tool for exceedingly large files!\n")

        # Storage account name
        account_name = input("Specify tour Azure storage account name (default '%s'): " %
                             self.default_account_name) or self.default_account_name

        # Storage account key
        account_key = input("Please specify the respective account key: ")

        # Container name
        container_name = input("Which blob storage container should be used (default '%s'): " %
                             self.default_container_name) or self.default_container_name

        # File size limit
        file_limit = input("Strumpf uploads large files to Azure instead of checking them into git," +
                            "from which file size in MB on should we upload your files (default '%s' MB): " %
                             self.default_file_size_in_mb) or self.default_file_size_in_mb

        # Local resource folder
        local_resource_folder = input("Please specify the full path to the resource folder you want to track: ")

        cli_out = {
            'azure_account_name': account_name,
            'azure_account_key': account_key,
            'file_size_limit_in_mb': file_limit,
            'container_name': container_name,
            'local_resource_folder': local_resource_folder
        }

        self.strumpf.validate_config(cli_out)
        self.service = storage.Service(account_name, account_key, container_name)

        formatted_json = json.dumps(cli_out, sort_keys=False, indent=2)

        click.echo("\nThis is your current settings file " +
                   click.style("config.json", bold=True) + ":\n")
        click.echo(click.style(formatted_json, fg="green", bold=True))

        confirm = input(
            "\nDoes this look good? (default 'y') [y/n]: ") or 'yes'
        if not to_bool(confirm):
            click.echo(
                "" + click.style("Please initialize strumpf once again", fg="red", bold=True))
            return

        self.strumpf.set_config(cli_out)
        set_context(self.strumpf.get_context_from_config())


    def status(self):
        large_files = self.strumpf.get_large_files()
        tracked_files = self.strumpf.get_tracked_files()
        staged_files = self.strumpf.get_staged_files()

        modified_files = [f for f in large_files if f[0] in tracked_files]
        untracked_files = [f for f in large_files if f[0] not in tracked_files]
        modified_unstaged = [f for f in modified_files if f[0] not in staged_files]

        if large_files:
            if staged_files:
                click.echo('\n Changes to be uploaded:')
                click.echo(' (use "strumpf reset <file>..." to unstage files)\n')
                for stage in staged_files:
                    click.echo('' + click.style('        modified:    ' + stage, fg="green", bold=False))
                click.echo('\n')

            if modified_unstaged:
                click.echo('\n Changes not staged for upload:')
                click.echo(' (use "strumpf add <file>..." to update files)\n')
                for mod in modified_files:
                    click.echo('' + click.style('        modified:    ' + mod[0] + 
                               '  (file size: ' + str(int(mod[1])/1000000) + ' mb)', fg="red", bold=False))
                click.echo('\n')
            if untracked_files:
                click.echo(' Untracked large files:')
                click.echo(' (use "strumpf add <file>..." to include in what will be committed)\n')
                for untracked in untracked_files:
                    click.echo("        " + click.style(untracked[0] + 
                               '      (file size: ' + str(int(untracked[1])/1000000) + ' mb)', fg="red", bold=False))
                click.echo('\n')
        else:
            click.echo(' No large files available for upload')

        untracked_file_size = sum(s[1] for s in large_files)
        total_file_size = self.strumpf.get_total_file_size()
        size_after_upload = total_file_size - untracked_file_size
        space_saved = round(untracked_file_size / total_file_size * 100)

        click.echo("Total directory size after uploading all large files {} mb ({} %% saved)".format(size_after_upload, space_saved))

    
    def add(self, path):
        if self.strumpf.is_file(path):
            self.strumpf.add_file(path)
        else:
            self.strumpf.add_path(path)

    def upload(self):
        self.strumpf.compress_staged_files()
        self.strumpf.compute_and_store_hashes()
        self.strumpf.upload_compressed_files()
        self.strumpf.cache_and_delete()
        self.strumpf.clear_staging()

    def download(self, file_name):
        self.service.download_blob(file_name, "FOO")
        # TODO: download individual files
        # if hash already exists in cache, don't download again
        # if hash does not exist of deviates, download and re-compute hash
        pass
    
    def bulk_download(self):
        # TODO: bulk download all remote resources and update hashes
        # i.e. force update
        pass
        

def handle():
    try:
        cli = CLI()
        sys.exit(cli.command_dispatcher())
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        click.echo(click.style("Error: ", fg='red', bold=True))
        traceback.print_exc(e)
        sys.exit()


if __name__ == '__main__':
    handle()
