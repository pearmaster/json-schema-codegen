from setuptools import setup, find_packages

setup(name='json-schema-codegen',
      version='0.0.2',
      description='Codegen from JSON Schema',
      url='http://github.com/pearmaster/json-schema-codegen',
      author='Jacob Brunson',
      author_email='pypi@jacobbrunson.com',
      license='GPLv2',
      packages=['jsonschemacodegen', 'jsonschemacodegen.templates.cpp'],
      package_data={
            'jsonschemacodegen.templates.cpp': ['*.jinja2']
      },
      zip_safe=False,
      install_requires=[
          'jinja2',
          'stringcase',
      ],
      include_package_data=True,
      python_requires='>=3.7',
)