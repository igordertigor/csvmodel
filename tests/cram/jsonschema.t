This tests generally the use with validating a csv file using a jsonschema. To do so, we first create a csv file
  $ echo Employee,Email,Salary > employees.csv
  $ echo Fred,fred@company.com,50000 >> employees.csv
  $ echo Tina,Tina123@company.com,80000 >> employees.csv
  $ echo Alfred,Alfred@home.com,60000 >> employees.csv
  $ cat employees.csv
  Employee,Email,Salary
  Fred,fred@company.com,50000
  Tina,Tina123@company.com,80000
  Alfred,Alfred@home.com,60000

We want to validate this data against a jsonschema. Jsonschema only provides relatively coarse validation, but it ensures for example, that all columns are entered and that numeric columns actually contain numbers.
  $ echo '{"type": "object", "properties": {"Employee": {"type": "string"}, "Email": {"type": "string"}, "Salary": {"type": "number"}}}' > schema.json

Now we want to validate our data against this schema:
  $ csvmodel --json-schema=schema.json employees.csv

We will now add another line with an error: The salary is not a valid number
  $ echo Jimmy,jim@intership.com,15k >> employees.csv
  $ csvmodel --json-schema=schema.json employees.csv
  employees.csv:5: '15k' is not of type 'number'
  [1]

Note how this provides the offending line number and the issue with that line. We can accomplish the same by using a configuration file:
  $ echo "[csvmodel]" > csvmodel.ini
  $ echo "schema = file:schema.json" >> csvmodel.ini
  $ echo "validator = jsonschema" >> csvmodel.ini

Now, we can just run
  $ csvmodel employees.csv
  employees.csv:5: '15k' is not of type 'number'
  [1]

We add some more lines to our csv files, some valid, some invalid
  $ echo Tony,t@c.com,35000 >> employees.csv
  $ echo Carla,42000 >> employees.csv
  $ echo Charles,cc@c.com,53000 >> employees.csv
  $ cat employees.csv
  Employee,Email,Salary
  Fred,fred@company.com,50000
  Tina,Tina123@company.com,80000
  Alfred,Alfred@home.com,60000
  Jimmy,jim@intership.com,15k
  Tony,t@c.com,35000
  Carla,42000
  Charles,cc@c.com,53000

Now we have two different errors: On line 5, we still have the invalid salary from Jimmy, but on line 7, we forgot the email for Carla.
  $ csvmodel employees.csv
  employees.csv:5: '15k' is not of type 'number'
  employees.csv:7: Missing 1 column
  [1]
