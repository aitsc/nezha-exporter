from setuptools import setup, find_packages


with open('version.txt', 'r') as f:
    version = f.read().strip()
with open('readme.md', 'r') as f:
    long_description = f.read()


setup(
    name='nezha-exporter',
    version=version,
    description="nezha 面板 api 转 prometheus metrics 接口",
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
    python_requires='>=3.7',
)
