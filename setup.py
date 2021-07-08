#!/usr/bin/python3
import setuptools
setuptools.setup(
    name='cyber_zfs_backup',
    version='1.0',
    packages=['cyber_zfs_backup'],
    install_requires=[
        'arrow',
        'pkg-resources',
        'importlib-metadata',   # FIXME: why is this a dependency now???
    ],
    # NOTE: Python packaging has no clear way to create config files in /etc/.
    # Therefore that is done in debian/*.install instead.
    # package_data={
    #     '': ['*.jpg',
    #          '*.css']},
    # This makes /usr/bin/foo which are basically #!/bin/sh ↲ exec python3 -m foo "$@"
    # Ref. https://packaging.python.org/tutorials/distributing-packages/#console-scripts
    # Ref. https://github.com/pypa/sampleproject
    entry_points={
        'console_scripts': [
            'cyber-zfs-backup=cyber_zfs_backup.__main__:main',
        ]
    }
)
