# Copyright 2018 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import collections.abc as abc
import io
import warnings

from numbers import Integral, Number
from operator import eq
from pprint import PrettyPrinter

from dimod.cyvariables import cyVariables
from dimod.decorators import lockable_method


__all__ = ['Variables']


def iter_serialize_variables(variables):
    # want to handle things like numpy numbers and fractions that do not
    # serialize so easy
    for v in variables:
        if isinstance(v, Integral):
            yield int(v)
        elif isinstance(v, Number):
            yield float(v)
        elif isinstance(v, str):
            yield v
        # we want Collection, but that's not available in py3.5
        elif isinstance(v, (abc.Sequence, abc.Set)):
            yield tuple(iter_serialize_variables(v))
        else:
            yield v


def iter_deserialize_variables(variables):
    # convert list back into tuples
    for v in variables:
        # we want Collection, but that's not available in py3.5
        if isinstance(v, (abc.Sequence, abc.Set)) and not isinstance(v, str):
            yield tuple(iter_deserialize_variables(v))
        else:
            yield v


class Variables(cyVariables, abc.Set, abc.Sequence):
    """Set-like and list-like variables tracking.

    Args:
        iterable (iterable):
            An iterable of labels. Duplicate labels are ignored. All labels
            must be hashable.

    """
    def __eq__(self, other):
        if isinstance(other, abc.Sequence):
            return len(self) == len(other) and all(map(eq, self, other))
        elif isinstance(other, abc.Set):
            return not (self ^ other)
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        stream = io.StringIO()
        stream.write(type(self).__name__)
        stream.write('(')
        if self:
            if self.is_range and len(self) > 10:
                # 10 is arbitrary, but the idea is we want to truncate
                # longer variables that are integer-labelled
                stream.write(repr(range(len(self))))
            else:
                stream.write('[')
                iterator = iter(self)
                stream.write(repr(next(iterator)))
                for v in iterator:
                    stream.write(', ')
                    stream.write(repr(v))
                stream.write(']')
        stream.write(')')
        return stream.getvalue()

    @property
    def is_range(self):
        return self._is_range()

    def to_serializable(self):
        """Return an object that (should be) json-serializable.

        Returns:
            list: A list of (hopefully) json-serializable objects. Handles some
            common cases like NumPy scalars.
            See :func:`iter_serialize_variables`.

        """
        return list(iter_serialize_variables(self))


# register the various objects with prettyprint
def _pprint_variables(printer, variables, stream, indent, *args, **kwargs):
    if not variables or variables.is_range:
        stream.write(repr(variables))
    else:
        indent += stream.write(type(variables).__name__)
        indent += stream.write('(')
        printer._pprint_list(variables, stream, indent, *args, **kwargs)
        indent += stream.write(')')


try:
    PrettyPrinter._dispatch[Variables.__repr__] = _pprint_variables
except AttributeError:
    # we're using some internal stuff in PrettyPrinter so let's silently fail
    # for that
    pass
