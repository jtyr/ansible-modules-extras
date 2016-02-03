#!/usr/bin/python
# encoding: utf-8

# (c) 2015-2016, Jiri Tyr <jiri.tyr@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


from glob import glob
import ConfigParser
import os
from ansible.module_utils.pycompat24 import get_exception


DOCUMENTATION = '''
---
module: yum_repository
author: Jiri Tyr (@jtyr)
version_added: '2.2'
short_description: Add and remove YUM repositories
description:
  - Add or remove YUM repositories in RPM-based Linux distributions.

options:
  async:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - If set to C(yes) Yum will download packages and metadata from this
        repo in parallel, if possible.
  bandwidth:
    required: false
    default: 0
    description:
      - Maximum available network bandwidth in bytes/second. Used with the
        I(throttle) option.
      - If I(throttle) is a percentage and bandwidth is C(0) then bandwidth
        throttling will be disabled. If I(throttle) is expressed as a data rate
        (bytes/sec) then this option is ignored. Default is C(0) (no bandwidth
        throttling).
  baseurl:
    required: false
    default: null
    description:
      - URL to the directory where the yum repository's 'repodata' directory
        lives.
      - This or the I(mirrorlist) parameter is required if I(state) is set to
        C(present).
  cost:
    required: false
    default: 1000
    description:
      - Relative cost of accessing this repository. Useful for weighing one
        repo's packages as greater/less than any other.
  deltarpm_metadata_percentage:
    required: false
    default: 100
    description:
      - When the relative size of deltarpm metadata vs pkgs is larger than
        this, deltarpm metadata is not downloaded from the repo. Note that you
        can give values over C(100), so C(200) means that the metadata is
        required to be half the size of the packages. Use C(0) to turn off
        this check, and always download metadata.
  deltarpm_percentage:
    required: false
    default: 75
    description:
      - When the relative size of delta vs pkg is larger than this, delta is
        not used. Use C(0) to turn off delta rpm processing. Local repositories
        (with file:// I(baseurl)) have delta rpms turned off by default.
  description:
    required: false
    default: null
    description:
      - A human readable string describing the repository.
      - This parameter is only required if I(state) is set to C(present).
  enabled:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - This tells yum whether or not use this repository.
  enablegroups:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - Determines whether yum will allow the use of package groups for this
        repository.
  exclude:
    required: false
    default: null
    description:
      - List of packages to exclude from updates or installs. This should be a
        space separated list. Shell globs using wildcards (eg. C(*) and C(?))
        are allowed.
      - The list can also be a regular YAML array.
  failovermethod:
    required: false
    choices: [roundrobin, priority]
    default: roundrobin
    description:
      - C(roundrobin) randomly selects a URL out of the list of URLs to start
        with and proceeds through each of them as it encounters a failure
        contacting the host.
      - C(priority) starts from the first I(baseurl) listed and reads through
        them sequentially.
  file:
    required: false
    default: null
    description:
      - File to use to save the repo in. Defaults to the value of I(name).
  gpgcakey:
    required: false
    default: null
    description:
      - A URL pointing to the ASCII-armored CA key file for the repository.
  gpgcheck:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - Tells yum whether or not it should perform a GPG signature check on
        packages.
  gpgkey:
    required: false
    default: null
    description:
      - A URL pointing to the ASCII-armored GPG key file for the repository.
  http_caching:
    required: false
    choices: [all, packages, none]
    default: all
    description:
      - Determines how upstream HTTP caches are instructed to handle any HTTP
        downloads that Yum does.
      - C(all) means that all HTTP downloads should be cached.
      - C(packages) means that only RPM package downloads should be cached (but
         not repository metadata downloads).
      - C(none) means that no HTTP downloads should be cached.
  ignore_repo_files:
    version_added: '2.2'
    required: false
    default: None
    description:
      - List of repo files which should be ignored during deletion in the
        Managed Mode. Default is empty list (C([])).
  include:
    required: false
    default: null
    description:
      - Include external configuration file. Both, local path and URL is
        supported. Configuration file will be inserted at the position of the
        I(include=) line. Included files may contain further include lines.
        Yum will abort with an error if an inclusion loop is detected.
  includepkgs:
    required: false
    default: null
    description:
      - List of packages you want to only use from a repository. This should be
        a space separated list. Shell globs using wildcards (eg. C(*) and C(?))
        are allowed. Substitution variables (e.g. C($releasever)) are honored
        here.
      - The list can also be a regular YAML array.
  ip_resolve:
    required: false
    choices: [4, 6, IPv4, IPv6, whatever]
    default: whatever
    description:
      - Determines how yum resolves host names.
      - C(4) or C(IPv4) - resolve to IPv4 addresses only.
      - C(6) or C(IPv6) - resolve to IPv6 addresses only.
  keepalive:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - This tells yum whether or not HTTP/1.1 keepalive should be used with
        this repository. This can improve transfer speeds by using one
        connection when downloading multiple files from a repository.
  keepcache:
    required: false
    choices: ['0', '1']
    default: '1'
    description:
      - Either C(1) or C(0). Determines whether or not yum keeps the cache of
        headers and packages after successful installation.
  metadata_expire:
    required: false
    default: 21600
    description:
      - Time (in seconds) after which the metadata will expire.
      - Default value is 6 hours.
  metadata_expire_filter:
    required: false
    choices: [never, 'read-only:past', 'read-only:present', 'read-only:future']
    default: 'read-only:present'
    description:
      - Filter the I(metadata_expire) time, allowing a trade of speed for
        accuracy if a command doesn't require it. Each yum command can specify
        that it requires a certain level of timeliness quality from the remote
        repos. from "I'm about to install/upgrade, so this better be current"
        to "Anything that's available is good enough".
      - C(never) - Nothing is filtered, always obey I(metadata_expire).
      - C(read-only:past) - Commands that only care about past information are
        filtered from metadata expiring. Eg. I(yum history) info (if history
        needs to lookup anything about a previous transaction, then by
        definition the remote package was available in the past).
      - C(read-only:present) - Commands that are balanced between past and
        future. Eg. I(yum list yum).
      - C(read-only:future) - Commands that are likely to result in running
        other commands which will require the latest metadata. Eg.
        I(yum check-update).
      - Note that this option does not override "yum clean expire-cache".
  metalink:
    required: false
    default: null
    description:
      - Specifies a URL to a metalink file for the repomd.xml, a list of
        mirrors for the entire repository are generated by converting the
        mirrors for the repomd.xml file to a I(baseurl).
  mirrorlist:
    required: false
    default: null
    description:
      - Specifies a URL to a file containing a list of baseurls.
      - This or the I(baseurl) parameter is required if I(state) is set to
        C(present).
  mirrorlist_expire:
    required: false
    default: 21600
    description:
      - Time (in seconds) after which the mirrorlist locally cached will
        expire.
      - Default value is 6 hours.
  name:
    required: false
    description:
      - Unique repository ID.
      - This parameter is only required if I(state) is set to C(present) or
        C(absent).
  params:
    required: false
    default: null
    description:
      - Option used to allow the user to overwrite any of the other options.
        To remove an option, set the value of the option to C(null).
  password:
    required: false
    default: null
    description:
      - Password to use with the username for basic authentication.
  priority:
    required: false
    default: 99
    description:
      - Enforce ordered protection of repositories. The value is an integer
        from 1 to 99.
      - This option only works if the YUM Priorities plugin is installed.
  protect:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - Protect packages from updates from other repositories.
  proxy:
    required: false
    default: null
    description:
      - URL to the proxy server that yum should use. Set to C(_none_) to disable
        the global proxy setting.
  proxy_password:
    required: false
    default: null
    description:
      - Username to use for proxy.
  proxy_username:
    required: false
    default: null
    description:
      - Password for this proxy.
  repo_gpgcheck:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - This tells yum whether or not it should perform a GPG signature check
        on the repodata from this repository.
  reposdir:
    required: false
    default: /etc/yum.repos.d
    description:
      - Directory where the C(.repo) files will be stored.
  retries:
    required: false
    default: 10
    description:
      - Set the number of times any attempt to retrieve a file should retry
        before returning an error. Setting this to C(0) makes yum try forever.
  s3_enabled:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - Enables support for S3 repositories.
      - This option only works if the YUM S3 plugin is installed.
  skip_if_unavailable:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - If set to C(yes) yum will continue running if this repository cannot be
        contacted for any reason. This should be set carefully as all repos are
        consulted for any given command.
  ssl_check_cert_permissions:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - Whether yum should check the permissions on the paths for the
        certificates on the repository (both remote and local).
      - If we can't read any of the files then yum will force
        I(skip_if_unavailable) to be C(yes). This is most useful for non-root
        processes which use yum on repos that have client cert files which are
        readable only by root.
  sslcacert:
    required: false
    default: null
    description:
      - Path to the directory containing the databases of the certificate
        authorities yum should use to verify SSL certificates.
  sslclientcert:
    required: false
    default: null
    description:
      - Path to the SSL client certificate yum should use to connect to
        repos/remote sites.
  sslclientkey:
    required: false
    default: null
    description:
      - Path to the SSL client key yum should use to connect to repos/remote
        sites.
  sslverify:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - Defines whether yum should verify SSL certificates/hosts at all.
  state:
    required: false
    choices: [absent, present, mm_enabled, mm_disabled, managed]
    default: present
    description:
      - The state of the repo file (C(absent), C(present)) or the Managed Mode
        (C(mm_enabled), C(mm_disabled), C(managed)).
      - The C(mm_enabled) will enable Managed Mode. This state should be used
        somewhere at the beginning of the playbook before any M(yum_repository)
        module calls are made.
      - The C(mm_disabled) will disable the Managed Mode.
      - The C(managed) will initiate the deletion of unmanaged repo files if
        the I(mm_enabled) was used before. This state should be used only
        somewhere at the end of the playbook where M(yum_repository) module is
        called no more.
  throttle:
    required: false
    default: null
    description:
      - Enable bandwidth throttling for downloads.
      - This option can be expressed as a absolute data rate in bytes/sec. An
        SI prefix (k, M or G) may be appended to the bandwidth value.
  timeout:
    required: false
    default: 30
    description:
      - Number of seconds to wait for a connection before timing out.
  ui_repoid_vars:
    required: false
    default: releasever basearch
    description:
      - When a repository id is displayed, append these yum variables to the
        string if they are used in the I(baseurl)/etc. Variables are appended
        in the order listed (and found).
  username:
    required: false
    default: null
    description:
      - Username to use for basic authentication to a repo or really any url.

extends_documentation_fragment:
  - files

notes:
  - All comments will be removed if modifying an existing repo file.
  - Section order is preserved in an existing repo file.
  - Parameters in a section are ordered alphabetically in an existing repo
    file.
  - The repo file will be automatically deleted if it contains no repository.
'''

