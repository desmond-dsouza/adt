# TODO: Refine(List[Person], list_checker) -> RefinementType with check_instance functionality

class ParameterizedType(type):
    """An instance of ParameterizedType is a proper type, corresponding to a TypeConstructor after 
    all its parameters are filled in, and capable of check() on any object x. It has:
    name:str, base:class, args: tuple, checker: function"""

    # Registry of all Parameterized Types (an alternative would be custom == & hash)
    registry = {}  ### key:(TypeConstructor, arg1, arg2, ...) -> value: ParameterizedType

    def __repr__(cls):
        # print(cls.args)
        return "%s[%s]" % (cls.__name__, ', '.join((str(t) if isinstance(t, ParameterizedType) \
            else (t.__name__ if hasattr(t, '__name__') else str(t)) for t in cls.args)))

    # TODO: uniform check_instance protocol for PTypes, List/Union/Dict etc., Struct, RefinementTypes
    def check(cls, x):
        """Could not find a way to hook into Python's isinstance() checks, so just left this 
        as separate method."""
        return isinstance(x, cls.base) and cls.checker[0](cls, x)

class TypeConstructor(object):
    """A TypeConstructor is an object that generates a ParameterizedType when indexed with required arguments.
    e.g. List is a TypeConstructor, and List[int] is a ParameterizedType derived from built-in list. Arity is
    an integer, or '*' for any number. """
    def __init__(self, name, base, arity, checker=None):
        """The desired ParameterizedType name, its base class, argument arity (int or "*") to instantiate the
        ParameterizedType, and optional checker function: (ParameterizedType, random_instance) -> Bool."""
        self.name = name
        self.base = base
        self.arity = arity
        self.checker = checker if checker else lambda self, x: True

    def __getitem__(self, args):
        """Python's index operator, triggered by: Obj[x, y, z]. It returns a type: an instance of
        ParameterizedType, either newly created or already existing, with an args tuple, base class, and
        optional checker."""
        args_tuple = args if isinstance(args, tuple) else (args,)
        assert self.arity == len(args_tuple) or self.arity == "*", "%s Arity Error" % self.name
        registry_key = tuple([self] + list(args_tuple))
        if ParameterizedType.registry.get(registry_key):
            return ParameterizedType.registry.get(registry_key)
        else:
            t = type.__new__(ParameterizedType,
                             self.name,
                             (self.base,),
                             {'args': args_tuple,
                              'base': self.base,
                              'checker': (self.checker,)}) # hack: tuple to work-around 2.7 unbound methods checks
            ParameterizedType.registry[registry_key] = t
            return t

    def __repr__(self):
        return "%s[%s]" % (self.name,
                           "*" if self.arity == "*" else ", ".join("_" for n in range(self.arity)))

### Python 2.x using @typing decorator
def sig(**kw):
    ## should also add @wraps etc.
    def type_annotater(f):
        f.__annotations__ = {('return' if k == 'return_' else k): v for k, v in kw.items()}
        return f
    return type_annotater

Any = object
List = TypeConstructor('List', base=list, arity=1)
Iterable = TypeConstructor('Iterable', base=object, arity=1)
Set = TypeConstructor('Set', base=set, arity=1)
Tuple = TypeConstructor('Tuple', base=tuple, arity="*")
Maybe = TypeConstructor('Maybe', base=object, arity=1)
Dict = TypeConstructor('Dict', base=dict, arity=2)
Union = TypeConstructor('Union', base=object, arity="*")
Function = TypeConstructor('Function', base=object, arity="*")
T1, T2, T3, T4, T5, T6, T7 = object, object, object, object, object, object, object


if __name__ == '__main__':

    _ = List[int], Iterable[int], Set[int], Tuple[int, str, int], Maybe[int], Dict[int, int]
    _ = Union[int, str, float], Function[int, str, float]

    List = TypeConstructor('List', base=list, arity=1)
    Dict = TypeConstructor('Dict', base=dict, arity=2)
    IntRange = TypeConstructor('IntRange', base=int, arity=2, checker=lambda t, x: x >= t.args[0] and x <= t.args[1])
    Enum = TypeConstructor('Enum', base=object, arity="*", checker=lambda t, x: x in t.args)
    Func = TypeConstructor('Func', base=object, arity="*")


    L1 = List[int]
    L2 = List[List[str]]
    D1 = Dict[str, List[Dict[int, str]]]

    I = IntRange[2, 5]

    E = Enum[1, 3, 5]

    F = Func[int, List[int], int]

    assert type(L1) == ParameterizedType and type(L1.args[0]) == type
    assert type(L2) == ParameterizedType and type(L2.args[0]) == ParameterizedType and type(L2.args[0].args[0]) == type
    assert type(D1) == ParameterizedType and type(D1.args[0]) == type and type(D1.args[1]) == ParameterizedType

    assert isinstance(L1([1, 2]), list)
    assert isinstance(D1(a=1, b=2), dict)
    assert L1.check(L1([1, 2]))
    assert not L1.check(2)
    assert I.check(2) and not I.check(8) and not I.check('abc')
    assert E.check(1) and not E.check(2)


    assert str(List) == "List[_]"
    assert str(L1) == "List[int]"  
    assert str(L2) == "List[List[str]]"

    assert str(Dict) == "Dict[_, _]"
    assert str(D1) == "Dict[str, List[Dict[int, str]]]"

    assert str(IntRange) == "IntRange[_, _]"
    assert str(I) == "IntRange[2, 5]"

    assert str(Enum) == "Enum[*]"
    assert str(E) == "Enum[1, 3, 5]"

    assert str(Func) == "Func[*]"
    assert str(F) == "Func[int, List[int], int]"

    # ### Python 3.x using type annotation syntax
    # ### Comment out this section if trying out with Python 2.x, as 2.x will not recognize annotation syntax
    # def f_py3(x: int, y: List[int]) -> int:
    #     return x + sum(y)
    #
    # ### Note that __annotations__ have the complete type structure, with no erasure
    # assert f_py3.__annotations__ == {'x': int, 'y': List[int], 'return': int}
    # assert f_py3(1, [2, 3]) == 6

    @sig(x=int, y=List[int], return_=int)
    def f_py2(x, y):
        return x + sum(y)

    assert f_py2.__annotations__ == {'x': int, 'y': List[int], 'return': int}
    assert f_py2(1, [2, 3]) == 6
