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

from .strumpf import set_config, get_config, validate_config
from .strumpf import get_context_from_config
from .utils import set_context

if sys.version_info[0] == 2:
    input = raw_input


_CONFIG = get_config()
AZURE_ACCOUNT_NAME = _CONFIG['azure_account_name']
FILE_SIZE_LIMIT_IN_MB = _CONFIG['file_size_limit_in_mb']
CONTAINER_NAME = _CONFIG['container_name']


def to_bool(string):
    if type(string) is bool:
        return string
    return True if string[0] in ["Y", "y"] else False


class CLI(object):

    def __init__(self):
        self.var_args = None
        self.command = None

    def command_dispatcher(self, args=None):
        desc = ('Strumpf, Skymind test resource management for paunchy files.\n')
        parser = argparse.ArgumentParser(description=desc)
        parser.add_argument(
            '-v', '--version', action='version',
            version=pkg_resources.get_distribution("strumpf").version,
            help='Print strumpf version'
        )

        subparsers = parser.add_subparsers(title='subcommands', dest='command')
        subparsers.add_parser('configure', help='Configure strumpf')
        subparsers.add_parser('status', help='Get strumpf status')
        subparsers.add_parser('add', help='Add files to strumpf tracking system')
        subparsers.add_parser('upload', help='Upload files to remote source')

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
            self.add()
            return

        if self.command == 'upload':
            self.upload()
            return

        if self.command == 'download':
            self.download()
            return
        
        if self.command == 'bulk_download':
            self.bulk_download()

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
                             AZURE_ACCOUNT_NAME) or AZURE_ACCOUNT_NAME

        # Storage account key
        account_key = input("Please specify the respective account key: ")

        # Container name
        container_name = input("Which blob storage container should be used (default '%s'): " %
                             CONTAINER_NAME) or CONTAINER_NAME

        # File size limit
        file_limit = input("Strumpf uploads large files to Azure instead of checking them into git," +
                            "from which file size in MB on should we upload your files (default '%s' MB): " %
                             FILE_SIZE_LIMIT_IN_MB) or FILE_SIZE_LIMIT_IN_MB

        # Local resource folder
        local_resource_folder = input("Please specify the full path to the resource folder you want to track: ")

        cli_out = {
            'azure_account_name': account_name,
            'azure_account_key': account_key,
            'file_size_limit_in_mb': file_limit,
            'container_name': container_name,
            'local_resource_folder': local_resource_folder
        }

        validate_config(cli_out)
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

        set_config(cli_out)
        set_context(get_context_from_config())


    def status(self):
        # TODO: list all large files in resource folder
        pass
    
    def add(self):
        # single file and "."
        pass

    def upload(self):
        # compress file
        # compute md5 hash of original and compressed file
        # create .resource file with file name and hashes
        # upload added files using azure cli
        pass

    def download(self):
        # TODO: download individual files
        pass
    
    def bulk_download(self):
        # TODO: bulk download all remote resources
        pass
        

def handle():
    try:
        cli = CLI()
        sys.exit(cli.command_dispatcher())
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        click.echo(click.style("Error: ", fg='red', bold=True))
        traceback.print_exc()
        sys.exit()


if __name__ == '__main__':
    handle()