EXAMPLES = '''
- name: Add repository
  yum_repository:
    name: epel
    description: EPEL YUM repo
    baseurl: http://download.fedoraproject.org/pub/epel/$releasever/$basearch/

- name: Add multiple repositories into the same file (1/2)
  yum_repository:
    name: epel
    description: EPEL YUM repo
    file: external_repos
    baseurl: http://download.fedoraproject.org/pub/epel/$releasever/$basearch/
    gpgcheck: no
- name: Add multiple repositories into the same file (2/2)
  yum_repository:
    name: rpmforge
    description: RPMforge YUM repo
    file: external_repos
    baseurl: http://apt.sw.be/redhat/el7/en/$basearch/rpmforge
    mirrorlist: http://mirrorlist.repoforge.org/el7/mirrors-rpmforge
    enabled: no

- name: Remove repository
  yum_repository:
    name: epel
    state: absent

- name: Remove repository from a specific repo file
  yum_repository:
    name: epel
    file: external_repos
    state: absent

#
# Allow to overwrite the yum_repository parameters by defining the parameters
# as a variable in the defaults or vars file:
#
# my_role_somerepo_params:
#   # Disable GPG checking
#   gpgcheck: no
#   # Remove the gpgkey option
#   gpgkey: null
#
- name: Add Some repo
  yum_repository:
    name: somerepo
    description: Some YUM repo
    baseurl: http://server.com/path/to/the/repo
    gpgkey: http://server.com/keys/somerepo.pub
    gpgcheck: yes
    params: "{{ my_role_somerepo_params }}"

#
# Example of a playbook using the Managed Mode
#

- name: Initial play
  hosts: all
  tasks:
    - name: Enable the Managed Mode
      yum_repository:
        state: mm_enabled

- name: My play
  hosts: testhost1
  tasks:
    - name: Create a repo file
      yum_repository:
        name: myrepo
        description: Managed repo
        baseurl: http://repo.server.com/path/to/the/repo

- name: Final play
  hosts: all
  tasks:
    - name: Delete unmanaged repo files
      yum_repository:
        state: managed
        # These repo files won't be deleted even if they are not managed
        ignore_repo_files:
          - CentOS-Base
          - CentOS-Media
'''

