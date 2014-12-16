from collections import namedtuple

def Struct(*slots_with_types):
    slots = tuple( 
        [s_t[0] if isinstance(s_t, tuple) else s_t for s_t in slots_with_types])
    tuplebase = namedtuple("_".join(slots) + "_Record", slots)
    base_eq = getattr(tuplebase, '__eq__')
    base_replace = getattr(tuplebase, '_replace')

    def rep(self):
        vals = ','.join(str(getattr(self, x)) for x in slots)
        return "%s(%s)" % (type(self).__name__, vals)

    def eq(self, other):
        return type(self) == type(other) and base_eq(self, other)

    setattr(tuplebase, '__repr__', rep)
    setattr(tuplebase, '__eq__', eq)
    setattr(tuplebase, '__call__', base_replace)

    tuplebase.__annotations__ = slots_with_types
    tuplebase.__is_struct__ = True
    return tuplebase

class Singleton:
    pass

class _Union(type):
    def __init__(self, name, bases, attrs):
        for k, v in attrs.items():
            if isinstance(v, type):
                if len(v.__bases__) > 1 or (v.__bases__!=(Singleton,) and not hasattr(v.__bases__[0],'__is_struct__')):
                    print(v.__bases__)
                    raise Exception("Union: each variant must only subclass Struct(...) or Singleton")
                if Singleton in v.__bases__:
                    v.__bases__ = tuple(list(v.__bases__) + [self])
                    setattr(v, '__repr__', lambda self, k=k: k)
                    setattr(self, k, v())
                    setattr(self, "_type_of_" + k, v)
                else:
                    v.__bases__ = tuple(list(v.__bases__) + [self])
        # super().__init__(name, bases, attrs)  ## TODO: adding / removing this line makes no difference???

class Union(metaclass=_Union): pass


### ####################################################
### Shape = Circle(r) | Rect(w,h)
### ####################################################
class Circle(
    Struct(('r', int))):
    pass


### Tests & Examples of Use

import typing as T

## Single Record Type
class Person(Struct(
        ('name', str),
        ('age', int),
        ('cities', T.List[str]))):
    def walk(self):
        return "Walk"

p = Person('bob', 22, ['austin', 'dallas'])
assert p == Person('bob', 22, ['austin', 'dallas'])
assert p(age=p.age + 1) == Person('bob', 23, ['austin', 'dallas'])
assert str(p) == "Person(bob,22,['austin', 'dallas'])"

## Nested Records
class Club(Struct(
            ('name', str), ('members', T.List[Person]))):
    def foo(self):
        pass

s = Club('Soccer', [p, p(name='Chris')])
assert str(s) == "Club(Soccer,[Person(bob,22,['austin', 'dallas']), Person(Chris,22,['austin', 'dallas'])])"


## Union of 2 record types with unique + shared methods
class Shape(Union):
    def shared(self): return "I am a Shape"

    class Rect(Struct(
            ('x', int),
            ('y', int))):
        def area(self): return self.x * self.y
        def peri(self): return 2 * (self.x + self.y)

    class Circle(Struct(
            ('r', int))):
        def area(self): return 3.14 * self.r * self.r
        def peri(self): return 2 * 3.14 * self.r

Rect = Shape.Rect
Circle = Shape.Circle

r = Rect(10, 20)
c = Circle(20)

assert isinstance(r, Shape)
assert isinstance(r, Rect)
assert not isinstance(r, Circle)
assert isinstance(c, Shape)
assert r.shared() == "I am a Shape"
assert r.area() == 200
assert str(Rect(4,5))  == "Rect(4,5)"
assert Rect.__annotations__ == (('x', int), ('y', int))

## Just for comparison: Python 3.4 has built-in Enum
## It only allows enumerated values
from enum import Enum
class IntColor(Enum):
    Red = 1
    Blue = 2
    Green = 3

## Enum values can be structured objects, isinstance will work for those values
## - freely created values will NOT pass isinstance (even if equal to enum value)
class RGB(Struct('r','g', 'b')):
    pass

class StructuredColor(Enum):
    Red = RGB(1,0,0)
    Blue = RGB(0,1,0)
    Green = RGB(0,0,1)

