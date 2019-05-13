from setuptools import setup
from setuptools import find_packages

setup(
    name='strumpf',
    version='0.3.1',
    packages=find_packages(),
    install_requires=['azure', 'requests', 'click', 'argcomplete'],
    extras_require={
        'tests': ['pytest', 'pytest-pep8', 'pytest-cov', 'mock']
    },
    include_package_data=True,
    license='Apache',
    author='Max Pumperla',
    author_email='max@skymind.io',
    description='Skymind test resource management for paunchy files',
    url='https://github.com/deeplearning4j/strumpf',
    entry_points={
        'console_scripts': [
            'strumpf=strumpf.cli:handle'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ]
)