RETURN = '''
repo:
    description: repository name
    returned: success
    type: string
    sample: "epel"
state:
    description: state of the target, after execution
    returned: success
    type: string
    sample: "present"
'''


class YumRepo(object):
    # Class global variables
    module = None
    params = None
    section = None
    repofile = ConfigParser.RawConfigParser()

    # List of parameters which will be allowed in the repo file output
    allowed_params = [
        'async',
        'bandwidth',
        'baseurl',
        'cost',
        'deltarpm_metadata_percentage',
        'deltarpm_percentage',
        'enabled',
        'enablegroups',
        'exclude',
        'failovermethod',
        'gpgcakey',
        'gpgcheck',
        'gpgkey',
        'http_caching',
        'include',
        'includepkgs',
        'ip_resolve',
        'keepalive',
        'keepcache',
        'metadata_expire',
        'metadata_expire_filter',
        'metalink',
        'mirrorlist',
        'mirrorlist_expire',
        'name',
        'password',
        'priority',
        'protect',
        'proxy',
        'proxy_password',
        'proxy_username',
        'repo_gpgcheck',
        'retries',
        's3_enabled',
        'skip_if_unavailable',
        'sslcacert',
        'ssl_check_cert_permissions',
        'sslclientcert',
        'sslclientkey',
        'sslverify',
        'throttle',
        'timeout',
        'ui_repoid_vars',
        'username']

    # List of parameters which can be a list
    list_params = ['exclude', 'includepkgs']

    def __init__(self, module):
        # To be able to use fail_json
        self.module = module
        # Shortcut for the params
        self.params = self.module.params
        # Section is always the repoid
        self.section = self.params['repoid']

        # Check if repo directory exists
        repos_dir = self.params['reposdir']
        if not os.path.isdir(repos_dir):
            self.module.fail_json(
                msg="Repo directory '%s' does not exist." % repos_dir)

        # Set dest; also used to set dest parameter for the FS attributes
        self.params['dest'] = os.path.join(
            repos_dir, "%s.repo" % self.params['file'])

        # Read the repo file if it exists
        if os.path.isfile(self.params['dest']):
            self.repofile.read(self.params['dest'])

    def add(self):
        # Remove already existing repo and create a new one
        if self.repofile.has_section(self.section):
            self.repofile.remove_section(self.section)

        # Add section
        self.repofile.add_section(self.section)

        # Baseurl/mirrorlist is not required because for removal we need only
        # the repo name. This is why we check if the baseurl/mirrorlist is
        # defined.
        if (self.params['baseurl'], self.params['mirrorlist']) == (None, None):
            self.module.fail_json(
                msg='Paramater "baseurl" or "mirrorlist" is required for '
                'adding a new repo.')

        # Set options
        for key, value in sorted(self.params.items()):
            if key in self.list_params and isinstance(value, list):
                # Join items into one string for specific parameters
                value = ' '.join(value)
            elif isinstance(value, bool):
                # Convert boolean value to integer
                value = int(value)

            # Set the value only if it was defined (default is None)
            if value is not None and key in self.allowed_params:
                self.repofile.set(self.section, key, value)

    def save(self):
        if len(self.repofile.sections()):
            # Write data into the file
            try:
                fd = open(self.params['dest'], 'wb')
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg="Cannot open repo file %s." % self.params['dest'],
                    details=str(e))

            self.repofile.write(fd)

            try:
                fd.close()
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg="Cannot write repo file %s." % self.params['dest'],
                    details=str(e))
        else:
            # Remove the file if there are not repos
            try:
                os.remove(self.params['dest'])
            except OSError:
                e = get_exception()
                self.module.fail_json(
                    msg=(
                        "Cannot remove empty repo file %s." %
                        self.params['dest']),
                    details=str(e))

    def remove(self):
        # Remove section if exists
        if self.repofile.has_section(self.section):
            self.repofile.remove_section(self.section)

    def dump(self):
        repo_string = ""

        # Compose the repo file
        for section in sorted(self.repofile.sections()):
            repo_string += "[%s]\n" % section

            for key, value in sorted(self.repofile.items(section)):
                repo_string += "%s = %s\n" % (key, value)

            repo_string += "\n"

        return repo_string


