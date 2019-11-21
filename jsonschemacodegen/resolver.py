from . import cpp
from . import python as pyschema
from . import json_example as jsex
import stringcase
from . import schemawrappers
import yaml
from copy import copy

class SimpleResolver(cpp.ResolverBaseClass, pyschema.ResolverBaseClass, jsex.SchemaResolverBaseClass):

    def __init__(self, uri, root=None):
        self.uri = uri
        self.root = root
        self.usings = []
        self.rootNs = []

    def cpp_set_root_namespace(self, ns: list):
        self.rootNs = ns

    def cpp_add_using(self, using: list):
        self.usings.append(using)

    def cpp_get_root_namespace(self) -> list:
        return self.rootNs

    def cpp_get_usings(self) -> list:
        return self.usings

    def _get_reference_parts(self, reference) -> tuple:
        pkg = None
        fn = reference.split('#')[0] or None
        path = reference.split('#')[1]
        parts = path.split('/')
        if fn:
            pkg = fn.split('.')[0]
        return (pkg, parts[-2], stringcase.pascalcase(parts[-1]))

    def _get_reference_parts(self, reference) -> dict:
        assert('#' in reference), "Reference '{}' seemed malformed".format(reference)
        url, path = reference.split('#')
        theType, name = path.split('/')[-2:]
        return {
            "url": url,
            "uri": url,
            "path": path,
            "type": theType,
            "PascalType": stringcase.pascalcase(theType),
            "name": name,
            "PascalName": stringcase.pascalcase(name),
            "snake_name": stringcase.snakecase(name),
            "pkg": url is not None and url.split(".")[0] or None,
        }

    def cpp_get_header_dir(self, uri=None) -> str:
        uri = uri or self.uri
        pkg = uri.split(".")[0]
        return pkg

    def cpp_get_filename_base(self, reference) -> str:
        parts = self._get_reference_parts(reference)
        if parts['pkg'] not in [None, self.uri]:
            header_dir = self.cpp_get_header_dir(parts['uri'])
            fn_base = "{0}/{1}_{2}".format(header_dir, parts['type'].rstrip('s'), parts['snake_name'])
        else:
            fn_base = "{0}_{1}".format(parts['type'].rstrip('s'), parts['snake_name'])
        return fn_base

    def cpp_get_header(self, reference) -> str:
        header = "{}.hpp".format(self.cpp_get_filename_base(reference))
        return header

    def cpp_get_namespace(self, reference) -> list:
        parts = self._get_reference_parts(reference)
        ns = copy(self.rootNs)
        if parts['pkg'] is not None:
            ns.append(stringcase.lowercase(parts['pkg']))
        else:
            ns.append(self.uri)
        ns.append(stringcase.lowercase(parts['type'].rstrip('s')))
        return ns

    def cpp_get_name(self, reference) -> str:
        parts = self._get_reference_parts(reference)
        return parts['PascalName']

    def py_include_statement(self, reference) -> str:
        ref = self._get_reference_parts(reference)
        if ref['pkg'] is not None:
            return "import {pkg}.{type}_{name}".format(**ref)
        else:
            return "import {type}_{name}".format(**ref)

    def py_class_name(self, reference) -> str:
        ref = self._get_reference_parts(reference)
        if ref['pkg'] is not None:
            return "{pkg}.{type}_{name}.{PascalName}".format(**ref)
        else:
            return "{type}_{name}.{PascalName}".format(**ref)

    def py_filename(self, reference) -> str:
        ref = self._get_reference_parts(reference)
        return "{type}_{name}.py".format(**ref)

    def _walk_through_tree(self, tree, path) -> dict:
        walker = tree
        for p in path:
            walker = walker[p]
        return walker

    def _get_document(self, uri, encoding=None) -> dict:
        with open(uri, 'r') as fp:
            if encoding == 'json' or (encoding is None and 'json' in uri):
                return json.load(f)
            else:
                return yaml.load(fp, Loader=yaml.FullLoader)

    def get_schema(self, reference) -> schemawrappers.SchemaBase:
        parts = self._get_reference_parts(reference)
        uri = parts['uri']
        if not uri:
            if not self.root:
                uri = self.uri
            else:
                return schemawrappers.SchemaFactory(self._walk_through_tree(self.root, parts['path']))
        raw = self._get_document(uri)
        return schemawrappers.SchemaFactory(self._walk_through_tree(raw, parts['path']))

