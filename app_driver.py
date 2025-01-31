import requests as req

def create_user_test():
    data = {
        "username": "modio",
        "email": "gio@gmail.com",
        "password": "test123"
    }
    request = req.post("http://127.0.0.1:8000/create_user", json=data)
    print(request.json())
    
def get_user_data():
    response = req.get("http://127.0.0.1:8000/user/milk")
    print(response.json())
    
def sign_in_test():
    data = {
        "username": "milk",
        "password": "johndoe"
    }
    request = req.post("http://127.0.0.1:8000/makepost", json=data)
    print(request.json())

def cookie_test():
    response = req.get("http://127.0.0.1:8000/")
    print(response.json())    

sign_in_test()