class ManagedMode(object):
    def __init__(self, module):
        # To be able to use fail_json
        self.module = module
        # Shortcut for the params
        self.params = self.module.params
        # Path to the .managed file
        self.file = "%s/.managed" % self.params['reposdir']

    def enable(self):
        changed = False

        file_exists = os.path.isfile(self.file)

        if (
                not file_exists or
                os.path.getsize(self.file) > 0):
            if not self.module.check_mode:
                # Create an empty file or truncate the existing one
                try:
                    open(self.file, 'w').close()
                except IOError:
                    e = get_exception()
                    self.module.fail_json(
                        msg="Cannot create managed file '%s'." % self.file,
                        details=str(e))

            # Register the change if the file was just created
            if not file_exists:
                changed = True

        return changed

    def disable(self):
        changed = False

        # Delete the file if exists
        if os.path.isfile(self.file):
            if not self.module.check_mode:
                try:
                    os.remove(self.file)
                except OSError:
                    e = get_exception()
                    self.module.fail_json(
                        msg="Cannot delete managed file '%s'." % self.file,
                        details=str(e))

            # Register the change
            changed = True

        return changed

    def add(self, repo_file):
        changed = False

        if os.path.isfile(self.file):
            try:
                fd = open(self.file, 'a+')
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg="Cannot open managegment file '%s'." % self.file,
                    details=str(e))

            found = False

            # Check if the repo file is already managed
            for line in fd.read().splitlines():
                if line == repo_file:
                    found = True
                    break

            if not found:
                if not self.module.check_mode:
                    # Add the repo file name into the managed file
                    fd.write("%s\n" % repo_file)

                # Register the change
                changed = True

            try:
                fd.close()
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg=(
                        "Cannot close the managed file '%s'." % self.file),
                    details=str(e))

        return changed

    def remove(self, repo_file):
        changed = False

        if os.path.isfile(self.file):
            try:
                fd = open(self.file, 'r')
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg="Cannot open the managed file '%s'." % self.file,
                    details=str(e))

            found = -1

            lines = fd.read().splitlines()

            # Check if the repo file is managed
            for i, line in enumerate(lines):
                if line == repo_file:
                    found = i
                    break

            if found > -1:
                lines.pop(found)
                # Register the change
                changed = True

            # Close the file
            try:
                fd.close()
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg="Cannot close the managed file '%s'." % self.file,
                    details=str(e))

            # Build the file from scratch
            if not self.module.check_mode:
                # Clear the file
                self.enable()

                # Add remaining lines back into the file
                for line in lines:
                    # Record the change
                    self.add(line)

        return changed

    def process(self):
        changed = False

        if os.path.isfile(self.file):
            # Get list of repo files
            repo_files = glob("%s/*.repo" % self.params['reposdir'])

            try:
                fd = open(self.file, 'r')
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg="Cannot open the managed file '%s'." % self.file,
                    details=str(e))

            # Walk through the managed repos
            managed_files = fd.read().splitlines()

            # Close the file
            try:
                fd.close()
            except IOError:
                e = get_exception()
                self.module.fail_json(
                    msg="Cannot close the managed file '%s'." % self.file,
                    details=str(e))

            # Walk through the repo files and check if they are managed
            for f in repo_files:
                # Get only the file name without the extension
                repo_file = os.path.basename(f)[:-5]

                if (
                        repo_file not in managed_files and
                        repo_file not in self.params['ignore_repo_files']):
                    if not self.module.check_mode:
                        # Delete the file if not managed
                        try:
                            os.remove(f)
                        except OSError:
                            e = get_exception()
                            self.module.fail_json(
                                msg=(
                                    "Cannot delete the unmanaged repo file "
                                    "'%s'." % f),
                                details=str(e))

                        # Delete it from the managed file as well
                        self.remove(repo_file)

                    # Register the change
                    changed = True

        return changed


