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
from .utils import set_context, _BASE_DIR

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
        subparsers.add_parser('configure', help='Configure strumpf.')
        subparsers.add_parser('status', help='Get strumpf status.')
        file_add_parser = subparsers.add_parser(
            'add', help='Add files to strumpf tracking system.')
        file_add_parser.add_argument(
            'path', type=str, nargs='+', help='Path or file to add to upload.')

        subparsers.add_parser('upload', help='Upload files to remote source.')

        subparsers.add_parser(
            'bulk_download', help='Download all remote files')
        download_parser = subparsers.add_parser(
            'download', help='Download file from remote source.')
        download_parser.add_argument('-f', '--file', help='File to download.')

        subparsers.add_parser('reset', help='Reset previously staged files.')
        subparsers.add_parser('blobs', help='List all relevant Azure blobs.')
        subparsers.add_parser(
            'projects', help='List all projects tracked by Strumpf.')

        project_parser = subparsers.add_parser(
            'set_project', help='Set a project tracked by Strumpf as default.')
        project_parser.add_argument(
            'project', type=str, nargs='?', help='The project you want to set.')

        argcomplete.autocomplete(parser)
        args = parser.parse_args(args)
        self.var_args = vars(args)

        if not args.command:
            parser.print_help()
            return

        self.command = args.command

        if self.command != 'configure' and 'project_name' not in self.config.keys():
            raise Exception(
                "Can't run this command.\nNo project name found. Did you run 'strumpf configure' before?")

        if self.command == 'configure':
            self.configure()
            return

        if self.command == 'status':
            self.status()
            return

        if self.command == 'add':
            paths = self.var_args['path']
            self.add(paths)
            return

        if self.command == 'upload':
            self.upload()
            return

        if self.command == 'download':
            self.download(self.var_args['file'])
            return

        if self.command == 'bulk_download':
            self.bulk_download()

        if self.command == 'reset':
            self.reset()

        if self.command == 'blobs':
            self.blobs()

        if self.command == 'projects':
            self.projects()

        if self.command == 'set_project':
            project = self.var_args['project']
            self.set_project(project)
            return

    def configure(self):

        click.echo(click.style(u"""\n███████╗████████╗██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗
██╔════╝╚══██╔══╝██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝
███████╗   ██║   ██████╔╝██║   ██║██╔████╔██║██████╔╝█████╗  
╚════██║   ██║   ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  
███████║   ██║   ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║     ██║     
╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝   \n""", fg='blue', bold=True))

        click.echo(click.style("strumpf", bold=True) +
                   " is Skymind's test resource management tool for exceedingly large files!\n")

        project_name = input(
            "What's the name of this project? You can address existing projects by name: ")

        account_name = input("Specify tour Azure storage account name (default '%s'): " %
                             self.default_account_name) or self.default_account_name

        account_key = input("Please specify the respective account key: ")

        container_name = input("Which blob storage container should be used (default '%s'): " %
                               self.default_container_name) or self.default_container_name

        file_limit = input("Strumpf uploads large files to Azure instead of checking them into git," +
                           "from which file size in MB on should we upload your files (default '%s' MB): " %
                           self.default_file_size_in_mb) or self.default_file_size_in_mb

        local_resource_folder = input(
            "Please specify the full path to the resource folder you want to track: ")

        cli_out = {
            'project_name': project_name,
            'azure_account_name': account_name,
            'azure_account_key': account_key,
            'file_size_limit_in_mb': file_limit,
            'container_name': container_name,
            'local_resource_folder': local_resource_folder,
            'cache_directory': os.path.join(_BASE_DIR, project_name)
        }
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

        click.echo("Running validation...")
        self.strumpf.set_config(cli_out)
        if not os.path.isdir(local_resource_folder):
            raise Exception("The provided resource folder {} can not be found on your system. Please run 'strumpf configure' again.".format(local_resource_folder))
        service = self.strumpf.service_from_config()
        set_context(self.strumpf.get_context_from_config())
        click.echo("Validation passed.")

    def status(self):
        click.echo('>>> Working on project {}'.format(
            (self.strumpf.get_context_from_config())))

        large_files = self.strumpf.get_large_files()
        tracked_files = self.strumpf.get_tracked_files()
        staged_files = self.strumpf.get_staged_files()

        modified_files = [f for f in large_files if f[0] in tracked_files]
        untracked_files = [f for f in large_files if (
            f[0] not in staged_files and f[0 not in tracked_files])]
        modified_unstaged = [
            f for f in modified_files if f[0] not in staged_files]

        if large_files:
            if staged_files:
                click.echo('\n Changes to be uploaded:')
                click.echo(
                    ' (use "strumpf reset" to unstage all added files)\n')
                for stage in staged_files:
                    click.echo(
                        '' + click.style('        modified:    ' + stage, fg="green", bold=False))
                click.echo('\n')

            if modified_unstaged:
                click.echo('\n Changes not staged for upload:')
                click.echo(' (use "strumpf add <file>..." to update files)\n')
                for mod in modified_files:
                    click.echo('' + click.style('        modified:    ' + mod[0] +
                                                '  (file size: ' + str(int(mod[1])/(1024*1024)) + ' mb)', fg="red", bold=False))
                click.echo('\n')
            if untracked_files:
                click.echo(' Untracked large files:')
                click.echo(
                    ' (use "strumpf add <file>..." to include in what will be committed)\n')
                for untracked in untracked_files:
                    click.echo("        " + click.style(untracked[0] +
                                                        '      (file size: ' + str(int(untracked[1])/(1024*1024)) + ' mb)', fg="red", bold=False))
                click.echo('\n')
        else:
            click.echo(' No large files available for upload')

        large_file_size = sum(s[1] for s in large_files) / (1024*1024)
        total_file_size, total_files = self.strumpf.get_total_file_size()
        total_file_size /= 1024*1024
        size_after_upload = round(total_file_size - large_file_size)
        space_saved = round(large_file_size / total_file_size *
                            100) if total_file_size > 0 else 0
        files_left = total_files - len(large_files)

        click.echo("Total directory size after uploading all large files {} mb ({}% saved)".format(
            size_after_upload, space_saved))
        click.echo("Total number of files left after upload: {}, number of files to upload {}".format(
            files_left, len(large_files)))

    def add(self, path_list):
        for path in path_list:
            if self.strumpf.is_file(path):
                self.strumpf.add_file(path)
            else:
                self.strumpf.add_path(path)

    def upload(self):
        aborting = False
        print('>>> Compressing staged files')
        self.strumpf.compress_staged_files()
        print('>>> Computing SHA256 hashes for large files')
        self.strumpf.compute_and_store_hashes()
        print('>>> Uploading compressed files')
        try:
            self.strumpf.upload_compressed_files()
        except Exception:
            print(">>> Strumpf file upload failed or was interrupted. Aborting...")
            aborting = True
        
        if aborting:
            print('>>> Upload aborted. Removing zip files and references.')
            self.strumpf.roll_back()
        else:
            print('>>> Caching large files locally and deleting them from resource folder')
            self.strumpf.cache_and_delete()
        print('>>> Removing files from staging environment.')
        self.strumpf.clear_staging()

    def download(self, file_name):
        service = self.strumpf.service_from_config()
        was_downloaded = service.download_blob(
            file_name, self.strumpf.get_cache_dir())
        return was_downloaded

    def bulk_download(self):
        service = self.strumpf.service_from_config()
        service.bulk_download(self.strumpf.get_cache_dir())

    def reset(self):
        self.strumpf.roll_back()
        self.strumpf.clear_staging()

    def blobs(self):
        service = self.strumpf.service_from_config()
        service.list_all_blobs()

    def projects(self):
        projects = self.strumpf.get_all_contexts()
        if projects:
            print('>>> Currently tracked Strumpf projects:')
            for project in projects:
                print(project)

    def set_project(self, project):
        projects = self.strumpf.get_all_contexts()
        if project not in projects:
            raise Exception(
                "Project {} not found. Make sure the project you want is listed by 'strumpf projects'".format(project))

        config = self.strumpf.load_config(
            os.path.join(_BASE_DIR, '{}.json'.format(project)))
        self.strumpf.set_config(config)
        set_context(self.strumpf.get_context_from_config())


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
