from collections import namedtuple

## TODO: mixin classes: copy slots, use cls.__dict__ for methods (conflict-check)

def rule(f):
    f.__isrule__ = True
    return f

def Struct(*slots_with_types):
    """Returns a new (namedtuple) type. slots_with_types can be:
    (a) 2-tuples with types:  ('name', str), ('friends', List[Person]), ...
    (b) just slot names:      'name', 'age', ...
    (c) a single string:      'name age eye_color ...'
    Defines custom string(__repr__), equality(__eq__), and copy-with-update (with_) methods.
    Custom __init__ checks all @rule methods after instance construction & update.
    """
    slots_with_types = tuple([st for st in slots_with_types if not isinstance(st, type)])
    if len(slots_with_types)==1 and isinstance(slots_with_types[0], str):
        slots_with_types = slots_with_types[0].split()
    slots = tuple( 
        [s_t[0] if isinstance(s_t, tuple) else s_t for s_t in slots_with_types])
    
    struct_type = namedtuple("_".join(slots) + "_Record", slots)
    base_eq = getattr(struct_type, '__eq__')
    base_replace = getattr(struct_type, '_replace')
    
    def _repr(self):
        vals = ','.join(str(getattr(self, x)) for x in slots)
        return "%s(%s)" % (type(self).__name__, vals)
    
    def _eq(self, other):
        return type(self) == type(other) and base_eq(self, other)

    def _assert_valid(self):
        cls_dict = type(self).__dict__
        rules = [m for k, m in cls_dict.items() if hasattr(m, '__isrule__')]
        failed = [r for r in rules if not r(self)]
        if failed:
            raise Exception("Rules violated: {0}".format(str(failed)))

    def _with(self, *a, **k):
        updated = base_replace(self, *a, **k)
        updated._assert_valid()
        return updated

    def _init(self, *a, **k):
        # no super().__init__ as namedtuple uses __new__ for initialization
        self._assert_valid()

    setattr(struct_type, '__repr__', _repr)
    setattr(struct_type, '__eq__', _eq)
    setattr(struct_type, 'with_', _with)
    setattr(struct_type, '__init__', _init)
    setattr(struct_type, '_assert_valid', _assert_valid)
    
    struct_type.__annotations__ = slots_with_types
    struct_type.__is_struct__ = True
    return struct_type

class Singleton(object):
    @staticmethod
    def __new__(cls):
        if hasattr(cls, '__instance__'):
            return getattr(cls, '__instance__')
        else:
            cls.__instance__ = object.__new__(cls)
            return cls.__instance__

    def __repr__(self):
        return type(self).__name__ + "()"

if __name__ == '__main__':

    ### ##### Examples of Use (see tests for more details) #####

    from diy_typing import sig, List, Union, Function, Any, T1, T2

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
            ('cities', List[City]),
            ('friends', List['Person']))):

        def describe(self):
            return self.name

    p1 = Person('joe', 22, [], [])
    assert p1.describe() == 'joe'
    p2 = p1.with_(name='steve')
    assert p1 == Person('joe', 22, [], [])
    assert p2 == Person('steve', 22, [], [])

    ### ##########################################
    ###  Union, including Singleton & methods
    ###  LList = Empty() | Cons(hd, tl)
    ### ##########################################

    LList = Union['Empty', 'Cons']

    class Empty(Singleton):
        def len(self):
            return 0

    E = Empty()

    class Cons(Struct(
                      ('hd', Any),
                      ('tl', LList))):
        def len(self):
            return 1 + self.tl.len()

    l1 = Cons(1, Cons(2, E))
    assert l1.len() == 2

    ### ##########################################
    ### external function over a Union
    ### @sig is for Python 2.7 (e.g. iPad Pythonista)
    ###    for Python 3, just use:  def map(f: Functino, l: LList) -> LList:

    @sig(f=Function, l=LList, return_=LList)
    def map(f, l):
        if isinstance(l, Cons):
            return Cons(f(l.hd), map(f, l.tl))
        elif l == E:
            return Empty()
        else: raise Exception()

    assert map(lambda x: x+1, Cons(1, Cons(2, E))) == Cons(2, Cons(3, E))