def main():
    # Module settings
    module = AnsibleModule(
        argument_spec=dict(
            async=dict(type='bool'),
            bandwidth=dict(),
            baseurl=dict(),
            cost=dict(),
            deltarpm_metadata_percentage=dict(),
            deltarpm_percentage=dict(),
            description=dict(),
            enabled=dict(type='bool'),
            enablegroups=dict(type='bool'),
            exclude=dict(),
            failovermethod=dict(choices=['roundrobin', 'priority']),
            file=dict(),
            gpgcakey=dict(),
            gpgcheck=dict(type='bool'),
            gpgkey=dict(),
            http_caching=dict(choices=['all', 'packages', 'none']),
            include=dict(),
            includepkgs=dict(),
            ip_resolve=dict(choices=['4', '6', 'IPv4', 'IPv6', 'whatever']),
            keepalive=dict(type='bool'),
            keepcache=dict(choices=['0', '1']),
            metadata_expire=dict(),
            metadata_expire_filter=dict(
                choices=[
                    'never',
                    'read-only:past',
                    'read-only:present',
                    'read-only:future']),
            metalink=dict(),
            mirrorlist=dict(),
            mirrorlist_expire=dict(),
            name=dict(),
            params=dict(),
            password=dict(no_log=True),
            priority=dict(),
            protect=dict(type='bool'),
            proxy=dict(),
            proxy_password=dict(no_log=True),
            proxy_username=dict(),
            repo_gpgcheck=dict(type='bool'),
            reposdir=dict(default='/etc/yum.repos.d', type='path'),
            retries=dict(),
            s3_enabled=dict(type='bool'),
            skip_if_unavailable=dict(type='bool'),
            sslcacert=dict(),
            ssl_check_cert_permissions=dict(type='bool'),
            sslclientcert=dict(),
            sslclientkey=dict(),
            sslverify=dict(type='bool'),
            state=dict(
                choices=[
                    'present',
                    'absent',
                    'mm_enabled',
                    'mm_disabled',
                    'managed'],
                default='present'),
            throttle=dict(),
            timeout=dict(),
            ui_repoid_vars=dict(),
            username=dict(),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    # Update module parameters by user's parameters if defined
    if 'params' in module.params and isinstance(module.params['params'], dict):
        module.params.update(module.params['params'])
        # Remove the params
        module.params.pop('params', None)

    name = module.params['name']
    state = module.params['state']

    # Check if required parameters are present
    if state in ['present', 'absent'] and name is None:
        module.fail_json(
            msg="Parameter 'name' is required.")
    if state == 'present':
        if (
                module.params['baseurl'] is None and
                module.params['mirrorlist'] is None):
            module.fail_json(
                msg="Parameter 'baseurl' or 'mirrorlist' is required.")
        if module.params['description'] is None:
            module.fail_json(
                msg="Parameter 'description' is required.")

    # Instantiate the ManagedMode object
    mm = ManagedMode(module)

    if state in ['present', 'absent']:
        # Rename "name" and "description" to ensure correct key sorting
        module.params['repoid'] = module.params['name']
        module.params['name'] = module.params['description']
        del module.params['description']
        del module.params['ignore_repo_files']

        # Define repo file name if it doesn't exist
        if module.params['file'] is None:
            module.params['file'] = module.params['repoid']

        # Instantiate the YumRepo object
        yumrepo = YumRepo(module)

        # Get repo status before change
        yumrepo_before = yumrepo.dump()

        # Perform action depending on the state
        if state == 'present':
            yumrepo.add()

            # Make sure the repo file is managed if required
            mm.add(module.params['file'])
        elif state == 'absent':
            yumrepo.remove()

            # If the file was removed, remove also from the managed list
            if not os.path.isfile(module.params['file']):
                mm.remove(module.params['file'])

        # Get repo status after change
        yumrepo_after = yumrepo.dump()

        # Compare repo states
        changed = yumrepo_before != yumrepo_after

        # Save the file only if not in check mode and if there was a change
        if not module.check_mode and changed:
            yumrepo.save()

        # Change file attributes if needed
        if os.path.isfile(module.params['dest']):
            file_args = module.load_file_common_arguments(module.params)
            changed = module.set_fs_attributes_if_different(file_args, changed)

        # Print status of the change
        module.exit_json(changed=changed, repo=name, state=state)
    elif state in ['mm_enabled', 'mm_disabled', 'managed']:
        # Perform action depending on the state
        if state == 'mm_enabled':
            changed = mm.enable()
        elif state == 'mm_disabled':
            changed = mm.disable()
        elif state == 'managed':
            changed = mm.process()

        # Print status of the change
        module.exit_json(changed=changed, state=state)


# Import module snippets
from ansible.module_utils.basic import *


if __name__ == '__main__':
    main()
