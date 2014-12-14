from collections import namedtuple

def merge_into(dict1, dict2):
    return {k:v for d in (dict1, dict2) for k, v in d.items()}

## TODO: Consider 
## Union('List',
##   Type('Cons','h','tl',len=...),
##   Singleton('Empty',len=...),
## This will need setting global Module variables, ...

## TODO: just use Python 3.4 Enum: class Color(Enum): red=1 blue=2 ...
## TODO: just use stylized Python classes, inherit from Field(('x' str), ('y', int))
## Consider defining a Union class parallel to Enum, with classes within it

def Union(name, **methods):
    """Return a Type for use as base with shared 'methods' among
    several Variants """    
    return _Type(name, None, *tuple(), **methods)

def Variant(base, name, *slots_with_types, **methods):
    """Return a Type inheriting from a 'base' ADT with shared methods.
    The new Type is based off a named tuple and the ADT base, and
    adds methods, deep equality (with namedtuple), record update (via __call__),
    and an ADT-like __repr__"""
    return _Type(name, base, *slots_with_types, **methods)

def Singleton(base, name, **methods):
    """Return unique singleton instance of a new anonymous Variant, repr=name"""
    ms = merge_into({'__repr__':lambda self: name}, methods)

    v = Variant(base, "_", **ms)()

    ## TODO: set module globals directly from each function
    # import sys
    # mod = sys.modules[__name__]
    # setattr(mod, name, v)

    return Variant(base, "_", **ms)()


def Type(name, *slots_with_types, **methods):
    """Return a stand-alone Type subclassed from a namedtuple, with
    methods, deep equality, record update (via __call__),
    and an ADT-like __repr__"""
    return _Type(name, None, *slots_with_types, **methods)


def _Type(name, base, *slots_with_types, **methods):
    """Return a new type based of named-tuple type with slots, __annotations__,
    and methods, deep equality, record update, an ADT-like __repr__.
    base can be None, or a Union with shared methods"""
    slots = tuple( 
        [st[0] if isinstance(st, tuple) else st for st in slots_with_types])
    tuplebase = namedtuple(name+"Base", slots)
    bases = (tuplebase, base) if base else (tuplebase,)

    def repr(self):
        vals = ','.join(str(getattr(self, x)) for x in slots)
        return "%s(%s)" % (name, vals)

    ## TODO: remove this; namedtuple already has _replace
    def call(self, **updates):
        attrs = {s: getattr(self, s) for s in slots}
        attrs.update(updates)
        return nt(**attrs)

    def eq(self, other):
        return type(self) == type(other) and tuplebase.__eq__(self, other)

    ms = {'__repr__':repr, '__call__':call, '__eq__':eq}
    mdict = merge_into(ms, methods) #{k:v for d in (ms, methods) for k, v in d.items()}

    ## TODO: possibly elminiate 1 inheritance level
    # grab getattr(tuplebase,'__eq__' for eq-override to avoid circularity
    # just set / modify methods on tuplebase itself
    nt = type(name, bases, mdict)
    nt.__annotations__ = slots_with_types
    return nt


# if __name__ == '__main__':

import typing as T 

Age = int

def bar(self: 'Person', y: int):
    return self.age - y

# Stand-alone Type with some methods
Person = Type('Person',
              ('name', str),
              ('age', Age),
              ('city', T.List[str]),
              ## TODO: BAH!! cannot put type annotations on lambda
              foo=lambda self, x: x + self.age,
              bar=bar)


p = Person('bob', 22, 'austin')

# test equality, repr, annotations, & methods
assert p == Person('bob', 22, 'austin')
assert str(p) == 'Person(bob,22,austin)'
assert p.__annotations__ == (('name', str), ('age', int), ('city', list))
assert p.foo(2) == 24
assert p.bar(2) == 20
bar = p.bar
assert bar(2) == 20

# test record update
p2 = p(age=p.age + 1)
assert p2 == Person('bob', 23, 'austin')
assert p == Person('bob', 22, 'austin')

p3 = p._replace(age=p.age + 5)
assert p3 == Person('bob', 27, 'austin')

# test type with custom __call__ method overrides record update operator
T = Type('T',__call__=lambda self, *x, **k: 42)
t = T()
assert t(w='whatever') == 42

## List = Empty | Cons(a, List(a))
# Union (with shared method)
# of 1 Singleton (Empty) and 1 Variant (Cons) with unique map() and len()
List = Union('List', isList=lambda self: True)
E = Singleton(List, "empty",
    len=lambda self: 0,
    map=lambda self, f: E)
Cons = Variant(List, 'Cons', 'hd', 'tl',
                   len=lambda self: 1 + self.tl.len(),
                   map=lambda self, f: Cons(f(self.hd), self.tl.map(f)))
l2 = Cons(2, Cons(3, E))
assert str(E) == "empty"
assert l2.isList()
assert l2.len() == 2
assert l2.map(lambda x: x * x) == Cons(4, Cons(9, E))
assert isinstance(l2, List)
assert isinstance(l2, Cons)
assert isinstance(E, List)
assert not isinstance(E, Cons)


# Union with shared method & 1 Variant with method
Shape = Union('Shape',
                  show=lambda self: "Shape"
                  )

Rect = Variant(Shape, 'Rect', 'w', 'h',
                   area=lambda self: self.w * self.h
                   )

r = Rect(5, 10)
assert r.show() == "Shape"
assert r.area() == 50

### Peano
Num = Union("Num")
Z = Singleton(Num, "0",
    __add__=lambda self, x: x)
S = Variant(Num, "S", 'n',
    __add__=lambda self, x: self.n + S(x))

_1 = S(Z)
_2 = S(_1)
_3 = S(_2)
assert _3 == S(S(S(Z)))
assert Z + S(Z) == S(Z)
assert _1 + _2 == _3
assert _2 + _1 == _3



