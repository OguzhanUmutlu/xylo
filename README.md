# Xylo

A powerful template engine with Python expression evaluation.

## Installation

```bash
pip install xylo.py
```

## Usage

```python
from xylo import xylo

# Basic expressions
xylo("text $(1 + 5)")  # "text 6"

# Variables via context
xylo("Hello $(name)!", {"name": "World"})  # "Hello World!"

# Conditionals
xylo("$if(x > 5) Big $else Small $end", {"x": 10})  # " Big "

# Loops
xylo("$for(i in range(3)) $(i) $end")  # " 0  1  2 "

# Functions
xylo('$function(greet, name) Hello, $(name)! $end $call(greet, "World")')  # "  Hello, World! "
```

## Features

- **Expressions**: `$(expression)` - Evaluate and insert Python expressions
- **Exec**: `$exec(code)` - Execute Python code without output
- **Conditionals**: `$if(cond) ... $elif(cond) ... $else ... $end`
- **Loops**: `$for(var in iterable) ... $end`, `$while(cond) ... $end`
- **Functions**: `$function(name, args) ... $end` and `$call(name, args)`
- **Switch**: `$switch(expr) $case(val) ... $default ... $end`
- **Error handling**: `$try ... $catch(e) ... $end`, `$raise(msg)`, `$assert(cond)`
- **Context managers**: `$with(expr as var) ... $end`
- **Control flow**: `$break`, `$continue`, `$return`

## License

MIT

