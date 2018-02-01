# Login to portal.student.kit.ac.jp

This module can login to https://portal.student.kit.ac.jp/ and access any other pages limited access to students or 
teacher of Kyoto Institute of Technology. 

## Requirements

* Python 3.5 or later
* beautifulsoup4==4.6.0
* lxml==4.1.1
* requests==2.18.4

## Usage

This module require your username and password to auth. First, create instance of `shibboleth_login.ShibbolethClient`.

```python
from shibboleth_login import ShibbolethClient

client = ShibbolethClient('your username', 'your passsword')
```

Access to any other pages

```python
from shibboleth_login import ShibbolethClient

client = ShibbolethClient('your username', 'your passsword')
try:
    res = client.get('URL which you want to access')
    print(type(res)) # => <class 'requests.models.Response'>
except Exception:
    # error handling
finally:
    client.close()
```
Now, you can only use 'get' method. Any other method, for example 'post', is not implemented yet. 
'get' method return 'requests.models.Response' object. So you simply use it as requests module. 

with `with` statement

```python
with ShibbolethClient('your username', 'your password') as client:
    res = client.get('URL which you want to access')
    print(type(res)) # => <class 'requests.models.Response'>
```

## License

MIT

## Author

pudding
