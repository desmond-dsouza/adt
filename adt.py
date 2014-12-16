from collections import namedtuple
from diy_typing import Union

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
    setattr(tuplebase, 'with_', base_replace)

    tuplebase.__annotations__ = slots_with_types
    tuplebase.__is_struct__ = True
    return tuplebase

class Singleton(Struct()):
    @staticmethod
    def __new__(cls):
        if hasattr(cls, '__instance__'):
            return getattr(cls, '__instance__')
        else:
            cls.__instance__ = tuple.__new__(cls)
            return cls.__instance__

    def __repr__(self):
        return type(self).__name__ + "()"

if __name__ == '__main__':

    ### ##### Examples of Use (see tests for more details) #####

    import diy_typing as T

    ### ##########################################
    ### Simple structures, with or without methods
    ### ##########################################
    class City(Struct('name')):
        pass

    assert str(City('austin')) == 'City(austin)'

    class Person(
        Struct(
            ('name', str),
            'age',
            ('cities', T.List[City]),
            ('friends', T.List['Person']))):

        def describe(self):
            return self.name

    p1 = Person('joe', 22, [], [])
    p2 = p1.with_(name='steve')
    assert p1 == Person('joe', 22, [], [])
    assert p2 == Person('steve', 22, [], [])

    ### ##########################################
    ###  Union, including Singleton
    ###  List = Empty() | Cons(hd, tl)
    ### ##########################################

    class Empty(Singleton):
        def len(self):
            return 0

    E = Empty()

    class Cons(Struct('hd', 'tl')):
        def len(self):
            return 1 + self.tl.len()

    List = Union[Empty, Cons]

    l1 = Cons(1, Cons(2, E))
    assert l1.len() == 2

    ### ##########################################
    ### external function over a Union
    ### map(f: T.Function, l: List) -> List

    def map(f, l):
        if isinstance(l, Cons):
            return Cons(f(l.hd), map(f, l.tl))
        elif l == E:
            return Empty()
        else: raise Exception()

    assert map(lambda x: x+1, Cons(1, Cons(2, E))) == Cons(2, Cons(3, E))


