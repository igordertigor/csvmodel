# csvmodel checks your csv files against a data model

This tools helps you keep your csv files valid, by validating each row against a specified [jsonschema](https://json-schema.org) or [pydantic](https://pydantic-docs.helpmanual.io) model. This way you can always be sure that your data is complete and valid.

## Install

You can install csvmodel from [pypi](https://pypi.org/project/csvmodel/) like this
```bash
pip install csvmodel
```

## Getting started

In this getting started guide, commands that you type are prefixed by a `$` sign, output is shown as is.
Let's create a csv file:

```
  $ echo "Employee,Email,Salary"               > employees.csv
  $ echo "Fred,fred@company.com,50000"        >> employees.csv
  $ echo "Tina,Tina123@company.com,80k"       >> employees.csv
  $ echo "Alfred,Alfred_at_home.com,60000"    >> employees.csv
```

We want to validate this csv file against the following json schema:

```
  $ echo '{'                                        > schema.json
  $ echo '  "type": "object",'                     >> schema.json
  $ echo '  "properties": {'                       >> schema.json
  $ echo '    "Employee": {"type": "string"},'     >> schema.json
  $ echo '    "Email": {'                          >> schema.json
  $ echo '      "type": "string",'                 >> schema.json
  $ echo '      "pattern": "^[a-z0-9.]+@[a-z0-9]+[.][a-z]{2,6}"' >> schema.json
  $ echo '    },'                                  >> schema.json
  $ echo '    "Salary": {"type": "number"}'        >> schema.json
  $ echo '  }'                                     >> schema.json
  $ echo '}'                                       >> schema.json
```

We can do so by using csvmodel like this:

```
  $ csvmodel --json-schema=schema.json employees.csv
  employees.csv:3: '80k' is not of type 'number'
  employees.csv:4: 'Alfred_at_home.com' does not match '^[a-z0-9.]+@[a-z0-9]+[.][a-z]{2,6}'
  [1]
```

This very quickly points us to the two issues with this file.
Imagine having to find these (in particular for a larger file) after you noticed that [pandas](https://pandas.pydata.org) made your "Salary" column have type "object".

Alternatively, you can specify your data expectations in the form of a pydantic model. Let's try that out now:

```
  $ echo 'from pydantic import BaseModel, EmailStr'   > model.py
  $ echo ''                                          >> model.py
  $ echo 'class Employee(BaseModel):'                >> model.py
  $ echo '    Employee: str'                         >> model.py
  $ echo '    Email: EmailStr'                       >> model.py
  $ echo '    Salary: float'                         >> model.py
```

Again, we can get errors like this:

```
  $ csvmodel --pydantic-model="model.py:Employee" employees.csv
  employees.csv:3: Issue in column Salary: value is not a valid float
  employees.csv:4: Issue in column Email: value is not a valid email address
  [1]
```

Again, we quickly get pointed to the issues in the csv file.

## Config file

csvmodel reads an ini-style configuration file from `csvmodel.ini` or any file passed to the `--config` option.
The default section is `[csvmodel]` with the following default values:
```ini
[csvmodel]
validator = jsonschema
schema = {"type": "object"}
separator = ,
```
Note that this schema will accept everything (so not very useful).

Here you see, that the *schema* is passed "inline", i.e. it is simply written as the argument for schema. This is equivalent to prefixing it with the string "inline:" like this:
```ini
schema = inline: {"type": "object"}
```
If you want to read the schema froma file, you would use the following syntax
```ini
schema = file:schema.json
```
For the `file:` schema, you can (for pydantic must) add the specific class you want to use. Let's say you want to use the `MyModel` class, you would use
```ini
schema = file:schema.py:MyModel
```

The options for *validator* are either "jsonschema" or "pydantic".

You can overwrite specific options (e.g. the schema) on a file specific basis by using separate sections like so
```ini
[csvmodel]
validator = pydantic

[csvmodel:employees.csv]
schema = file:src/model.py:Employee

[csvmodel:products.csv]
schema = file:src/model.py:Product
```

## Which validator?

In principle, both kinds of validator have advantages and disadvantages.

For jsonschema, we have
- A simple portable schema language
- Support for inline schema
- Not very readable
- No more than one error reported per line (this is an issue with the jsonschema validation itself)
- Complex datatypes can involve rather advanced regex acrobatics

For pydantic, we have
- It's python, no new language to learn
- No support for inline schema
- Very readable (it's python)
- Many complex data types are already implemented in pydantic
- Multiple errors can be reported for the same line.


## Why would I want csvmodel?

Tools like [flake8](https://flake8.pycqa.org/en/latest/) or [mypy](https://mypy.readthedocs.io/en/stable/index.html) are useful, because they spot weaknesses in python programs without needing to run the code.
However, python code is often data science code and we don't have the same checks for data files.
This is particularly relevant for small datasets, that get edited manually and consist of a few hundred kb (for larger datasets, formats are likely more structured and binary or you need to lift them from sources that already enforce some level of structure).
I wrote *csvmodel* for these small files to be run in a similar way as flake8: As part of your favourite editor.
My editor is nvim, so the integration is pretty straight forward, after writing the config file, I usually just run `:!csvmodel %`.
