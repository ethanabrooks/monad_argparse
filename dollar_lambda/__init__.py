"""
This package provides an alternative to [`argparse`](https://docs.python.org/3/library/argparse.html)
based on parser combinators and functional first principles. Arguably, `$λ` is way more expressive than any reasonable
person would ever need... but even if it's not the parser that we need, it's the parser we deserve.

# Installation
```
pip install dollar-lambda
```

# Highlights
`$λ` comes with syntactic sugar that came make building parsers completely boilerplate-free.
For complex parsing situations that exceed the expressive capacity of this syntax,
the user can also drop down to the lower-level syntax that lies behind the sugar, which can
handle any reasonable amount of logical complexity.

## The [`@command`](#dollar_lambda.command) decorator
For the vast majority of parsing patterns, `@command` is the most concise way to
define a parser:

>>> @command()
... def main(x: int, dev: bool = False, prod: bool = False):
...     return dict(x=x, dev=dev, prod=prod)

Here is the help text generated by this parser:

>>> main("-h")
usage: -x X --dev --prod

And here it is in action:

>>> main("-x", "1", "--dev")
{'x': 1, 'dev': True, 'prod': False}

Ordinarily you would provide `main` no arguments and
it would get them from the command line.

>>> parser.TESTING = False  # False by default but needs to be true for doctests
>>> import sys
>>> sys.argv[1:] = ["-x", "1", "--dev"]  # simulate command line input
>>> main()
{'x': 1, 'dev': True, 'prod': False}

In this document we'll feed the strings directly for the sake of brevity.
>>> parser.TESTING = True

Use the `parsers` argument to add custom logic to this parser:

>>> @command(parsers=dict(kwargs=(flag("dev") | flag("prod"))))
... def main(x: int, **kwargs):
...     return dict(x=x, **kwargs)

This parser requires either a `--dev` or `--prod` flag and maps it to the `kwargs` argument:
>>> main("-h")
usage: -x X [--dev | --prod]
>>> main("-x", "1", "--dev")
{'x': 1, 'dev': True}
>>> main("-x", "1", "--prod")
{'x': 1, 'prod': True}
>>> main("-x", "1")
usage: -x X [--dev | --prod]
The following arguments are required: --dev

## `CommandTree` for dynamic dispatch
For many programs, a user will want to use one entrypoint for one set of
arguments, and another for another set of arguments. Returning to our example,
let's say we wanted to execute `prod_function` when the user provides the
`--prod` flag, and `dev_function` when the user provides the `--dev` flag:

>>> tree = CommandTree()
...
>>> @tree.command()
... def base_function(x: int):
...     print("Ran base_function with arguments:", dict(x=x))
...
>>> @base_function.command()
... def prod_function(x: int, prod: bool):
...     print("Ran prod_function with arguments:", dict(x=x, prod=prod))
...
>>> @base_function.command()
... def dev_function(x: int, dev: bool):
...     print("Ran dev_function with arguments:", dict(x=x, dev=dev))

Let's see how this parser handles different inputs.
If we provide the `--prod` flag, `$λ` automatically invokes
 `prod_function` with the parsed arguments:

>>> tree("-x", "1", "--prod")
Ran prod_function with arguments: {'x': 1, 'prod': True}

If we provide the `--dev` flag, `$λ` invokes `dev_function`:

>>> tree("-x", "1", "--dev")
Ran dev_function with arguments: {'x': 1, 'dev': True}

With this configuration, the parser will run `base_function` if neither
`--prod` nor `--dev` are given:

>>> tree("-x", "1")
Ran base_function with arguments: {'x': 1}

As with `main` in the previous example, you would ordinarily provide `tree` no arguments and it would get them
from the command line.

There are many other ways to use `CommandTree`,
including some that make use of the `base_function`.
To learn more, we recommend the [`CommandTree` tutorial](#commandtree-tutorial).

## Lower-level syntax
[`@command`](#dollar_lambda.command) and `CommandTree` cover many use cases,
but they are both syntactic sugar for a lower-level interface that is far
more expressive.

Suppose you want to implement a parser that first tries to parse an option
(a flag that takes an argument),
`-x X` and if that fails, tries to parse the input as a variadic sequence of
floats:

>>> p = option("x", type=int) | argument("y", type=float).many()

We go over this syntax in greater detail in the [tutorial](#tutorial).
For now, suffice to say that `argument` defines a positional argument,
[`many`](#dollar_lambda.Parser.many) allows parsers to be applied
zero or more times, and [`|`](#dollar_lambda.Parser.__or__) expresses alternatives.

Here is the help text:

>>> p.parse_args("-h")
usage: [-x X | [Y ...]]

As promised, this succeeds:

>>> p.parse_args("-x", "1")
{'x': 1}

And this succeeds:

>>> p.parse_args("1", "2", "3")
{'y': [1.0, 2.0, 3.0]}

Again, you would ordinarily provide `parse_args` no arguments and it would get them
from the command line:
>>> parser.TESTING = False
>>> sys.argv[1:] = ["-x", "1"]  # simulate command line input
>>> p.parse_args()
{'x': 1}
>>> parser.TESTING = True

# Tutorial

We've already seen many of the concepts that power `$λ` in the
[Highlights](#highlights) section. This tutorial will address
these concepts one at a time and expose the reader to some
nuances of usage.

## An example from `argparse`

Many of you are already familiar with `argparse`.
You may even recognize this example from the `argparse` docs:

```
import argparse
parser = argparse.ArgumentParser(description="calculate X to the power of Y")
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action="store_true")
group.add_argument("-q", "--quiet", action="store_true")
parser.add_argument("x", type=int, help="the base")
parser.add_argument("y", type=int, help="the exponent")
args = parser.parse_args()
```

Here is one way to express this logic in `$λ`:

>>> @command(
...     parsers=dict(kwargs=(flag("verbose") | flag("quiet")).optional()),
...     help=dict(x="the base", y="the exponent"),
... )
... def main(x: int, y: int, **kwargs):
...     return dict(x=x, y=y, **kwargs)  # Run program. Return can be whatever.

Here is the help text for this parser:

>>> main("-h")
usage: -x X -y Y [--verbose | --quiet]
x: the base
y: the exponent

As indicated, this succeeds given `--verbose`

>>> main("-x", "1", "-y", "2", "--verbose")
{'x': 1, 'y': 2, 'verbose': True}

or `--quiet`

>>> main("-x", "1", "-y", "2", "--quiet")
{'x': 1, 'y': 2, 'quiet': True}

or neither

>>> main("-x", "1", "-y", "2")
{'x': 1, 'y': 2}

Ordinarily , we would not feed `main` any arguments, and it would get them from
the command line:

>>> parser.TESTING = False  # False by default but needs to be True for doctests
>>> sys.argv[1:] = ["-x", "1", "-y", "2"]  # simulate command line input
>>> main()
{'x': 1, 'y': 2}
>>> parser.TESTING = True

## Equivalent in lower-level syntax
To better understand what is going on here, let's remove the syntactic sugar:

>>> p = nonpositional(
...     (flag("verbose") | flag("quiet")).optional(),
...     option("x", type=int, help="the base"),
...     option("y", type=int, help="the exponent"),
... )
...
>>> def main(x, y, **kwargs):
...     return dict(x=x, y=y, **kwargs)

Now let's walk through this step by step.

## High-Level Parsers
In the de-sugared implementation there are two different parser constructors:
`flag`, which binds a boolean value to a variable, and `option`, which binds an arbitrary value to a variable.

### `flag`
>>> p = flag("verbose")
>>> p.parse_args("--verbose")
{'verbose': True}

By default `flag` fails when it does not receive expected input:
>>> p.parse_args()
usage: --verbose
The following arguments are required: --verbose

Alternately, you can set a default value:
>>> flag("verbose", default=False).parse_args()
{'verbose': False}

### `option`
`option` is similar but takes an argument:
By default, `option` expects a single `-` for single-character variable names (as in `-x`),
as opposed to `--` for longer names (as in `--xenophon`):

>>> option("x").parse_args("-x", "1")
{'x': '1'}
>>> option("xenophon").parse_args("--xenophon", "1")
{'xenophon': '1'}

Use the `type` argument to convert the input to a different type:
>>> option("x", type=int).parse_args("-x", "1")  # converts "1" to an int
{'x': 1}

## Parser Combinators
Parser combinators are functions that combine multiple parsers into new, more complex parsers.
Our example uses two such functions: `nonpositional` and [`|`](#dollar_lambda.Parser.__or__).

### [`|`](#dollar_lambda.Parser.__or__)

The [`|`](#dollar_lambda.Parser.__or__) operator is used for alternatives. Specifically, it will try the first parser,
and if that fails, try the second:

>>> p = flag("verbose") | flag("quiet")
>>> p.parse_args("--quiet") # flag("verbose") fails
{'quiet': True}
>>> p.parse_args("--verbose") # flag("verbose") succeeds
{'verbose': True}

By default one of the two flags would be required to prevent failure:
>>> p.parse_args() # neither flag is provided so this fails
usage: [--verbose | --quiet]
The following arguments are required: --verbose

We can permit the omission of both flags
by using `optional`, as we saw earlier, or we can supply a default value:

>>> (flag("verbose") | flag("quiet")).optional().parse_args() # flags fail, but that's ok
{}
>>> (flag("verbose") | flag("quiet", default=False)).parse_args() # flag("verbose") fails but flag("quiet", default=False) succeeds
{'quiet': False}

Users should note that unlike logical "or" but like Python `or`, the [`|`](#dollar_lambda.Parser.__or__) operator is not commutative:

>>> (flag("verbose") | argument("x")).parse_args("--verbose")
{'verbose': True}

`argument` binds to positional arguments. If it comes first, it will think that `"--verbose"` is
the expression that we want to bind to `x`:

>>> (argument("x") | flag("verbose")).parse_args("--verbose")
{'x': '--verbose'}

### `nonpositional` and [`+`](#dollar_lambda.Parser.__add__)
`nonpositional` takes a sequence of parsers as arguments and attempts all permutations of them,
returning the first permutations that is successful:

>>> p = nonpositional(flag("verbose"), flag("quiet"))
>>> p.parse_args("--verbose", "--quiet")
{'verbose': True, 'quiet': True}
>>> p.parse_args("--quiet", "--verbose")  # reverse order also works
{'quiet': True, 'verbose': True}

For just two parsers you can use [`+`](#dollar_lambda.Parser.__add__) instead of `nonpositional`:
>>> p = flag("verbose") + flag("quiet")
>>> p.parse_args("--verbose", "--quiet")
{'verbose': True, 'quiet': True}
>>> p.parse_args("--quiet", "--verbose")  # reverse order also works
{'quiet': True, 'verbose': True}

This will not cover all permutations for more than two parsers:
>>> p = flag("verbose") + flag("quiet") + option("x")
>>> p.parse_args("--verbose", "-x", "1", "--quiet")
usage: --verbose --quiet -x X
Expected '--quiet'. Got '-x'

To see why note the implicit parentheses:
>>> p = (flag("verbose") + flag("quiet")) + option("x")

In order to cover the case where `-x` comes between `--verbose` and `--quiet`,
use `nonpositional`:
>>> p = nonpositional(flag("verbose"), flag("quiet"), option("x"))
>>> p.parse_args("--verbose", "-x", "1", "--quiet")  # works
{'verbose': True, 'x': '1', 'quiet': True}

## Putting it all together
Let's recall the original example without the syntactic sugar:

>>> p = nonpositional(
...     (flag("verbose") | flag("quiet")).optional(),
...     option("x", type=int, help="the base"),
...     option("y", type=int, help="the exponent"),
... )
...
>>> def main(x, y, verbose=False, quiet=False):
...     return dict(x=x, y=y, verbose=verbose, quiet=quiet)

As we've seen, `(flag("verbose") | flag("quiet")).optional()` succeeds on either `--verbose` or `--quiet`
or neither.

`option("x", type=int)` succeeds on `-x X`, where `X` is
some integer, binding that integer to the variable `"x"`. Similarly for `option("y", type=int)`.

`nonpositional` takes the three parsers:

- `(flag("verbose") | flag("quiet")).optional()`
- `option("x", type=int)`
- `option("y", type=int)`

and applies them in every order, until some order succeeds.

Applying the syntactic sugar:

>>> @command(
...     parsers=dict(kwargs=(flag("verbose") | flag("quiet")).optional()),
...     help=dict(x="the base", y="the exponent"),
... )
... def main(x: int, y: int, **kwargs):
...     pass  # do work

Here the `parsers` argument reserves a function argument (in this case, `kwargs`)
for a custom parser (in this case, `(flag("verbose") | flag("quiet")).optional()`)
using our lower-level syntax.  The `help` argument
assigns help text to the arguments (in this case `x` and `y`).

## Variations on the example
### Positional arguments
What if we wanted to supply `x` and `y` as positional arguments?

>>> flags = flag("verbose") | flag("quiet")
>>> p =  option("x", type=int) >> option("y", type=int) >> flags
>>> p.parse_args("-h")
usage: -x X -y Y [--verbose | --quiet]

This introduces a new parser combinator: [`>>`](#dollar_lambda.Parser.__rshift__) which evaluates
parsers in sequence. In this example, it would first evaluate the `option("x", type=int)` parser,
and if that succeeded, it would hand the unparsed remainder on to the `option("y", type=int)` parser,
and so on until all parsers have been evaluated or no more input remains.
 If any of the parsers fail, the combined parser fails:

>>> p.parse_args("-x", "1", "-y", "2", "--quiet")   # succeeds
{'x': 1, 'y': 2, 'quiet': True}
>>> p.parse_args("-typo", "1", "-y", "2", "--quiet")   # first parser fails
usage: -x X -y Y [--verbose | --quiet]
Expected '-x'. Got '-typo'
>>> p.parse_args("-x", "1", "-y", "2", "--typo")   # third parser fails
usage: -x X -y Y [--verbose | --quiet]
Expected '--verbose'. Got '--typo'

Unlike with `nonpositional` in the previous section, [`>>`](#dollar_lambda.Parser.__rshift__) requires the user to provide
arguments in a fixed order:
>>> p.parse_args("-y", "2", "-x", "1", "--quiet")   # fails
usage: -x X -y Y [--verbose | --quiet]
Expected '-x'. Got '-y'

When using positional arguments, it might make sense to drop the `-x` and `-y` flags:
>>> p = argument("x", type=int) >> argument("y", type=int) >> flags
>>> p.parse_args("-h")
usage: X Y [--verbose | --quiet]
>>> p.parse_args("1", "2", "--quiet")
{'x': 1, 'y': 2, 'quiet': True}

`argument` will bind input to a variable without checking for any special flag strings like
`-x` or `-y` preceding the input.


### Variable numbers of arguments

What if there was a special argument, `verbosity`,
that only makes sense if the user chooses `--verbose`?

>>> p = nonpositional(
...    ((flag("verbose") + option("verbosity", type=int)) | flag("quiet")),
...    option("x", type=int),
...    option("y", type=int),
... )

Remember that [`+`](#dollar_lambda.Parser.__add__) evaluates two parsers in both orders
and stopping at the first order that succeeds. So this allows us to
supply `--verbose` and `--verbosity` in any order.

>>> p.parse_args("-x", "1", "-y", "2", "--quiet")
{'x': 1, 'y': 2, 'quiet': True}
>>> p.parse_args("-x", "1", "-y", "2", "--verbose", "--verbosity", "3")
{'x': 1, 'y': 2, 'verbose': True, 'verbosity': 3}
>>> p.parse_args("-x", "1", "-y", "2", "--verbose")
usage: [--verbose --verbosity VERBOSITY | --quiet] -x X -y Y
Expected '--verbose'. Got '-x'

We could express the same logic with the `command` decorator:

>>> @command(
...     parsers=dict(
...         kwargs=flag("verbose") + option("verbosity", type=int) | flag("quiet")
...     ),
...     help=dict(x="the base", y="the exponent"),
... )
... def main(x: int, y: int, **kwargs):
...     pass  # do work

This is also a case where you might want to use `CommandTree`:

>>> tree = CommandTree()
...
>>> @tree.command(help=dict(x="the base", y="the exponent"))
... def base_function(x: int, y: int):
...     pass  # do work
...
>>> @base_function.command()
... def verbose_function(x: int, y: int, verbose: bool, verbosity: int):
...     args = dict(x=x, y=y, verbose=verbose, verbosity=verbosity)
...     print("invoked verbose_function with args", args)
...
>>> @base_function.command()
... def quiet_function(x: int, y: int, quiet: bool):
...     pass  # do work
...
>>> tree("-x", "1", "-y", "2", "--verbose", "--verbosity", "3")
invoked verbose_function with args {'x': 1, 'y': 2, 'verbose': True, 'verbosity': 3}

### [`many`](#dollar_lambda.Parser.many)

What if we want to specify verbosity by the number of times that `--verbose` appears?
For this we need `Parser.many`. Before showing how we could use `Parser.many` in this setting,
let's look at how it works.

`parser.many` takes `parser` and tries to apply it as many times as possible.
`Parser.many` is a bit like the `*` pattern, if you are familiar with regexes.
`parser.many` always succeeds:

>>> p = flag("verbose").many()
>>> p.parse_args()  # succeeds
{}
>>> p.parse_args("--verbose")  # still succeeds
{'verbose': True}
>>> p.parse_args("--verbose", "--verbose")  # succeeds, binding list to 'verbose'
{'verbose': [True, True]}

Now returning to the original example:

>>> p = nonpositional(
...     flag("verbose").many(),
...     option("x", type=int),
...     option("y", type=int),
... )
>>> args = p.parse_args("-x", "1", "-y", "2", "--verbose", "--verbose")
>>> args
{'x': 1, 'y': 2, 'verbose': [True, True]}
>>> verbosity = len(args['verbose'])
>>> verbosity
2

### [`many1`](#dollar_lambda.Parser.many1)

In the previous example, the parse will default to `verbosity=0` if no `--verbose` flags
are given.  What if we wanted users to be explicit about choosing a "quiet" setting?
In other words, what if the user actually had to provide an explicit `--quiet` flag when
no `--verbose` flags were given?

For this, we use `Parser.many1`. This method is like `Parser.many` except that it fails
when on zero successes (recall that `Parser.many` always succeeds). So if `Parser.many`
is like regex `*`, `Parser.many1` is like [`+`](#dollar_lambda.Parser.__add__). Take a look:

>>> p = flag("verbose").many()
>>> p.parse_args()  # succeeds
{}
>>> p = flag("verbose").many1()  # note many1(), not many()
>>> p.parse_args()  # fails
usage: --verbose [--verbose ...]
The following arguments are required: --verbose
>>> p.parse_args("--verbose")  # succeeds
{'verbose': True}

To compell that `--quiet` flag from our users, we can do the following:

>>> p = nonpositional(
...    ((flag("verbose").many1()) | flag("quiet")),
...    option("x", type=int),
...    option("y", type=int),
... )

Now omitting both `--verbose` and `--quiet` will fail:
>>> p.parse_args("-x", "1", "-y", "2")
usage: [--verbose [--verbose ...] | --quiet] -x X -y Y
Expected '--verbose'. Got '-x'
>>> p.parse_args("--verbose", "-x", "1", "-y", "2") # this succeeds
{'verbose': True, 'x': 1, 'y': 2}
>>> p.parse_args("--quiet", "-x", "1", "-y", "2") # and this succeeds
{'quiet': True, 'x': 1, 'y': 2}

# `CommandTree` Tutorial
`CommandTree` has already shown up in the
[Highlights section](#commandtree-for-dynamic-dispatch)
and in the [tutorial](#variations-on-the-example).
In this section we will give a more thorough treatment,
exposing some of the underlying logic and covering all
the variations in functionality that `CommandTree`
offers.

`CommandTree` draws inspiration
from the [`Click`](https://click.palletsprojects.com/) library.
`CommandTree.subcommand` (discussed [here](#commandtreesubcommand)) closely
approximates the functionality described in the [Commands and Groups](https://click.palletsprojects.com/en/8.1.x/commands/#command)
section of the `Click` documentation.

## `CommandTree.command`

First let's walk through the use of the `CommandTree.command` decorator, one step
at a time. First we define the object:

>>> tree = CommandTree()

Now we define at least one child function:

>>> @tree.command()
... def f1(a: int):
...     return dict(f1=dict(a=a)) # this can be whatever

`CommandTree.command` automatically converts the function arguments into a parser.
We can run the parser and pass its output to our function `f1` by calling `tree`:

>>> tree("-h")
usage: -a A

At this point the parser takes a single option `-a` that binds an `int` to `'a'`:
>>> tree("-a", "1")
{'f1': {'a': 1}}

Usually we would call `tree` with no arguments, and it would get its input from `sys.argv[1:]`.

>>> parser.TESTING = False  # False by default but needs to be true for doctests
>>> sys.argv[1:] = ["-a", "1"]  # simulate command line input
>>> tree()
{'f1': {'a': 1}}
>>> parser.TESTING = True

Now let's add a second child function:

>>> @tree.command()
... def f2(b: bool):
...     return dict(f2=dict(b=b))  # this can also be whatever

>>> tree("-h")
usage: [-a A | -b]

`tree` will execute either `f1` or `f2` based on which of the parsers succeeds.
This will execute `f1`:

>>> tree("-a", "1")
{'f1': {'a': 1}}

This will execute `f2`:

>>> tree("-b")
{'f2': {'b': True}}

This fails:

>>> tree()
usage: [-a A | -b]
The following arguments are required: -a

Often in cases where there are alternative sets of argument like this,
there is also a set of shared arguments. We can define a parent function
 to make our help text more concise and to allow the user to run the
 parent function when the child arguments are not provided.

>>> tree = CommandTree()
...
>>> @tree.command()
... def f1(a: int):  # this will be the parent function
...     return dict(f1=dict(a=a))

Now define a child function, `g1`:

>>> @f1.command()  # note f1, not tree
... def g1(a:int, b: bool):
...     return dict(g1=dict(b=b))

Make sure to include all the arguments of `f1` in `g1` or else
`g1` will fail when it is invoked. In its current state, `tree` sequences
 the arguments of `f1` and `g1`:

>>> tree("-h")
usage: -a A -b

As before we can define an additional child function to induce alternative
argument sets:

>>> @f1.command()  # note f1, not tree
... def g2(a: int, c: str):
...     return dict(g2=dict(c=c))

Note that our usage message shows `-a A` preceding the brackets because it corresponds
to the parent function:
>>> tree("-h")
usage: -a A [-b | -c C]

To execute `g1`, we give the `-b` flag:
>>> tree("-a", "1", "-b")
{'g1': {'b': True}}

To execute `g2`, we give the `-c` flag:
>>> tree("-a", "1", "-c", "foo")
{'g2': {'c': 'foo'}}

Also, note that `tree` can have arbitrary depth:

>>> @g1.command()  # h1 is a child of g1
... def h1(a: int, b: bool, d: float):
...    return dict(h1=dict(d=d))

Note the additional `-d D` argument on the left side of the `|` pipe:

>>> tree("-h")
usage: -a A [-b -d D | -c C]

That comes from the third argument of `h1`.

## `CommandTree.subcommand`
Often we want to explicitly specify which function to execute by naming it on the command line.
This would implement functionality similar to
[`ArgumentParser.add_subparsers`](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers)
or [`Click.command`](https://click.palletsprojects.com/en/8.1.x/commands/#command).

For this we would use the `CommandTree.subcommand` decorator:

>>> tree = CommandTree()
...
>>> @tree.command()
... def f1(a: int):
...     return dict(f1=dict(a=a))
...
>>> @f1.subcommand()  # note subcommand, not command
... def g1(a:int, b: bool):
...     return dict(g1=dict(b=b))
...
>>> @f1.subcommand()  # again, subcommand, not command
... def g2(a: int, c: str):
...     return dict(g2=dict(c=c))

Now the usage message indicates that `g1` and `g2` are required arguments:
>>> tree("-h")
usage: -a A [g1 -b | g2 -c C]

Now we would select g1 as follows:
>>> tree("-a", "1", "g1", "-b")
{'g1': {'b': True}}

And g2 as follows:
>>> tree("-a", "1", "g2", "-c", "foo")
{'g2': {'c': 'foo'}}

You can freely mix and match `subcommand` and `command`:

>>> tree = CommandTree()
...
>>> @tree.command()
... def f1(a: int):
...     return dict(f1=dict(a=a))
...
>>> @f1.subcommand()
... def g1(a:int, b: bool):
...     return dict(g1=dict(b=b))
...
>>> @f1.command()  # note command, not subcommand
... def g2(a: int, c: str):
...     return dict(g2=dict(c=c))

Note that the left side of the pipe (corresponding to the `g1` function)
requires a `"g1"` argument to run but the right side (corresponding to the `g2` function)
does not:

>>> tree("-h")
usage: -a A [g1 -b | -c C]

# Use with config files
A common use case is to have a config file with default values that arguments should
fall back to if not provided on the command line. Instead of implementing specific functionality
itself, `$λ` accommodates this situation by simply getting out of the way, thereby affording the
user the most flexibility in terms of accessing and using the config file. Here is a simple example.

```
# example-config.json
.. include:: ../example-config.json
```

Define a parser with optional values where you want to be able to fall back to the config file:
>>> p = option("x", type=int).optional() >> argument("y", type=int)
>>> p.parse_args("-h")
usage: -x X Y

In this example, `-x X` can be omitted, falling back to the config, but the positional argument
`Y` will be required.

Make sure that the optional arguments do not have default values or else the config value will
always be overridden.
Inside main, load the config and update with any arguments provided on the command line:
>>> import json
>>> def main(**kwargs):
...     with open("example-config.json") as f:
...         config = json.load(f)
...
...     config.update(kwargs)
...     return config

Override the value in the config by providing an explicit argument:
>>> main(**p.parse_args("-x", "0", "1"))
{'x': 0, 'y': 1}

Fall back to the value in the config by not providing an argument for `x`:
>>> main(**p.parse_args("2"))
{'x': 1, 'y': 2}

We can also write this with `@command` syntax:

>>> @command(
...     parsers=dict(
...         y=argument("y", type=int),
...         kwargs=option("x", type=int).optional(),
...     )
... )
... def main(y: int, **kwargs):
...     with open("example-config.json") as f:
...         config = json.load(f)
...
...     config.update(**kwargs, y=y)
...     return config
>>> main("-x", "0", "1")  # override config value
{'x': 0, 'y': 1}
>>> main(2)  # fall back to config value
{'x': 1, 'y': 2}

# Nesting output
By default introducing a `.` character into the name of an `argument`, `option`, or `flag` will
induce nested output:
>>> argument("a.b", type=int).parse_args("1")
{'a': {'b': 1}}
>>> option("a.b", type=int).parse_args("--a.b", "1")
{'a': {'b': 1}}
>>> flag("a.b").parse_args("--a.b")
{'a': {'b': True}}

This mechanism handles collisions:
>>> nonpositional(flag("a.b"), flag("a.c")).parse_args("--a.b", "--a.c")
{'a': {'b': True, 'c': True}}

even when mixing nested and unnested output:
>>> nonpositional(flag("a"), flag("a.b")).parse_args("-a", "--a.b")
{'a': [True, {'b': True}]}

It can also go arbitrarily deep:
>>> nonpositional(flag("a.b.c"), flag("a.b.d")).parse_args("--a.b.c", "--a.b.d")
{'a': {'b': {'c': True, 'd': True}}}

This behavior can always be disabled by setting `nesting=False` (or just not using `.` in the name).

# Ignoring arguments
There may be cases in which a user wants to provide certain arguments on the
command line that `$λ` should ignore (not return in the output of `Parser.parse_args`
or pass to the a decorated function). Suppose we wish to ignore any arguments starting
with the `--config-` prefix:

>>> regex = r"config-\\S*"
>>> config_parsers = flag(regex) | option(regex)

In the case of ordered arguments, we simply use the `ignore` method:

>>> p = flag("x") >> config_parsers.ignore() >> flag("y")

This will ignore any argument that starts with `--config-` and comes between `x` and `y`:
>>> p.parse_args("-x", "--config-foo", "-y")
{'x': True, 'y': True}

Because of the way we defined `config_parsers`, this also works with `option`:
>>> p.parse_args("-x", "--config-bar", "1", "-y")
{'x': True, 'y': True}

In the case of nonpositional arguments, use the `repeated` keyword:
>>> p = nonpositional(flag("x"), flag("y"), repeated=config_parsers.ignore())

Now neither `config-foo` nor `config-bar` show up in the output:
>>> p.parse_args("-x", "-y", "--config-foo", "--config-bar", "1")
{'x': True, 'y': True}

This works regardless of order:
>>> p.parse_args("--config-baz", "1", "-y", "--config-foz", "-x")
{'y': True, 'x': True}

And no matter how many matches are found:
>>> p.parse_args(
...     "--config-foo",
...     "1",
...     "--config-bar",
...     "-y",
...     "--config-baz",
...     "2",
...     "-x",
...     "--config-foz",
... )
{'y': True, 'x': True}

The same technique can be used with decorators:
>>> @command(repeated=config_parsers.ignore())
... def f(x: bool, y: bool):
...    return dict(x=x, y=y)
>>> f("-x", "-y", "--config-foo", "--config-bar", "1")
{'x': True, 'y': True}

And similarly with `CommandTree`.

# Why `$λ`?

`$λ` can handle many kinds of argument-parsing patterns
that are either very awkward, difficult, or impossible with other parsing libraries.
In particular, we emphasize the following qualities:

### Versatile
`$λ` provides high-level functionality equivalent to other parsers. But unlike other parsers,
it permits low-level customization to handle arbitrarily complex parsing patterns.
There are many parsing patterns that `$λ` can handle which are not possible with other parsing libraries.

### Type-safe
`$λ` uses type annotations as much as Python allows. Types are checked using [`MyPy`](
https://mypy.readthedocs.io/en/stable/index.html#) and exported with the package so that users can also benefit from
the type system. Furthermore, with rare exceptions, `$λ` avoids mutations and side-effects and preserves [referential
transparency](https://en.wikipedia.org/wiki/Referential_transparency). This makes it easier for the type-checker _and
for the user_ to reason about the code.

### Concise
`$λ` provides many syntactic shortcuts for cutting down boilerplate:

- the `command` decorator and the `CommandTree` object for automatically building parsers from function signatures.
- operators like [`>>`](#dollar_lambda.Parser.__rshift__),
[`|`](#dollar_lambda.Parser.__or__), [`^`](#dollar_lambda.Parser.__xor__),
and [`+`](#dollar_lambda.Parser.__add__) (and [`>=`](#dollar_lambda.Parser.__ge__) if you want to get fancy)

### Lightweight
`$λ` is written in pure python with no dependencies
(excepting [`pytypeclass`](https://github.com/ethanabrooks/pytypeclass)
which was written expressly for this library and has no dependencies).
`$λ` will not introduce dependency conflicts and it installs in a flash.
"""


__pdoc__ = {}

from dollar_lambda.args import Args, field
from dollar_lambda.decorators import CommandTree, command
from dollar_lambda.parser import (
    Parser,
    apply,
    argument,
    defaults,
    flag,
    item,
    matches,
    nonpositional,
    option,
    sat,
)

__all__ = [
    "Parser",
    "apply",
    "argument",
    "matches",
    "flag",
    "item",
    "nonpositional",
    "option",
    "sat",
    "Args",
    "defaults",
    "field",
    "command",
    "CommandTree",
]


__pdoc__["Parser.__add__"] = True
__pdoc__["Parser.__or__"] = True
__pdoc__["Parser.__xor__"] = True
__pdoc__["Parser.__rshift__"] = True
__pdoc__["Parser.__ge__"] = True
