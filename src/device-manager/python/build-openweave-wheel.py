#
#    Copyright (c) 2019 Google LLC.
#    Copyright (c) 2014-2017 Nest Labs, Inc.
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

#
#    Description:
#      Builds a Python wheel package for OpenWeave.
#

import sys
import os
from datetime import datetime
import shutil
import getpass
from setuptools import setup
from wheel.bdist_wheel import bdist_wheel

owDLLName = '_WeaveDeviceMgr.so'
deviceManagerShellName = 'weave-device-mgr.py'
deviceManagerShellInstalledName = os.path.splitext(deviceManagerShellName)[0]

#
# Perform a series of setup steps prior to creating the openweave package...
#

# Expect to find the source files for the python modules in the same directory
# as the build script. 
srcDir = os.path.dirname(os.path.abspath(__file__))

# Use the current directory as the build directory.
buildDir = os.path.abspath(os.curdir)

# Make a copy of the openweave package in the build directory, but only if the
# build directory is not the same as the source directory.
owPackageDir = os.path.join(buildDir, 'openweave')
if srcDir != buildDir:
    if os.path.isdir(owPackageDir):
        shutil.rmtree(owPackageDir)
    shutil.copytree(os.path.join(srcDir, 'openweave'), owPackageDir)

# Copy the openweave wrapper DLL from where libtool places it (.libs) into
# the root of the openweave package directory.  This is necessary because
# setuptools will only add package data files that are relative to the
# associated package source root.
shutil.copy2(os.path.join(buildDir, '.libs', owDLLName),
             os.path.join(owPackageDir, owDLLName))

# Make a copy of the Weave Device Manager Shell script in the build directory,
# but without the .py suffix. This is how we want it to appear when installed
# by the wheel, however setuptools provides no way to rename a file at installation
# time. Thus we make a copy.
shutil.copy2(os.path.join(srcDir, deviceManagerShellName),
             os.path.join(buildDir, deviceManagerShellInstalledName))

# Search for the OpenWeave LICENSE file in the parents of the source
# directory and make a copy of the file called LICENSE.txt in the build
# directory.  
def _AllDirsToRoot(dir):
    dir = os.path.abspath(dir)
    while True:
        yield dir
        parent = os.path.dirname(dir)
        if parent == '' or parent == dir:
            break
        dir = parent
for dir in _AllDirsToRoot(srcDir):
    licFileName = os.path.join(dir, 'LICENSE')
    if os.path.isfile(licFileName):
        shutil.copy2(licFileName,
                     os.path.join(buildDir, 'LICENSE.txt'))
        break
else:
    raise FileNotFoundError('Unable to find OpenWeave LICENSE file')

# Define a custom version of the bdist_wheel command that configures the
# resultant wheel as platform-specific (i.e. not "pure"). 
class bdist_wheel_override(bdist_wheel):
    def finalize_options(self):
        bdist_wheel.finalize_options(self)
        self.root_is_pure = False

# Construct the package version string.  If building under Travis use the Travis
# build number as the package version.  Otherwise use a dummy version of '0.0'.
# (See PEP-440 for the syntax rules for python package versions).
if 'TRAVIS_BUILD_NUMBER' in os.environ:
    owPackageVer = os.environ['TRAVIS_BUILD_NUMBER']
else:
    owPackageVer = '0.0'

# Generate a description string with information on how/when the package
# was built. 
if 'TRAVIS_BUILD_NUMBER' in os.environ:
    buildDescription = 'Built by Travis CI on %s\n- Build: %s/#%s\n- Build URL: %s\n- Branch: %s\n- Commit: %s\n' % (
                            datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                            os.environ['TRAVIS_REPO_SLUG'],
                            os.environ['TRAVIS_BUILD_NUMBER'],
                            os.environ['TRAVIS_BUILD_WEB_URL'],
                            os.environ['TRAVIS_BRANCH'],
                            os.environ['TRAVIS_COMMIT'])
else:
    buildDescription = 'Build by %s on %s\n' % (
                            getpass.getuser(),
                            datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

#
# Build the openweave package...
#
 
# Invoke the setuptools 'bdist_wheel' command to generate a wheel containing
# the OpenWeave python packages, shared libraries and scripts.
setup(
    name='openweave',
    version=owPackageVer,
    description='Python APIs for OpenWeave.',
    long_description=buildDescription,
    url='https://github.com/openweave/openweave-core',
    license='Apache',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    python_requires='>=2.7, <3',
    packages=[
        'openweave'                     # Arrange to install a package named "openweave"
    ],
    package_dir={
        '':srcDir,                      # By default, look in the source directory for packages/modules to be included.
        'openweave':owPackageDir        # For the "openweave" package, use the copy in the build directory.
    },
    package_data={
        'openweave':[
            owDLLName                   # Include the wrapper DLL as package data in the "openweave" package.
        ]
    },
    scripts=[                           # Install the Device Manager Shell as an executable script in the 'bin' directory.
        os.path.join(buildDir, deviceManagerShellInstalledName)
    ],
    install_requires=[
        'dbus-python;platform_system=="Linux"',
        'pgi;platform_system=="Linux"'
    ],
    options={
        'bdist_wheel':{
            'universal':False,
            'dist_dir':buildDir         # Place the generated .whl in the build directory.
        },
        'egg_info':{
            'egg_base':buildDir         # Place the .egg-info subdirectory in the build directory.
        }
    },
    cmdclass={
        'bdist_wheel':bdist_wheel_override
    },
    script_args=[ 'clean', '--all', 'bdist_wheel' ]
)
