#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

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
        """
        :return: returns list of all LWM2M objects present in this model.
        """
        return [x for x in sorted([int(i) for i in self.data.keys()])]

    def instances(self, obj):
        """
        :param obj: object ID to get instances for
        :return: list of all instances of the given object present in this model.
        """
        _insts = self.data[str(obj)]
        return [x for x in sorted([int(i) for i in _insts.keys()])]

    def resources(self, obj, inst=0):
        """
        :param obj: object ID to get resources for
        :param inst: instance ID to get resources for
        :return: list of all resources of the given object ID/instance ID
        """
        return [x for x in sorted([int(i) for i in self.data[str(obj)][str(inst)].keys()])]

    def resource(self, obj, inst, res):
        """
        Retrieves a specific resource for the given object ID, instance ID, resource ID.
        :param obj: object ID
        :param inst: instance ID
        :param res: resource ID
        :return: resource for the given path
        """
        return self.data[str(obj)][str(inst)][str(res)]

    def has_definition(self, obj):
        """
        :param obj: object ID to check
        :return: True, if the given object ID is present in this client model.
        """
        return str(obj) in self.definition.keys()

    def is_object_multi_instance(self, obj):
        """
        Check if an object is a multi-instance object according to the existing definition.
        :param obj: object ID to check
        :return: True, if the given object ID is defined as a multi-instance object.
        """
        return self.definition[str(obj)]["instancetype"] == "multiple"

    def is_resource_multi_instance(self, obj, inst, res):
        """
        Check if a resource is a multi-instance resource according to the existing definition.
        :param obj: object ID
        :param inst: instance ID
        :param res: resource ID
        :return: True, if a resource defined for object ID + instance ID + resource ID is a multi-instance resource.
        """
        return self.definition[str(obj)]["resourcedefs"][str(res)]["instancetype"] == "multiple"

    def instance_iter(self):
        """
        Generator which generates a list of tuples of all object instances contained in the data, e.g.:
        [('1','0'),('3','0'),('6','0') ... ]
        :return: list of tuples of all object instances
        """
        for obj in self.objects():
            for inst in self.instances(obj):
                yield (str(obj), str(inst))

    def resource_iter(self):
        """
        Generator which generates a list of tuples of all resources contained in the data, e.g.:
        [('1','0','0'),('1','0','1'), ... ]
        :return: list of tuples of all resources
        """
        for obj in self.objects():
            for inst in self.instances(obj):
                for res in self.resources(obj, inst):
                    yield (str(obj), str(inst), str(res))

    def get_object_links(self):
        """
        Generator which can be used to create a list of object links (as presented in the client's registration),
        in form of </objectID/instanceID>, ...
        :return: a generator producing object links
        """
        for obj in self.objects():
            for inst in self.instances(obj):
                yield "</%s/%s>" % (obj, inst)

    def is_path_valid(self, path):
        """
        Checks if a given path tuple (objectID, instanceID, resourceID) is valid.
        :param path: path to check
        :return: True, if the given path is valid.
        """
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
        """
        Checks if the resource represented by the given objectID/instanceID/resourceID is readable.
        :param obj: object ID
        :param inst: instance ID
        :param res: resource ID
        :return: True, if the resource is readable.
        """
        _ops = self.definition[str(obj)]["resourcedefs"][str(res)]["operations"]
        return False if _ops == "NONE" else "R" in _ops

    def is_resource_writable(self, obj, inst, res):
        """
        Checks if the resource represented by the given objectID/instanceID/resourceID is writable.
        :param obj: object ID
        :param inst: instance ID
        :param res: resource ID
        :return: True, if the resource is writable.
        """
        _ops = self.definition[str(obj)]["resourcedefs"][str(res)]["operations"]
        return False if _ops == "NONE" else "W" in _ops

    def is_resource_executable(self, obj, inst, res):
        """
        Checks if the resource represented by the given objectID/instanceID/resourceID is executable.
        :param obj: object ID
        :param inst: instance ID
        :param res: resource ID
        :return: True, if the resource is executable.
        """
        _ops = self.definition[str(obj)]["resourcedefs"][str(res)]["operations"]
        return False if _ops == "NONE" else "E" in _ops

    def set_resource(self, obj, inst, res, content):
        """
        Sets the data of the resource for given objectID/instanceID/resourceID.
        :param obj: object ID
        :param inst: instance ID
        :param res: resource ID
        :param content: content of the resource to set
        :return:
        """
        if self.is_resource_writable(obj, inst, res):
            self.data[str(obj)][str(inst)][str(res)] = content

    def apply(self, data):
        """
        Applies one or more resources to the data model.
        :param data: resources to change, must follow the format:
                 { objectID : { instanceID : { resourceID : "content" }}}
        :return:
        """
        assert isinstance(data, dict), "data must be a dict"
        for obj in data.keys():
            for inst in data[obj].keys():
                for res in data[obj][inst].keys():
                    log.debug("applying %s/%s/%s = %s" % (obj, inst, res, data[obj][inst][res]))
                    self.set_resource(obj, inst, res, data[obj][inst][res])
