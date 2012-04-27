#!/usr/bin/env python
from distutils.core import setup

setup(name='django-outliner',
      version='0.1',
      description='Django application that extends django-mptt with an outliner changelist',
      author='AGoodId',
      author_email='teknik@agoodid.se',
      url='http://github.com/AGoodId/django-outliner/',
      packages=['outliner'],
      license='BSD',
      include_package_data = False,
      zip_safe = False,
      classifiers = [
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Environment :: Web Environment',
          'Framework :: Django',
      ],
)
