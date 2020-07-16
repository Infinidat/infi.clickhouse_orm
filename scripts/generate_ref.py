
import inspect
from collections import namedtuple

DefaultArgSpec = namedtuple('DefaultArgSpec', 'has_default default_value')

def _get_default_arg(args, defaults, arg_index):
    """ Method that determines if an argument has default value or not,
    and if yes what is the default value for the argument

    :param args: array of arguments, eg: ['first_arg', 'second_arg', 'third_arg']
    :param defaults: array of default values, eg: (42, 'something')
    :param arg_index: index of the argument in the argument array for which,
    this function checks if a default value exists or not. And if default value
    exists it would return the default value. Example argument: 1
    :return: Tuple of whether there is a default or not, and if yes the default
    value, eg: for index 2 i.e. for "second_arg" this function returns (True, 42)
    """
    if not defaults:
        return DefaultArgSpec(False, None)

    args_with_no_defaults = len(args) - len(defaults)

    if arg_index < args_with_no_defaults:
        return DefaultArgSpec(False, None)
    else:
        value = defaults[arg_index - args_with_no_defaults]
        if (type(value) is str):
            value = '"%s"' % value
        return DefaultArgSpec(True, value)

def get_method_sig(method):
    """ Given a function, it returns a string that pretty much looks how the
    function signature would be written in python.

    :param method: a python method
    :return: A string similar describing the pythong method signature.
    eg: "my_method(first_argArg, second_arg=42, third_arg='something')"
    """

    # The return value of ArgSpec is a bit weird, as the list of arguments and
    # list of defaults are returned in separate array.
    # eg: ArgSpec(args=['first_arg', 'second_arg', 'third_arg'],
    # varargs=None, keywords=None, defaults=(42, 'something'))
    argspec = inspect.getargspec(method)
    arg_index=0
    args = []

    # Use the args and defaults array returned by argspec and find out
    # which arguments has default
    for arg in argspec.args:
        default_arg = _get_default_arg(argspec.args, argspec.defaults, arg_index)
        if default_arg.has_default:
            val = default_arg.default_value
            args.append("%s=%s" % (arg, val))
        else:
            args.append(arg)
        arg_index += 1
    if argspec.varargs:
        args.append('*' + argspec.varargs)
    if argspec.keywords:
        args.append('**' + argspec.keywords)
    return "%s(%s)" % (method.__name__, ", ".join(args[1:]))


def docstring(obj):
    doc = (obj.__doc__ or '').rstrip()
    if doc:
        lines = doc.split('\n')
        # Find the length of the whitespace prefix common to all non-empty lines
        indentation = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
        # Output the lines without the indentation
        for line in lines:
            print(line[indentation:])
        print()


def class_doc(cls, list_methods=True):
    bases = ', '.join([b.__name__ for b in cls.__bases__])
    print('###', cls.__name__)
    print()
    if bases != 'object':
        print('Extends', bases)
        print()
    docstring(cls)
    for name, method in inspect.getmembers(cls, lambda m: inspect.ismethod(m) or inspect.isfunction(m)):
        if name == '__init__':
            # Initializer
            print('####', get_method_sig(method).replace(name, cls.__name__))
        elif name[0] == '_':
            # Private method
            continue
        elif hasattr(method, '__self__') and method.__self__ == cls:
            # Class method
            if not list_methods:
                continue
            print('#### %s.%s' % (cls.__name__, get_method_sig(method)))
        else:
            # Regular method
            if not list_methods:
                continue
            print('####', get_method_sig(method))
        print()
        docstring(method)
        print()


def module_doc(classes, list_methods=True):
    mdl = classes[0].__module__
    print(mdl)
    print('-' * len(mdl))
    print()
    for cls in classes:
        class_doc(cls, list_methods)


def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in all_subclasses(s)]


if __name__ == '__main__':

    from infi.clickhouse_orm import database
    from infi.clickhouse_orm import fields
    from infi.clickhouse_orm import engines
    from infi.clickhouse_orm import models
    from infi.clickhouse_orm import query
    from infi.clickhouse_orm import funcs
    from infi.clickhouse_orm import system_models

    print('Class Reference')
    print('===============')
    print()
    module_doc([database.Database, database.DatabaseException])
    module_doc([models.Model, models.BufferModel, models.MergeModel, models.DistributedModel, models.Constraint, models.Index])
    module_doc(sorted([fields.Field] + all_subclasses(fields.Field), key=lambda x: x.__name__), False)
    module_doc([engines.Engine] + all_subclasses(engines.Engine), False)
    module_doc([query.QuerySet, query.AggregateQuerySet, query.Q])
    module_doc([funcs.F])
    module_doc([system_models.SystemPart])
