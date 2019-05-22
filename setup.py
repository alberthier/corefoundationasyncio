from setuptools import setup

def read(fname):
    import os
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "corefoundationasyncio",
    version = "0.0.1",
    description = "CoreFoundation based selector and asyncio event loop",
    long_description = read('README.md'),
    long_description_content_type='text/markdown',
    url = 'https://github.com/alberthier/corefoundationasyncio',
    license = 'MIT',
    author = 'Eric ALBER',
    author_email = 'eric.alber@gmail.com',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: MacOS X :: Cocoa',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
    ],
    install_requires=['pyobjc'],
    py_modules = ['corefoundationasyncio', 'corefoundationselector'],
)
