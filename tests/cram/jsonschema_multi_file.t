This example is similar to the jsonschema.t one. However, it goes into less depth building up the files, but rather illustrates one more involved configuration that can handle multiple different schemata for different files.
  $ echo Employee,Email,Salary > employees.csv
  $ echo Jimmy,jim@company.com,55000 >> employees.csv
  $ echo Carla,ca@comp.com,64000 >> employees.csv
  $ echo Chris,crs1@one.com,45k >> employees.csv
  $ cat employees.csv
  Employee,Email,Salary
  Jimmy,jim@company.com,55000
  Carla,ca@comp.com,64000
  Chris,crs1@one.com,45k

  $ echo "Customer;Email;ProductKey;Status" > customers.csv
  $ echo "Charles;charles@users.com;48001;atcive" >> customers.csv
  $ echo "Tina;tt@ta.com;4838.1;inactive" >> customers.csv
  $ echo "Randall;rand@all;4884;active" >> customers.csv
  $ cat customers.csv
  Customer;Email;ProductKey;Status
  Charles;charles@users.com;48001;atcive
  Tina;tt@ta.com;4838.1;inactive
  Randall;rand@all;4884;active

These two files have different constraints:
  $ echo '{"type": "object", "properties": {"Employee": {"type": "string"}, "Email": {"type": "string", "pattern": "^[a-z0-9.]+@[a-z0-9]+[.][a-z0-9]{1,6}"},"Salary": {"type": "number"}}}' > employees.json
  $ cat employees.json | json_pp
  {
     "properties" : {
        "Email" : {
           "pattern" : "^[a-z0-9.]+@[a-z0-9]+[.][a-z0-9]{1,6}",
           "type" : "string"
        },
        "Employee" : {
           "type" : "string"
        },
        "Salary" : {
           "type" : "number"
        }
     },
     "type" : "object"
  }

  $ echo '{"type": "object", "properties": {"Customer": {"type": "string"}, "Email": {"type": "string", "pattern": "^[a-z0-9.]+@[a-z0-9]+[.][a-z0-9]{1,6}"}, "ProductKey": {"type": "integer"}, "Status": {"enum": ["active", "inactive"]}}}' > customers.json
  $ cat customers.json | json_pp
  {
     "properties" : {
        "Customer" : {
           "type" : "string"
        },
        "Email" : {
           "pattern" : "^[a-z0-9.]+@[a-z0-9]+[.][a-z0-9]{1,6}",
           "type" : "string"
        },
        "ProductKey" : {
           "type" : "integer"
        },
        "Status" : {
           "enum" : [
              "active",
              "inactive"
           ]
        }
     },
     "type" : "object"
  }

To test both files together, we can use the following config file
  $ echo "[csvmodel:employees.csv]" > csvmodel.ini
  $ echo "schema = file:employees.json" >> csvmodel.ini
  $ echo "" >> csvmodel.ini
  $ echo "[csvmodel:customers.csv]" >> csvmodel.ini
  $ echo "schema = file:customers.json" >> csvmodel.ini
  $ echo "separator = ;" >> csvmodel.ini

Note how this is excluding defaults (e.g. validator=jsonschema and separator=,).
  $ csvmodel employees.csv
  employees.csv:4: '45k' is not of type 'number'
  [1]

  $ csvmodel customers.csv
  customers.csv:2: 'atcive' is not one of ['active', 'inactive']
  customers.csv:3: '4838.1' is not of type 'integer'
  customers.csv:4: 'rand@all' does not match '^[a-z0-9.]+@[a-z0-9]+[.][a-z0-9]{1,6}'
  [1]

