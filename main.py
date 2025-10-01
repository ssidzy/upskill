from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

class details:
    def __init__(self, name, age):
        self.name=name,
        self.age=age

    name: str
    age: int

data1 = {
    "name":"Siddarth",
    "age": 26,
}

data2 = {
    "name":"Siddarth",
    "age": "26",
}

user1 = User(**data1)
user3 = User(**data2)


print(user1.name, user1.age, type(user1.name), type(user1.age))
#print(user2.name, user2.age)
print(user3.name, user3.age, type(user3.name), type(user3.age))
#print(user4.name, user4.age)

user2 = details("upasana", 14)
print(user2.name, user2.age, type(user2.name), type(user2.age))

user4 = details(name="laptop", age="14")
#user4.name , user4.age =  "Upasana",18
print(user4.name, user4.age, type(user4.name), type(user4.age))




