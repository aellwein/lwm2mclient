#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from json import load

log = logging.getLogger("model")


class DefinitionFileLoader(object):
    """
    This loader is responsible for loading object definition to the client from a JSON file.
    """

    def __init__(self, definition_file="lwm2m-object-definitions.json"):
        """
        Creates a new JSON definition file loader.
        :param definition_file: JSON definition file to load.
        """
        assert isinstance(definition_file, str), "definition file must be a string"
        self.definition_file = definition_file

    def load(self):
        """
        Loads JSON definition file.
        :return: dictionary containing object definitions.
        """
        with open(self.definition_file) as f:
            return load(f)


class DataFileLoader(object):
    """
    This loader is responsible for loading object data to the client from a JSON file.
    """

    def __init__(self, data_file="data.json"):
        """
        Creates a new JSON data file loader.
        :param data_file: JSON data file
        """
        assert isinstance(data_file, str), "data file must be a string"
        self.data_file = data_file

    def load(self):
        """
        Loads LWM2M object data from a JSON file.
        :return: dictionary containing LWM2M object data.
        """
        with open(self.data_file) as f:
            return load(f)


class ClientModel(object):
    """
    A client model holds the data which is used by the LWM2M client.
    """
    def __init__(self, definition_loader=DefinitionFileLoader(), data_loader=DataFileLoader()):
        """
        Creates a new client model using given definition and data loaders.
        :param definition_loader: definition loader, loads from a JSON file "lwm2m-object-definitions.json" by default
        :param data_loader: data loader, loads from a JSON file "data.json" by default.
        """
        self.definition = definition_loader.load()
        self.data = data_loader.load()
        # simple validation: check if all data objects are in the definition
        for obj in self.objects():
            if not self.has_definition(obj):
                raise AttributeError("data file contains undefined object with ID %s. Aborting." % obj)

    def objects(self):
        return [x for x in sorted([int(i) for i in self.data.keys()])]

    def instances(self, obj):
        _insts = self.data[str(obj)]
        return [x for x in sorted([int(i) for i in _insts.keys()])]

    def resources(self, obj, inst=0):
        return [x for x in sorted([int(i) for i in self.data[str(obj)][str(inst)].keys()])]

    def resource(self, obj, inst, res):
        return self.data[str(obj)][str(inst)][str(res)]

    def has_definition(self, obj):
        return str(obj) in self.definition.keys()

    def is_object_multi_instance(self, obj):
        return self.definition[str(obj)]["instancetype"] == "multiple"

    def is_resource_multi_instance(self, obj, inst, res):
        return self.definition[str(obj)]["resourcedefs"][str(res)]["instancetype"] == "multiple"

    def resource_iter(self):
        for obj in self.objects():
            for inst in self.instances(obj):
                for res in self.resources(obj, inst):
                    yield (str(obj), str(inst), str(res))

    def instance_iter(self):
        for obj in self.objects():
            for inst in self.instances(obj):
                yield (str(obj), str(inst))

    def get_object_links(self):
        for obj in self.objects():
            for inst in self.instances(obj):
                yield "</%s/%s>" % (obj, inst)

    def is_path_valid(self, path):
        assert isinstance(path, tuple), "should be a tuple"
        for i in path:
            assert isinstance(i, int), "'{}' should be an int value".format(i)
        if len(path) == 3:
            _obj = int(path[0])
            _inst = int(path[1])
            _res = int(path[2])
            return _obj in self.objects() and _inst in self.instances(_obj) and _res in self.resources(_obj, _inst)
        elif len(path) == 2:
            _obj = int(path[0])
            _inst = int(path[1])
            return _obj in self.objects() and _inst in self.instances(_obj)
        elif len(path) == 1:
            _obj = int(path[0])
            return _obj in self.objects()
        else:
            raise AttributeError("invalid path length: %d." % len(path))

    def is_resource_readable(self, obj, inst, res):
        _ops = self.definition[obj]["resourcedefs"][str(res)]["operations"]
        return False if _ops == "NONE" else "R" in _ops

    def is_resource_executable(self, obj, inst, res):
        _ops = self.definition[obj]["resourcedefs"][str(res)]["operations"]
        return False if _ops == "NONE" else "E" in _ops

    def set_resource(self, obj, inst, res, content):
        self.data[str(obj)][str(inst)][str(res)] = content

    def apply(self, data):
        assert isinstance(data, dict), "data must be a dict"
        for obj in data.keys():
            for inst in data[obj].keys():
                for res in data[obj][inst].keys():
                    log.debug("applying %s/%s/%s = %s" % (obj, inst, res, data[obj][inst][res]))
                    self.set_resource(obj, inst, res, data[obj][inst][res])
