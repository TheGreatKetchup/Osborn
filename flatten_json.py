#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This code is originally from https://github.com/amirziai/flatten

# This version is saved for stability, and because custom changes were needed
# to make this serve our purpose.

# Changed by Matthew Schweiss
from collections import Iterable
from collections import OrderedDict

##from util import check_if_numbers_are_consecutive
# Sorry, I don't see why this deserves it's own modules, taking up the
# namespace of "util".
def check_if_numbers_are_consecutive(list_):
    """
    Returns True if numbers in the list are consecutive

    :param list_: list of integers
    :return: Boolean
    """
    return all([True if second - first == 1 else False
                for first, second in zip(list_[:-1], list_[1:])])

def _construct_key(previous_key, separator, new_key):
    """
    Returns the new_key if no previous key exists, otherwise concatenates previous key, separator, and new_key
    :param previous_key:
    :param separator:
    :param new_key:
    :return: a string if previous_key exists and simply passes through the new_key otherwise
    """
    if previous_key:
        return "{}{}{}".format(previous_key, separator, new_key)
    else:
        return new_key


def flatten(nested_dict, separator="_", root_keys_to_ignore=set(), preserve_order = False, _construct_key = _construct_key):
    """
    Flattens a dictionary with nested structure to a dictionary with no hierarchy
    Consider ignoring keys that you are not interested in to prevent unnecessary processing
    This is specially true for very deep objects

    :param nested_dict: dictionary we want to flatten
    :param separator: string to separate dictionary keys by
    :param root_keys_to_ignore: set of root keys to ignore from flattening
    :return: flattened dictionary
    """
    assert isinstance(nested_dict, dict), "flatten requires a dictionary input"
    assert isinstance(separator, str), "separator must be a string"

    # This global dictionary stores the flattened keys and values and is ultimately returned
    flattened_dict = dict() if not preserve_order else OrderedDict()

    def _flatten(object_, key):
        """
        For dict, list and set objects_ calls itself on the elements and for other types assigns the object_ to
        the corresponding key in the global flattened_dict
        :param object_: object to flatten
        :param key: carries the concatenated key for the object_
        :return: None
        """
        if isinstance(object_, dict):
            for object_key in object_:
                if not (not key and object_key in root_keys_to_ignore):
                    _flatten(object_[object_key], _construct_key(key, separator, object_key))
        elif isinstance(object_, list) or isinstance(object_, set):
            for index, item in enumerate(object_):
                _flatten(item, _construct_key(key, separator, index))
        else:
            flattened_dict[key] = object_

    _flatten(nested_dict, None)
    return flattened_dict

flatten_json = flatten


def _unflatten_asserts(flat_dict, separator):
    assert isinstance(flat_dict, dict), "un_flatten requires a dictionary input"
    assert isinstance(separator, str), "separator must be a string"
    assert all((not isinstance(value, Iterable) or isinstance(value, str)
                for value in flat_dict.values())), "provided dictionary is not flat"


def unflatten(flat_dict, separator='_'):
    """
    Creates a hierarchical dictionary from a flattened dictionary
    Assumes no lists are present
    :param flat_dict: a dictionary with no hierarchy
    :param separator: a string that separates keys
    :return: a dictionary with hierarchy
    """
    _unflatten_asserts(flat_dict, separator)

    # This global dictionary is mutated and returned
    unflattened_dict = dict()

    def _unflatten(dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})

        dic[keys[-1]] = value

    for item in flat_dict:
        _unflatten(unflattened_dict, item.split(separator), flat_dict[item])

    return unflattened_dict


def unflatten_list(flat_dict, separator='_'):
    """
    Unflattens a dictionary, first assuming no lists exist and then tries to identify lists and replaces them
    This is probably not very efficient and has not been tested extensively
    Feel free to add test cases or rewrite the logic
    Issues that stand out to me:
    - Sorting all the keys in the dictionary, which specially for the root dictionary can be a lot of keys
    - Checking that numbers are consecutive is O(N) in number of keys

    :param flat_dict: dictionary with no hierarchy
    :param separator: a string that separates keys
    :return: a dictionary with hierarchy
    """
    _unflatten_asserts(flat_dict, separator)

    # First unflatten the dictionary assuming no lists exist
    unflattened_dict = unflatten(flat_dict, separator)

    def _convert_dict_to_list(object_, parent_object, parent_object_key):
        if isinstance(object_, dict):
            try:
                keys = [int(key) for key in object_]
                keys.sort()
            except (ValueError, TypeError):
                keys = []
            keys_len = len(keys)

            if (keys_len > 0 and sum(keys) == int(((keys_len - 1) * keys_len) / 2) and keys[0] == 0 and
                    keys[-1] == keys_len - 1 and check_if_numbers_are_consecutive(keys)):
                # The dictionary looks like a list so we're going to replace it as one
                parent_object[parent_object_key] = [object_[str(key)] for key in keys]

            for key in object_:
                if isinstance(object_[key], dict):
                    _convert_dict_to_list(object_[key], object_, key)

    _convert_dict_to_list(unflattened_dict, None, None)
    return unflattened_dict