assert isinstance(StructuredColor.Red, StructuredColor)
assert not isinstance(RGB(1,0,0), StructuredColor)

## Union can have both open Constructors & selected values (normal class attrs)
class Color(Union):

    class RGB2(Struct('r', 'g', 'b')):
        pass

    Red = RGB2(1,0,0)
    Blue = RGB2(0,1,0)
    Green = RGB2(0,0,1)

assert isinstance(Color.RGB2(0,0,0), Color)
assert isinstance(Color.Red, Color)
assert isinstance(Color.RGB2(2,3,4), Color)
assert str(Color.Green) == "RGB2(0,0,1)"

## Unions can contain @singletons defined as classes with methods (but no Record fields)
## - the singleton becomes an instance, its class gets custom __bases__ and __repr__

## List = Empty | Cons(h, tl)
class List(Union):

    def isList(self): return True

    class Cons(Struct('hd', 'tl')):
        def len(self):
            return 1 + self.tl.len()

    class Empty(Singleton):
        def len(self):
            return 0

Cons = List.Cons
E = List.Empty

l2 = Cons(2, Cons(3, E))
assert str(E) == "Empty"
assert l2.isList()
assert l2.len() == 2
assert isinstance(l2, List)
assert isinstance(l2, Cons)
assert isinstance(E, List)
assert not isinstance(E, Cons)

## A pattern-matching MAP over List
def map(f: T.Function, l: T.List) -> T.List:
    if l == List.Empty:
        return List.Empty
    elif isinstance(l, List.Cons):
        return Cons(f(l.hd), map(f, l.tl))
    else: raise Exception("Not in List Union")

assert map(lambda x: x + 1, l2) == Cons(3, Cons(4, E))

### Peano Arithmetic example
class Num(Union):

    class S(Struct('n')):
        def __add__(self, x):
            return self.n + S(x)

    class Z(Singleton):
        def __add__(self, x):
            return x

S = Num.S
Z = Num.Z

_1 = S(Z)
_2 = S(_1)
_3 = S(_2)
assert str(Z) == "Z"
assert _3 == S(S(S(Z)))
assert Z + S(Z) == S(Z)
assert _1 + _2 == _3
assert _2 + _1 == _3

### Elm Collage -- selected bits

## Elm does extensible record typing : we simply add undeclared attributes
class Form(Struct(
    'theta',
    'scale',
    'x',
    'y',
    'alpha',
    'form')):
    pass

class FillStyle(Union):
    class Solid(Struct('color')): pass
    class Texture(Struct('url')): pass
    class Grad(Struct('gradient')): pass

Solid = FillStyle.Solid

class LineCap(Union):
    class Flat(Singleton): pass
    class Round(Singleton): pass
    class Padded(Singleton): pass

class BasicForm(Union):
    class FPath(Struct('linestyle', 'path')): pass
    class FShape(Struct('shapestyle', 'shape')): pass
    class FImage(Struct('w', 'h', 'pos', 'url')): pass
    class FGroup(Struct('transform2D', 'forms')): pass

FShape = BasicForm.FShape

class ShapeStyle(Union):
    class Line(Struct('linestyle')): pass
    class Fill(Struct('fillstyle')): pass

Fill = ShapeStyle.Fill

class Shape(Struct('point_list')): pass

def form(f: BasicForm) -> Form:
    return Form(theta=0,scale=1,x=0,y=0,alpha=1,form=f)

assert form("myBasicForm") == Form(0,1,0,0,1,"myBasicForm")

def _fill(fillstyle, shape):
    return form(FShape(Fill(fillstyle), shape))

def filled(c: Color, sh: Shape) -> Form:
    return _fill(Solid(c), sh)

s = Shape([(0,0), (1,1), (2,2)])
f = filled(Color.Red, s)
assert f == Form(0,1,0,0,1,FShape(Fill(Solid(Color.Red)),s))

def movex(dx: int, f: Form) -> Form:
    return f(x=f.x + dx)

f2 = movex(20, f)
assert f2 == Form(0,1,20,0,1,FShape(Fill(Solid(Color.Red)),s))