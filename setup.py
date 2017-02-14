from setuptools import setup


setup(
    zip_safe=True,
    name='minip4',
    version='1.0',
    author='p4kide',
    packages=[
        'minip4'
    ],
    description='Mininet utility for P4',
    license='LICENSE',
    install_requires=[
        'pyyaml'
    ],
    entry_points={
        'console_scripts': [
            'mnp4=minip4.shell:main',
        ]
    },
)
