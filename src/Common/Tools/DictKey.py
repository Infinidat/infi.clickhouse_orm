# -*- coding: utf-8 -*-


def find_value_fromdict_listkey(dict_a, find_key, result):
    assert isinstance(dict_a, dict), "dict_a is not type(dict)"
    assert isinstance(find_key, list), "find_key is not type(list)"
    if isinstance(find_key, list):
        for x in range(len(dict_a)):
            temp_key = dict_a.keys()[x]
            temp_value = dict_a[temp_key]
            if temp_key in find_key:
                result[temp_key] = temp_value
            elif isinstance(temp_value, dict):
                find_value_fromdict_listkey(temp_value, find_key, result)
            else:
                continue
        values = []
        [values.append(result.get(key, None)) for key in find_key]
        return values


def find_value_fromdict_singlekey(dict_a, find_key):
    assert isinstance(dict_a, dict), "dict_a is not type(dict)"
    if find_key in dict_a:
        return dict_a[find_key]
    for x in range(len(dict_a)):
        temp_key = dict_a.keys()[x]
        temp_value = dict_a[temp_key]
        if isinstance(temp_value, dict):
            result = find_value_fromdict_singlekey(temp_value, find_key)
            if result != None:
                return result
        else:
            continue

if __name__ == "__main__":
    a = {1: 0, 2: 0, 3: 0, 4: 0}
    result = {}
    find_value_fromdict_listkey(a, a.keys(), result)
    print result