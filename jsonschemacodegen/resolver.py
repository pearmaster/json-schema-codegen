from . import cpp
from . import python as pyschema
from . import json_example as jsex
import stringcase
from . import schemawrappers
import yaml
from copy import copy

class TreeWalkerException(Exception):
    pass

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
        assert(tree is not None), "No tree to walk through"
        walker = tree
        for p in [p for p in path.split('/') if len(p) > 0]:
            if p not in walker:
                treeTitle = 'info' in tree and 'title' in tree['info'] and tree['info']['title'] or 'UNKNOWN'
                treeId = 'id' in tree and tree['id'] or treeTitle
                raise TreeWalkerException("Could not resolve {} from '{}'".format(path, treeId))
            walker = walker[p]
        return walker

    def get_document(self, uri, encoding=None) -> dict:
        if '#' in uri:
            uri = uri.split('#')[0]
        with open(uri, 'r') as fp:
            if encoding == 'json' or (encoding is None and 'json' in uri):
                import json
                return json.load(fp)
            else:
                return yaml.load(fp, Loader=yaml.FullLoader)

    def _get_root(self, reference, root):
        parts = self._get_reference_parts(reference)
        if parts['uri']:
            root_doc = self.get_document(parts['uri'])
        elif root is not None:
            root_doc = root
        else:
            root_doc = self.root
        return root_doc

    def get_json(self, reference, root=None) -> dict:
        parts = self._get_reference_parts(reference)
        root_doc = self._get_root(reference, root)
        try:
            json_doc = self._walk_through_tree(root_doc, parts['path'])
        except TreeWalkerException as e:
            print(f"{self} Error in resolving {reference}: {e}")
            raise
        else:
            return json_doc

    def get_schema(self, reference, root=None) -> schemawrappers.SchemaBase:
        schemasRoot = self._get_root(reference, root)
        schema = schemawrappers.SchemaFactory(self.get_json(reference, root=root), schemasRoot)
        return schema

    def cpp_get_lib_ns(self):
        return []