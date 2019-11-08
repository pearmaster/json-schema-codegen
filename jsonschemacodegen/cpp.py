import json
import abc
import stringcase

from . import templator
from . import schemawrappers

class ResolverBaseClass(abc.ABC):

    def ResolveNamespace(self, usings: list, ns: list, append='') -> str:
        assert(isinstance(ns, list))
        for n in ns:
            assert(isinstance(n, str)), "namespace is %s" % (ns)
        ret = ns
        nsString = "||".join(ns)
        for using in usings:
            if nsString.startswith("||".join(using)):
                abbr = ns[len(using):]
                if len(abbr) < len(ret):
                    ret = abbr
        if len(ret) > 0:
            return "::".join(ret)+append
        else:
            return ""

    def AppendToNamespace(self, ns, appendage) -> list:
        assert(isinstance(ns, list)), "Namespace isn't list it is %s" % (ns)
        newNs = ns.copy()
        newNs.append(appendage)
        return newNs

    @abc.abstractmethod
    def GetHeader(self, reference: str) -> str:
        pass

    @abc.abstractmethod
    def GetNamespace(self, reference: str, usings=[], append='') -> list:
        pass

    @abc.abstractmethod
    def GetName(self, reference: str) -> str:
        pass


class SimpleResolver(ResolverBaseClass):

    def GetReferenceParts(self, reference):
        pkg = None
        fn = reference.split('#')[0] or None
        path = reference.split('#')[1]
        parts = path.split('/')
        if fn:
            pkg = fn.split('.')[0]
        return (pkg, parts[-2], stringcase.pascalcase(parts[-1]))

    def GetHeader(self, reference):
        pkg, _n, kls = self.GetReferenceParts(reference)
        return "%s%s%s.hpp" % (pkg or '', pkg and '/' or '', stringcase.snakecase(kls))

    def GetNamespace(self, reference, usings=[], append=''):
        pkg, n, _kls = self.GetReferenceParts(reference)
        ns = []
        if pkg is not None:
            ns.append(stringcase.lowercase(pkg))
        ns.append(stringcase.lowercase(n))
        return self.ResolveNamespace(usings, ns, append)

    def GetName(self, reference):
        _pkg, _n, kls = self.GetReferenceParts(reference)
        return stringcase.pascalcase(kls)


class GeneratorFromSchema(object):

    def __init__(self, src_output_dir, header_output_dir, resolver=None, namespace=[], src_usings=[]):
        self.output_dir = {
            "src": src_output_dir,
            "header": header_output_dir,
        }
        self.namespace = namespace
        self.usings = src_usings
        assert(isinstance(resolver, ResolverBaseClass)), "Resolver is %s" % (resolver)
        self.resolver = resolver

    def GetDeps(self, schema):
        return schema.CppIncludes(self.resolver)

    def Generate(self, schema, class_name, filename_base):
        retval = [None, None]
        srcGenerator = templator.Generator('jsonschemacodegen.templates.cpp', self.output_dir['src'])
        headerGenerator = templator.Generator('jsonschemacodegen.templates.cpp', self.output_dir['header'])
        args = {
            "Name": class_name,
            "schema": schemawrappers.SchemaFactory(schema),
        }
        headerFilename = "%s.hpp" % (filename_base)
        if '$ref' not in schema:
            srcFileName = "%s.cpp" % (filename_base)
            srcGenerator.RenderTemplate("source.cpp.jinja2", 
                srcFileName, 
                deps=["\"%s\"" % (headerFilename)], 
                usings=self.usings,
                ns=self.namespace,
                resolver=self.resolver,
                **args)
            retval[0] = srcFileName
        headerGenerator.RenderTemplate("header.hpp.jinja2", 
            headerFilename, 
            ns=self.namespace,
            deps=self.GetDeps(args['schema']), 
            resolver=self.resolver, 
            **args)
        retval[1] = headerFilename
        return tuple(retval)

