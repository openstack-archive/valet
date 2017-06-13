#
# Copyright 2014-2017 AT&T Intellectual Property
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Music ORM - Common Methods"""

from abc import ABCMeta
from abc import abstractmethod
from importlib import import_module
import inspect
import os
import pkgutil
import uuid

from pecan import conf
import six

from valet import api
from valet.api.common.i18n import _
from valet.common.music import Music


def get_class(kls):
    """Returns a class given a fully qualified class name"""
    pkg_path = os.path.dirname(__file__)
    for loader, mod_name, is_pkg in pkgutil.iter_modules([pkg_path]):
        mod = import_module('valet.api.db.models.music.' + mod_name)
        cls = getattr(mod, kls, None)
        if cls:
            return cls
    return None


class abstractclassmethod(classmethod):  # pylint: disable=C0103,R0903
    """Abstract Class Method from Python 3.3's abc module"""

    __isabstractmethod__ = True

    def __init__(self, callable):  # pylint: disable=W0622
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


class ClassPropertyDescriptor(object):  # pylint: disable=R0903
    """Supports the notion of a class property"""

    def __init__(self, fget, fset=None):
        """Initializer"""
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        """Get attribute"""
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        """Set attribute"""
        if not self.fset:
            raise AttributeError(_("Can't set attribute"))
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        """Setter"""
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func):
    """Class Property decorator"""
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


class Results(list):
    """Query results"""

    def __init__(self, *args, **kwargs):  # pylint: disable=W0613
        """Initializer"""
        super(Results, self).__init__(args[0])

    def all(self):
        """Return all"""
        return self

    def first(self):
        """Return first"""
        if len(self) > 0:
            return self[0]


@six.add_metaclass(ABCMeta)
class Base(object):
    """Custom declarative base that provides some Elixir-inspired shortcuts."""

    __tablename__ = None

    @classproperty
    def query(cls):  # pylint: disable=E0213
        """Return a query object a la sqlalchemy"""
        return Query(cls)

    @classmethod
    def __kwargs(cls):
        """Return common keyword args"""
        keyspace = conf.music.get('keyspace')
        kwargs = {
            'keyspace': keyspace,
            'table': cls.__tablename__,
        }
        return kwargs

    @classmethod
    def create_table(cls):
        """Create table"""
        kwargs = cls.__kwargs()
        kwargs['schema'] = cls.schema()
        conf.music.engine.create_table(**kwargs)

    @abstractclassmethod
    def schema(cls):
        """Return schema"""
        return cls()

    @abstractclassmethod
    def pk_name(cls):
        """Primary key name"""
        return cls()

    @abstractmethod
    def pk_value(self):
        """Primary key value"""
        pass

    @abstractmethod
    def values(self):
        """Values"""
        pass

    def insert(self):
        """Insert row"""
        kwargs = self.__kwargs()
        kwargs['values'] = self.values()
        pk_name = self.pk_name()
        if pk_name not in kwargs['values']:
            the_id = str(uuid.uuid4())
            kwargs['values'][pk_name] = the_id
            setattr(self, pk_name, the_id)
        conf.music.engine.create_row(**kwargs)

    def update(self):
        """Update row"""
        kwargs = self.__kwargs()
        kwargs['pk_name'] = self.pk_name()
        kwargs['pk_value'] = self.pk_value()
        kwargs['values'] = self.values()
        conf.music.engine.update_row_eventually(**kwargs)

    def delete(self):
        """Delete row"""
        kwargs = self.__kwargs()
        kwargs['pk_name'] = self.pk_name()
        kwargs['pk_value'] = self.pk_value()
        conf.music.engine.delete_row_eventually(**kwargs)

    @classmethod
    def filter_by(cls, **kwargs):
        """Filter objects"""
        return cls.query.filter_by(**kwargs)  # pylint: disable=E1101

    def flush(self, *args, **kwargs):
        """Flush changes to storage"""
        # TODO(JD): Implement in music? May be a no-op
        pass

    def as_dict(self):
        """Return object representation as a dictionary"""
        return dict((k, v) for k, v in self.__dict__.items()
                    if not k.startswith('_'))


class Query(object):
    """Data Query"""
    model = None

    def __init__(self, model):
        """Initializer"""
        if inspect.isclass(model):
            self.model = model
        elif isinstance(model, basestring):
            self.model = get_class(model)
        assert inspect.isclass(self.model)

    def __kwargs(self):
        """Return common keyword args"""
        keyspace = conf.music.get('keyspace')
        kwargs = {
            'keyspace': keyspace,
            'table': self.model.__tablename__,  # pylint: disable=E1101
        }
        return kwargs

    def __rows_to_objects(self, rows):
        """Convert query response rows to objects"""
        results = []
        pk_name = self.model.pk_name()  # pylint: disable=E1101
        for __, row in rows.iteritems():  # pylint: disable=W0612
            the_id = row.pop(pk_name)
            result = self.model(_insert=False, **row)
            setattr(result, pk_name, the_id)
            results.append(result)
        return Results(results)

    def all(self):
        """Return all objects"""
        kwargs = self.__kwargs()
        rows = conf.music.engine.read_all_rows(**kwargs)
        return self.__rows_to_objects(rows)

    def all_matching_key(self, key=None, value=None):
        '''Return all objects matching a particular key/value'''
        if not key:
            key = self.model.pk_name()
        kwargs = self.__kwargs()
        rows = conf.music.engine.read_row(
            pk_name=key, pk_value=value, **kwargs)
        return self.__rows_to_objects(rows)

    def filter_by(self, **kwargs):
        """Filter objects"""

        # Music doesn't allow filtering on anything but the primary key.
        # This leads to a default O(n) filtering algorithm. However, we
        # can make it O(1) in some cases.
        if len(kwargs) == 1:
            # *Iff* a secondary key has been manually made via cql, e.g.:
            #   CREATE INDEX ON keyspace.table (field);
            # and that field/value is the only one in kwargs, we'll try it.
            key = kwargs.keys()[0]
            value = kwargs[key]
            try:
                filtered_items = self.all_matching_key(key=key, value=value)
                return filtered_items
            except Exception:
                # If there's any kind of exception, we will take that
                # to mean there was no primary/secondary key (though
                # there can be other reasons). In this case, passthrough
                # and use the original O(n) filtering method.
                #
                # Not logging in this module just yet. (Never use print()!)
                pass

        # We need to get all items and then go looking for what we want.
        all_items = self.all()
        filtered_items = Results([])

        # For every candidate ...
        for item in all_items:
            passes = True
            # All filters are AND-ed.
            for key, value in kwargs.items():
                if getattr(item, key) != value:
                    passes = False
                    break
            if passes:
                filtered_items.append(item)
        return filtered_items


def init_model():
    """Data Store Initialization"""
    conf.music.engine = _engine_from_config(conf.music)
    keyspace = conf.music.get('keyspace')
    conf.music.engine.create_keyspace(keyspace)


def _engine_from_config(configuration):
    """Create database engine object based on configuration"""
    configuration = dict(configuration)
    kwargs = {
        'hosts': configuration.get('hosts'),
        'port': configuration.get('port'),
        'replication_factor': configuration.get('replication_factor'),
        'music_server_retries': configuration.get('music_server_retries'),
        'logger': api.LOG,
    }
    return Music(**kwargs)


def start():
    """Start transaction"""
    pass


def start_read_only():
    """Start read-only transaction"""
    start()


def commit():
    """Commit transaction"""
    pass


def rollback():
    """Rollback transaction"""
    pass


def clear():
    """Clear transaction"""
    pass


def flush():
    """Flush to disk"""
    pass
