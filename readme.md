# Python serialization to WL / WXF

This library is intended to provide a way to serialize python expression to WL / WXF string of bytes. The library was designed to be extensible so that any arbitrary Python object can be serialized with the addition of custom encoder(s). The code was tested with two interpreters: Python 2.7, Python 3.6.4 on MacOS and JYTHON 2.7.

# API

The main entry point to export python objects is the export function:

```
>>> from wolframclient.serializers import export
>>> export([1, 2, 3])
'{1, 2, 3}'
```

If a string is provided as second argument then export will dump directly to a file
```
>>> export([1, 2, 3], 'file.wl')
'file.wl'
```

export can write to any object that implements a write method, like file or BytesIO or StringIO.

```
>>> with open('file.wl', 'wb') as f:
...     export([1, 2, 3], f)
... 
<open file 'file.wl', mode 'wb' at 0x10a4f01e0>
```

## Data normalization

### Core data serialization

Built-in data structures are all supported:

```
>>> export({"list": [1, 2, 3], "set": set([1, 2, 2, 4]), "frozenset": frozenset([1, 2, 2, 4]), "dict": dict(a = 2)})
'<|"dict" -> <|"a" -> 2|>, "set" -> {1, 2, 4}, "list" -> {1, 2, 3}, "frozenset" -> {1, 2, 4}|>'
```

To preserve order with association use collections.OrderedDict

```
>>> export(OrderedDict(enumerate("abcd")))
'<|0 -> "a", 1 -> "b", 2 -> "c", 3 -> "d"|>'
```

Any class that has an __iter__ method is converted to a WL List, including generators.
Generators should be used to serialize big data without running out of memory.

```
>>> export((i + 2 for i in range(10)))
'"{2, 3, 4, 5, 6, 7, 8, 9, 10, 11}"'

>>> def gen():
...     yield 1
...     yield 2
... 
>>> export(gen())
'{1, 2}'

```

### Numeric serialization

float, decimal, integers and complex are supported:

```
>>> export({'int': 1, 'float':2.3, 'decimal': decimal.Decimal(1), 'complex': complex(3, 4)})
'<|"int" -> 1, "float" -> 2.300000, "decimal" -> 1, "complex" -> (3.000000 + I*4.000000)|>'
```

Infinity and NaN are converted to DirectedInfinity[...] and Indeterminate:

```
>>> export({'+inf': float('inf'), '-inf': - float('inf'), 'nan': float('NaN')})
'<|"+inf" -> DirectedInfinity[1], "-inf" -> DirectedInfinity[-1], "nan" -> Indeterminate|>'
```

fractions are serialized using Rational

```
>>> export(fractions.Fraction(2, 3))
'(2 / 3)'
```

### DateObject serialization

datetime, time and date are supported, by using $TimeZone.

```
>>> import datetime
>>> now = datetime.datetime.now()
>>> export([now.time(), now.date(), now])
'{TimeObject[{16, 1, 19.993822}, TimeZone -> $TimeZone], DateObject[{2018, 3, 16}], DateObject[{2018, 3, 16, 16, 1, 19.993822}, "Instant", "Gregorian", $TimeZone]}'```

datetime and time with timezone are supported as well:

```
>>> from pytz import timezone
>>> export(timezone('US/Eastern').localize(datetime.datetime.now()))
'DateObject[{2018, 3, 16, 16, 4, 17.712409}, "Instant", "Gregorian", "US/Eastern"]'
```

### Expressions

this module provide a simple way to write expressions complex WL expressions in python:

```
>>> export([wl.Now, wl.PrimeQ(1), wl.Interpreter("String")("foo")])
'{Now, PrimeQ[1], Interpreter["String"]["foo"]}'
```

### Custom Objects

in order to provide a custom serialization for an object you can subclass WLSerializable

```
from wolframclient.serializers.serializable import WLSerializable
class MyStuff(WLSerializable):
    def __init__(self, *stuff):
        self.stuff = stuff
    def to_wl(self):
        return wl.RandomThings(*self.stuff)
```

after that export will be able to serialize the expression recursivly:

```
>>> export(MyStuff(1, 2, MyStuff(2, 3)))
'RandomThings[1, 2, RandomThings[2, 3]]'
```

export also supports a normalization function that allows you to redefine how existing types should be serialized.

```
class MyStuff(object):
    def __init__(self, *stuff):
        self.stuff = stuff

def normalizer(o):
    if isinstance(o, int):
        return 'o'
    if isinstance(o, MyStuff):
        return wl.RandomThings(*o.stuff)
    return o
```

then you can pass the normalizer to export in order to perform a custom recursive normalization:

```
>>> export(MyStuff(1, 2, MyStuff([2, 3])), normalizer = normalizer)
'RandomThings["o", "o", RandomThings[{"o", "o"}]]'
```

## Export Formats

### WL

By default export serializes using InputForm

```
>>> export([1, 2, 3], format = "wl")
'{1, 2, 3}'
```

### WXF

WXF is an efficient format to rappresents expressions in WL

```
>>> export([1, 2, 3], format = "wxf")
'8:f\x03s\x04ListC\x01C\x02C\x03'
```

The format allows compression using zlib, the compression is disabled by default:

```
>>> export([1, 2, 3], format = "wxf", compress = True)
'8C:x\x9cKc.f\xf1\xc9,.qftfrf\x06\x00\x1b\xf8\x03L'
```
