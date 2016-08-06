# Login to portal.student.kit.ac.jp

This module can login to https://portal.student.kit.ac.jp/ and access any other pages limited access to students or 
teacher of Kyoto Institute of Technology. 

## Requirements

It is as follows. I verified this with Python 3.4.3 in Mac OS X 10.11.16.

* beautifulsoup4==4.5.1
* lxml==3.6.1
* requests==2.10.0


## Usage

This module require your username and password to auth. Login is very simple as follows.

```python
from login import ShibbolethClient

client = ShibbolethClient('your username', 'your passsword')
```

Access other pages

```python
from login import ShibbolethClient

client = ShibbolethClient('your username', 'your passsword')
with client:
    res = client.get('URL which you want to access')
    print(type(res)) # => <class 'requests.models.Response'>
```
Now, you can only use 'get' method in the 'with' statement. Any other method, for example 'post', is not implemented yet. 
'get' method return 'requests.models.Response' object. So you simply use it as requests module. 
When you exit 'with' statement, ShibbolethClient class automatically execute 'close()' method. You don't need to execute 'close()' expressly. 

