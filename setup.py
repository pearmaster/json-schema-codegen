from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fp:
    requirements = fp.read().split('\n')

setup(name='json-schema-codegen',
      version='0.0.7',
      url='http://github.com/pearmaster/json-schema-codegen',
      author='Jacob Brunson',
      author_email='pypi@jacobbrunson.com',
      description="Generate C++ structures from JSON-Schema",
      long_description=long_description,
      long_description_content_type="text/markdown",
      license='GPLv2',
      packages=['jsonschemacodegen', 'jsonschemacodegen.templates.cpp'],
      package_data={
            'jsonschemacodegen.templates.cpp': ['*.jinja2']
      },
      zip_safe=False,
      install_requires=requirements,
      include_package_data=True,
      python_requires='>=3.7',
)