from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import os.path
import stringbender

class CppNamer(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def get_header_path(self, source_uri: str, json_path: str, doc: "Document") -> str:
        """
        Constructs a path for a header file.

        For example, given the inputs, this might return something like:
        `/usr/local/include/myschema/definitions/foobar.hpp`.

        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: This is the parsed YAML/JSON file.
        :returns: path to header file.
        """

    @abstractmethod
    def get_source_path(self, source_uri: str, json_path: str) -> str:
        """
        Constructs a path for a source file.

        For example, given the inputs, this might return something like:
        `/usr/local/src/myschema/foobar.cpp`

        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: This is the parsed YAML/JSON file.
        """

    @abstractmethod
    def get_object_name(self, source_uri: str, json_path: str) -> str:
        """
        Constructs the name of an object, including namespaces.

        For example, given the inputs, this might return something like:
        `myschema::definitions::FooBar`.

        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: This is the parsed YAML/JSON file.
        """

    @abstractmethod
    def get_include_path(self, source_uri: str, json_path: str) -> str:
        """
        Constructs an include path for C++ to include a header file.

        This is everything after the include statement, and could be:
        `"definitions/foobar.hpp"` or `<myschema/definitions/foobar.hpp>`

        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: This is the parsed YAML/JSON file.
        """

    @abstractmethod
    def get_util_source_path(self, util_name: str) -> str:
        pass

    @abstractmethod
    def get_util_header_path(self, util_name: str) -> str:
        pass

    @abstractmethod
    def get_util_include_path(self, util_name: str) -> str:
        pass

    @abstractmethod
    def get_util_namespace(self, object_name:Optional[str]=None) -> List[str]:
        pass

    def write_file_indexes(self, source_files: List[str], header_files: List[str]):
        """
        In this class, this method does nothing, but is called after writing all the source files and headers.

        Depending on your build system, you may need to have a list of the files created.  In this case, you
        can override this method in your inheriting class and have it write whatever files you need.

        """

    def get_namespace(self, source_uri: str, json_path: str) -> List[str]:
        full_name = self.get_object_name(source_uri, json_path)
        if "::" in full_name:
            return full_name.split("::")[:-1]
        return []

    def get_class_name(self, uri, path) -> str:
        full_class_name = self.get_object_name(uri, path)
        return full_class_name.split("::")[-1]

    @staticmethod
    def split_reference(ref) -> Tuple[str, str]:
        return ref.split("#")


class GeneralCppNamer(CppNamer):

    def __init__(self, base_dir):
        super().__init__()
        self._base_dir = base_dir

    def get_header_path(self, source_uri: str, json_path: str, doc) -> str:
        """
        Constructs a path for a header file.

        This will return a path consisting of the `base_dir`, the name of the schema file, and the last bits
        of the json path.

        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: Is unused
        """
        source_filename = source_uri.split(os.path.sep)[-1]
        module_name = source_filename.split('.')[0]
        json_path_parts = json_path.split('/')
        fn = os.path.join(self._base_dir, "include", module_name, "{}.hpp".format("_".join([ pp.lower() for pp in json_path_parts[-2:] ])))
        return fn

    def get_source_path(self, source_uri: str, json_path: str) -> str:
        """
        Constructs a path for a source file.
        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: Is unused.
        """
        json_path_parts = json_path.split('/')
        joined_path_parts = "_".join([ pp.lower() for pp in json_path_parts[-2:] ])
        filename = os.path.join(self._base_dir, "src", "{}.cpp".format(joined_path_parts))
        return filename

    def get_object_name(self, source_uri: str, json_path: str) -> str:
        """
        Constructs a path for a source file.
        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: Is unused.
        """
        source_filename = source_uri.split(os.path.sep)[-1]
        module_name = source_filename.split('.')[0]
        json_path_parts = json_path.split('/')
        obj_parts = [module_name]
        if len(json_path_parts) >= 2:
            obj_parts.append(json_path_parts[-2].lower())
        obj_parts.append(stringbender.pascal(json_path_parts[-1]))
        obj_name = "::".join(obj_parts)
        return obj_name

    def get_include_path(self, source_uri: str, json_path: str) -> str:
        """
        Constructs a path for a source file.
        :param source_uri: This is a URI to a JSON/YAML file.  Normally it might be just a filesystem path.
        :param json_path: This is the JSON path into the document to a particular schema definition.
        :param doc: Is unused.
        """
        source_filename = source_uri.split(os.path.sep)[-1]
        module_name = source_filename.split('.')[0]
        json_path_parts = json_path.split('/')
        joined_path_parts = "_".join([ pp.lower() for pp in json_path_parts[-2:] ])
        filename = os.path.join(module_name, "{}.hpp".format(joined_path_parts))
        return f'"{filename}"'

    def get_util_source_path(self, util_name: str) -> str:
        filepath = os.path.join(self._base_dir, "src", f"util_{util_name}.cpp")
        return filepath

    def get_util_header_path(self, util_name: str) -> str:
        filepath = os.path.join(self._base_dir, "include", "util", f"{util_name}.hpp")
        return filepath

    def get_util_include_path(self, util_name: str) -> str:
        return f'"util/{util_name}.hpp"'

    def get_util_namespace(self, object_name:Optional[str]=None) -> List[str]:
        ns_arr = ["util"]
        if object_name is not None:
            ns_arr.append(object_name)
        return ns_arr