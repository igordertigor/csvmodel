This tests generally the use with validating a csv file using pydantic. To do so, we first create a csv file
  $ echo Employee,Email,Salary > employees.csv
  $ echo Fred,fred@company.com,50000 >> employees.csv
  $ echo Tina,Tina123@company.com,80000 >> employees.csv
  $ echo Alfred,Alfred@home.com,60000 >> employees.csv
  $ cat employees.csv
  Employee,Email,Salary
  Fred,fred@company.com,50000
  Tina,Tina123@company.com,80000
  Alfred,Alfred@home.com,60000

We want to validate this data against a pydantic model. 
  $ echo 'from pydantic import BaseModel, EmailStr' > model.py
  $ echo '' >> model.py
  $ echo 'class Model(BaseModel):' >> model.py
  $ echo '    Employee: str'       >> model.py
  $ echo '    Email: EmailStr'     >> model.py
  $ echo '    Salary: float'       >> model.py
  $ cat model.py
  from pydantic import BaseModel, EmailStr
  
  class Model(BaseModel):
      Employee: str
      Email: EmailStr
      Salary: float

Now we want to validate our data against this schema:
  $ csvmodel --pydantic-model="model.py:Model" employees.csv

We will now add another line with an error: The salary is not a valid number
  $ echo Jimmy,jim@intership.com,15k >> employees.csv
  $ csvmodel --pydantic-model="model.py:Model" employees.csv
  employees.csv:5: Issue in column Salary: value is not a valid float
  [1]

Note how this provides the offending line number and the issue with that line. We can accomplish the same by using a configuration file:
  $ echo "[csvmodel]" > csvmodel.ini
  $ echo "schema = file:model.py:Model" >> csvmodel.ini
  $ echo "validator = pydantic" >> csvmodel.ini

Now we can just run
  $ csvmodel employees.csv
  employees.csv:5: Issue in column Salary: value is not a valid float
  [1]

In contrast to the jsonschema version, pydantic also supports multiple errors on the same line. Here is a particularly bad line:
  $ echo Carla,carla_at_company.com,tdb >> employees.csv
  $ csvmodel employees.csv
  employees.csv:5: Issue in column Salary: value is not a valid float
  employees.csv:6: Issue in column Email: value is not a valid email address
  employees.csv:6: Issue in column Salary: value is not a valid float
  [1]

Notice how both issues on line 6 are detected.
