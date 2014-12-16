### ####################################################
### Tests & Examples of Use

from adt import Struct, Singleton, Union
import typing as T

### ################################################
## Simple Struct Type
class Person(
    Struct(
        ('name', str),
        ('age', int),
        ('cities', T.List[str]))):
    def walk(self):
        return "Walk"

p = Person('bob', 22, ['austin', 'dallas'])

def test_equality_update_repr():
    assert p == Person('bob', 22, ['austin', 'dallas'])
    assert p.with_(age=p.age + 1) == Person('bob', 23, ['austin', 'dallas'])
    assert str(p) == "Person(bob,22,['austin', 'dallas'])"

### ################################################
## Nested Struct Type

def test_nested_struct():

    class Club(
        Struct(
            ('name', str),
            ('members', T.List[Person]))):
        def foo(self):
            pass

    s = Club('Soccer', [p, p.with_(name='Chris')])
    assert str(s) == "Club(Soccer,[Person(bob,22,['austin', 'dallas']), Person(Chris,22,['austin', 'dallas'])])"

### ################################################
### Plain Union of 2 Structures
### Event = Key(k, modifiers) | Mouse(position)
### ################################################

def test_plain_union_of_structs():
    class Key(Struct('key', 'modifiers')):
        pass

    class Mouse(Struct('position')):
        pass

    Event = Union[Key, Mouse]

### ################################################
### Use normal Inheritance for Union with shared methods
### Shape(...) = Rect(...) | Circle(...)
### ################################################

def test_union_with_methods():

    class Shape:
        def shared(self): return "I am a Shape"

    class Rect(Shape,
               Struct(
                   ('x', int),
                   ('y', int))):
        def area(self): return self.x * self.y
        def peri(self): return 2 * (self.x + self.y)

    class Circle(Shape,
                 Struct(
                     ('r', int))):
        def area(self): return 3.14 * self.r * self.r
        def peri(self): return 2 * 3.14 * self.r

    ShapeUnion = Union[Rect, Circle]

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

### ################################################
## Just for comparison: Python 3.4 has built-in Enum
## to enumerate values
from enum import Enum
class IntColor(Enum):
    Red = 1
    Blue = 2
    Green = 3

## Enum values can be structured objects, isinstance will work for those values
## - freely created values will NOT pass isinstance (even if equal to enum value)
class RGB(Struct('r','g', 'b')):
    pass

class Color(Enum):
    Red = RGB(1,0,0)
    Blue = RGB(0,1,0)
    Green = RGB(0,0,1)

def test_enums():
    assert isinstance(Color.Red, Color)
    assert not isinstance(RGB(1,0,0), Color)

### ################################################
## Unions can contain @singletons defined as classes with methods (but no Record fields)
## The singleton gets a custom __repr__

### ################################################
## List = Empty | Cons(h, tl)
### ################################################

class Cons(Struct('hd', 'tl')):
    def len(self):
        return 1 + self.tl.len()

class Empty(Singleton):
    def len(self):
        return 0

List = Union[Cons,Empty]

E = Empty()

def test_list_cons_empty():

    assert Empty() is Empty()

    l2 = Cons(2, Cons(3, E))
    assert str(E) == "Empty()"
    assert E.len() == 0
    assert l2.len() == 2

## A pattern-matching MAP over List
def test_pattern_match_over_list():
    def map(f: T.Function, l: List) -> List:
        if isinstance(l, Empty):
            return E
        elif isinstance(l, Cons):
            return Cons(f(l.hd), map(f, l.tl))
        else: raise Exception("Not in List Union")

    l2 = Cons(2, Cons(3, E))
    assert map(lambda x: x + 1, l2) == Cons(3, Cons(4, E))

### Peano Arithmetic example
### ################################################
### Num = Zero | S(n)

class S(Struct('n')):
    def __add__(self, x):
        return self.n + S(x)

class Zero(Singleton):
    def __add__(self, x):
        return x

def test_peano():
    Z = Zero()
    _1 = S(Z)
    _2 = S(_1)
    _3 = S(_2)
    assert str(Z) == "Zero()"
    assert _3 == S(S(S(Z)))
    assert Z + S(Z) == S(Z)
    assert _1 + _2 == _3
    assert _2 + _1 == _3

### ################################################
### Elm Collage -- selected bits

## Elm does extensible record typing : Python does duck typing
class Form(Struct(
    'theta',
    'scale',
    'x',
    'y',
    'alpha',
    'form')):
    pass

######
class Solid(Struct('color')): pass
class Texture(Struct('url')): pass
class Grad(Struct('gradient')): pass
FillStyle = Union[Solid, Texture, Grad]


class Flat(Singleton): pass
class Round(Singleton): pass
class Padded(Singleton): pass
LineCap = Union[Solid, Texture, Grad]


class FPath(Struct('linestyle', 'path')): pass
class FShape(Struct('shapestyle', 'shape')): pass
class FImage(Struct('w', 'h', 'pos', 'url')): pass
class FGroup(Struct('transform2D', 'forms')): pass
BasicForm = Union[FPath, FShape, FImage, FGroup]


class Line(Struct('linestyle')): pass
class Fill(Struct('fillstyle')): pass
ShapeStyle = Union[Line, Fill]


class Shape(Struct('point_list')): pass

def test_elm_graphics():

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
        return f.with_(x=f.x + dx)

    f2 = movex(20, f)
    assert f2 == Form(0,1,20,0,1,FShape(Fill(Solid(Color.Red)),s))