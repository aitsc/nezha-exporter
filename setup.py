from setuptools import setup, find_packages


with open('version.txt', 'r') as f:
    version = f.read().strip()
with open('readme.md', 'r') as f:
    long_description = f.read()


setup(
    name='nezha-exporter',
    version=version,
    description="nezha 面板 api 转 prometheus metrics 接口 exporter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='aitsc',
    url='https://github.com/aitsc/nezha-exporter',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'httpx',
        'prometheus-client',
        'uvicorn',
        'tsc-base',
    ],
    entry_points={
        'console_scripts': [
            'nezha-prometheus-exporter=nezha_exporter.api:main',
        ],
    },
    license='Apache License 2.0',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
)
