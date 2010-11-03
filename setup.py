from setuptools import setup, find_packages
import sys, os

version = '.1'

setup(name='localsms',
      version=version,
      description="A message pooling system for SharedSolar.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='SMS, pyGSM, RapidSMS',
      author='Ivan Willig',
      author_email='iwillig@gmail.com',
      url='sharedsolar.org',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
	'pyserial',
        "python-dateutil",
	'pytz',
        'ipython',
        "simplejson",
        "httplib2",
        'sqlobject',
        'ipdb',
      ],

    entry_points="""
    [console_scripts]
    localsms_start = localsms:main
    """      
)
