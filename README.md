# Strumpf - Skymind Test Resource Upload Management for Paunchy Files

Strumpf is a test resource management tool for very large files that fits into your git workflow.
Instead having to rely on git LFS, Strumpf keeps references to the actual test files and downloads
them on demand at test time. This way your test resource folder won't exceed size limits you want
to avoid.

---------

[![Build Status](https://jenkins.ci.skymind.io/buildStatus/icon?job=deeplearing4j/strumpf/master)](https://jenkins.ci.skymind.io/blue/organizations/jenkins/deeplearing4j%2Fstrumpf/activity)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/deeplearning4j/strumpf/blob/master/LICENSE)
[![PyPI version](https://badge.fury.io/py/strumpf.svg)](https://badge.fury.io/py/strumpf)

## Installation

Strumpf is on PyPI, so you can install it with `pip`:

```bash
pip install strumpf
```

Alternatively, you can build the project locally as follows:

```bash
git clone https://www.github.com/deeplearning4j/strumpf.git
cd strumpf
python setup.py install
```

## Strumpf command line interface (CLI)

Installing Strumpf exposes a command line tool called `strumpf`. You can use this tool to configure
your test environment. To initialize a new Strumpf configuration, type

### Configuration

```bash
strumpf configure


███████╗████████╗██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗
██╔════╝╚══██╔══╝██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝
███████╗   ██║   ██████╔╝██║   ██║██╔████╔██║██████╔╝█████╗  
╚════██║   ██║   ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  
███████║   ██║   ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║     ██║
╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝

...
```

First, Strumpf will ask you what the project you want to track is called, where your local resources are stored (full path to folder), and Azure credentials for a blob storage account. After providing all information, you can change into your
test resource directory and query its status using `strumpf status`, which will prompt git-like information:

- it prompts which project you use (below "dl4j")
- it tells you about your untracked large files
- it shows you which large files have been modified
- it tells you which large files are already staged for upload

An example output would look as follows:

```
strumpf status

>>> Working on project dl4j
 Changes to be uploaded:
 (use "strumpf reset <file>..." to unstage files)

        modified:    /home/max/code/strumpf-test-folder/cgoban.jar


 Untracked large files:
 (use "strumpf add <file>..." to include in what will be committed)

        /home/max/code/strumpf-test-folder/test.jar

```
### Tracking large files

Next, to add files to strumpf tracking system you use `strumpf add <file or path>`, to track all
large files recently added in your test folder you could for instance issue the command `strumpf add .`. You can either use absolute paths, or paths relative to the test folder you're working with.

To see the effect of adding files you can query `strumpf status` afterwards again to see that your previously untracked or modified files are now staged for upload by strumpf.

### Uploading files

The final step is `strumpf upload`, which does several things for you:

- Strumpf will compress your staged files using `gzip`.
- It will then compute `sha256` hashes for both original and compressed files.
- The compressed files will be uploaded to Azure blob storage. The original files will be moved to a local caching folder.
- After completion of the upload, all large files will be removed locally and only _references_ to them will be kept, including the file hashes.
- Your large files are now hosted externally on Azure and you can git commit the file references instead.

### Downloading files

To download a file using the CLI, you use

```
strumpf download -f <relative-path-to-file>
```

This command will check if your cache already has the file you're looking for and check if its hash matches the
one found in your local resource folder. If the hashes match, the files won't be downloaded again. If they do not match or if they are no cached files at all, the file will be downloaded.

Finally, to download all available remote resource files, use:

```
strumpf bulk_download
```

### Changing projects

Should you have multiple projects you want to track with Strumpf, you
can do that quite easily. For instance, if you want to add a new project, simply use `strumpf configure` again and use a different project name and configuration as required. You can check at any point which projects are currently tracked by Strumpf by typing

```bash
strumpf projects
```

To switch to another project, simply use

```bash
strumpf set_project <project>
```