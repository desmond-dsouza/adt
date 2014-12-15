from collections import namedtuple

def merge_into(dict1, dict2):
    return {k:v for d in (dict1, dict2) for k, v in d.items()}

def Record(*slots_with_types):
    slots = tuple( 
        [s_t[0] if isinstance(s_t, tuple) else s_t for s_t in slots_with_types])
    tuplebase = namedtuple("_".join(slots), slots)
    base_eq = getattr(tuplebase, '__eq__')

    def repr(self):
        vals = ','.join(str(getattr(self, x)) for x in slots)
        return "%s(%s)" % (type(self).__name__, vals)

    def eq(self, other):
        return type(self) == type(other) and base_eq(self, other)

    setattr(tuplebase, '__repr__', repr)
    setattr(tuplebase, '__eq__', eq)

    tuplebase.__annotations__ = slots_with_types
    return tuplebase

##### tests

class Person(Record(('name', str), ('age', int))):
    def walk(self): return "Walk"

p = Person('bob', 22)
assert str(p) == 'Person(bob,22)'
assert p == Person('bob', 22)
assert not p == ('bob', 22)
assert p._replace(age=p.age + 1) == Person('bob',23)
assert Person.__annotations__ == (('name', str), ('age', int))

##### end tests

### HACK: to allow __bases__ to be assigned http://goo.gl/XkbBv3
class Variant(object): pass
# class object(object): pass

class Union(type):
    def __init__(self, name, bases, attrs):
        # def variant(v):
        #     return type(v.__name__, tuple(list(v.__bases__) + [self]), dict(v.__dict__))
        # self.variants = [variant(v) for k, v in attrs.items() if isinstance(v, type)]
        # for v in self.variants: 
        #     setattr(self, v.__name__, v)
        ## super(Meta, self).__init__(name, bases, attrs)
        for k, v in attrs.items(): 
            if isinstance(v, type): 
                v.__bases__ = tuple(list(v.__bases__) + [self])

class Shape(metaclass=Union):
    def shared(self): return "I am a Shape"

    class Rect(Record(('x', int), ('y', int))):
        def area(self): return self.x * self.y
        def peri(self): return 2 * (self.x + self.y)

    class Circle(Record('r')):
        import math
        def area(self): return math.pi * self.r * self.r
        def peri(self): return 2 * math.pi * self.r

Rect = Shape.Rect
Circle = Shape.Circle

r = Rect(10, 20)
c = Circle(20)

assert isinstance(r, Shape)
assert isinstance(r, Shape.Rect)
assert not isinstance(c, Shape.Rect)
isinstance(0, Shape.Circle)
assert isinstance(Circle(4), Shape)
assert r.shared() == "I am a Shape"
assert r.area() == 200
assert str(Shape.Rect(4,5))  == "Rect(4,5)"
assert Rect.__annotations__ == (('x', int), ('y', int))

## Enum only allows enumerated values
from enum import Enum
class IntColor(Enum):
    Red = 1
    Blue = 2
    Green = 3

## Enum values 
## - can be structured
## - enum values will pass isinstance 
## - freely created values will NOT pass isinstance (even if equal to enum value)
class RGB(Record('r','g', 'b')):
    pass

class StructuredColor(Enum):

    Red = RGB(1,0,0)
    Blue = RGB(0,1,0)
    Green = RGB(0,0,1)

assert isinstance(StructuredColor.Red, StructuredColor)
assert not isinstance(RGB(0,0,0), StructuredColor)
assert not isinstance(RGB(1,0,0), StructuredColor)

## Union can have both enumerated values (normal class attrs) & free Constructors
class ColorUnion(metaclass=Union):

    class RGB2(Record('r', 'g', 'b')):
        pass

    Red = RGB2(1,0,0)
    Blue = RGB2(0,1,0)
    Green = RGB2(0,0,1)

assert isinstance(ColorUnion.RGB2(0,0,0), ColorUnion)
print(ColorUnion.Red)
assert isinstance(ColorUnion.Red, ColorUnion)
assert isinstance(ColorUnion.RGB2(2,3,4), ColorUnion)

## or, more convincingly
class LL(metaclass=Union):
    class Cons(Record('h', 'tl')):
        def len(self):
            return 1 + self.tl.len()

    class Empty:
        def len(self):
            return 0
    


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

def Fields(*a): return object

class Persons(Fields(
    ('name', str),
    ('age', int),
    ('cities', T.List[str]))):
  def foo(self, x: int) -> int:
    return x + self.age
  def bar(self, y: int) -> int:
    return self.age - y

# class Persons(Fields(
#     ('name', str),
#     ('age', int),
#     ('cities', T.List[str])
#     )):
#   def foo(self, x: int) -> int:
#     return x + self.age
#   def bar(self, y: int) -> int:
#     return self.age - y




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



