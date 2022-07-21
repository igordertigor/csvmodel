This is testing a multifile setup, where one file is validated against a jsonschema and the other against a pydantic model
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

We will now use a pydantic model for the second file
  $ echo "from pydantic import BaseModel, EmailStr" > model.py
  $ echo "from enum import Enum"                   >> model.py
  $ echo ""                                        >> model.py
  $ echo "class Status(str, Enum):"                >> model.py
  $ echo "    active = 'active'"                   >> model.py
  $ echo "    inactive = 'inactive'"               >> model.py
  $ echo ""                                        >> model.py
  $ echo "class Customer(BaseModel):"              >> model.py
  $ echo "    Email: EmailStr"                     >> model.py
  $ echo "    ProductKey: int"                     >> model.py
  $ echo "    Status: Status"                      >> model.py
  $ cat model.py
  from pydantic import BaseModel, EmailStr
  from enum import Enum
  
  class Status(str, Enum):
      active = 'active'
      inactive = 'inactive'
  
  class Customer(BaseModel):
      Email: EmailStr
      ProductKey: int
      Status: Status

Now we use a config file to specify which file gets validated how:
  $ echo "[csvmodel:employees.csv]"             > csvmodel.ini
  $ echo "schema = file:employees.json"        >> csvmodel.ini
  $ echo "validator = jsonschema"              >> csvmodel.ini
  $ echo ""                                    >> csvmodel.ini
  $ echo "[csvmodel:customers.csv]"            >> csvmodel.ini
  $ echo "schema = file:model.py:Customer"     >> csvmodel.ini
  $ echo "validator = pydantic"                >> csvmodel.ini
  $ echo "separator = ;"                       >> csvmodel.ini

Now run everything together
  $ csvmodel *.csv
  customers.csv:2: Issue in column Status: value is not a valid enumeration member; permitted: 'active', 'inactive'
  customers.csv:3: Issue in column ProductKey: value is not a valid integer
  customers.csv:4: Issue in column Email: value is not a valid email address
  employees.csv:4: '45k' is not of type 'number'
  [1]
