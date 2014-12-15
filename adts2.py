from collections import namedtuple

def Attrs(*slots_with_types):
    slots = tuple( 
        [s_t[0] if isinstance(s_t, tuple) else s_t for s_t in slots_with_types])
    tuplebase = namedtuple("_".join(slots) + "_Record", slots)
    base_eq = getattr(tuplebase, '__eq__')
    base_replace = getattr(tuplebase, '_replace')

    def repr(self):
        vals = ','.join(str(getattr(self, x)) for x in slots)
        return "%s(%s)" % (type(self).__name__, vals)

    def eq(self, other):
        return type(self) == type(other) and base_eq(self, other)

    setattr(tuplebase, '__repr__', repr)
    setattr(tuplebase, '__eq__', eq)
    setattr(tuplebase, '__call__', base_replace)

    tuplebase.__annotations__ = slots_with_types
    return tuplebase

def singleton(cls):
    setattr(cls, 'is_singleton', True)
    return cls

class _Union(type):
    def __init__(self, name, bases, attrs):
        for k, v in attrs.items(): 
            if isinstance(v, type): 
                if v.__bases__ == (object,) and not hasattr(v, 'is_singleton'):
                    raise Exception("Must be Record or @singleton")
                if hasattr(v, 'is_singleton'):
                    if v.__bases__ != (object,):
                        raise Exception("@singleton cannot have base class")
                    kls = type(k, (v, self), {'__repr__': lambda self, k=k: k })
                    setattr(self, k, kls())
                else: 
                    v.__bases__ = tuple(list(v.__bases__) + [self])

class Union(metaclass=_Union): pass

if __name__ == '__main__':

    ### Tests & Examples of Use

    import typing as T

    ## Single Record Type
    class Person(Attrs(
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
    class Club(Attrs(
                ('name', str), ('members', T.List[Person]))):
        def foo(self):
            pass

    s = Club('Soccer', [p, p(name='Chris')])
    assert str(s) == "Club(Soccer,[Person(bob,22,['austin', 'dallas']), Person(Chris,22,['austin', 'dallas'])])"


    ## Union of 2 record types with unique + shared methods
    class Shape(Union):
        def shared(self): return "I am a Shape"

        class Rect(Attrs(
                ('x', int),
                ('y', int))):
            def area(self): return self.x * self.y
            def peri(self): return 2 * (self.x + self.y)

        class Circle(Attrs(
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
    class RGB(Attrs('r','g', 'b')):
        pass

    class StructuredColor(Enum):
        Red = RGB(1,0,0)
        Blue = RGB(0,1,0)
        Green = RGB(0,0,1)

    assert isinstance(StructuredColor.Red, StructuredColor)
    assert not isinstance(RGB(0,0,0), StructuredColor)
    assert not isinstance(RGB(1,0,0), StructuredColor)

    ## Union can have both open Constructors & selected values (normal class attrs)
    class ColorUnion(Union):

        class RGB2(Attrs('r', 'g', 'b')):
            pass

        Red = RGB2(1,0,0)
        Blue = RGB2(0,1,0)
        Green = RGB2(0,0,1)

    assert isinstance(ColorUnion.RGB2(0,0,0), ColorUnion)
    assert isinstance(ColorUnion.Red, ColorUnion)
    assert isinstance(ColorUnion.RGB2(2,3,4), ColorUnion)
    assert str(ColorUnion.Green) == "RGB2(0,0,1)"

    ## Unions can contain @singletons defined as classes with methods (but no Record fields)
    ## - the singleton becomes an instance, its class gets custom __bases__ and __repr__

    ## List = Empty | Cons(h, tl)
    class List(Union):

        def isList(self): return True

        class Cons(Attrs('hd', 'tl')):
            def len(self):
                return 1 + self.tl.len()

        @singleton
        class Empty:
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

        class S(Attrs('n')):
            def __add__(self, x):
                return self.n + S(x)

        @singleton
        class Z:
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



