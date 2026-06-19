from pydantic import BaseModel, ValidationError

class User(BaseModel):
    username: str
    age: int

try:
    # This will fail because 'age' should be an int, and 'username' is missing
    user = User(age="not-a-number")
except ValidationError as e:
    # Loop through each individual field error
    for error in e.errors():
        # 'loc' contains the path to the field (column) as a tuple
        column_name = error['loc'][0]
        error_type = error['type']
        error_message = error['msg']
        
        print(f"Column: {column_name} | Error: {error_message} ({error_type})")
