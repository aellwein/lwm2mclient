
# lwm2mclient

A customizable LWM2M client written in Python 3.

# Installation

Prerequisite: Download and install [Python 3.6+](https://www.python.org/downloads/).
Preferred way of installation is using [virtualenv](https://docs.python.org/3/tutorial/venv.html).

* Setting up _virtualenv_ in some directory (the instructions on Windows are slightly different,
  please refer to the [documentation](https://docs.python.org/3/tutorial/venv.html)):
  ```sh
  # following command creates a virtualenv in the '.venv' subfolder 

  $ python3 -m venv .venv

  # activate virtualenv for the current shell
  # for Windows, use .\.venv\Scripts\activate.bat
  $ source .venv/bin/activate

  ```
* Now, run ``pip install -r requirements.txt`` to install this package in the activated virtualenv.


# Usage

## Running The Client

If you didn't previously, activate virtualenv for your shell.
Use ``./client.py`` command to connect LWM2M server listening on udp://localhost:5683 (for instance, a [Leshan](http://www.eclipse.org/leshan/) server).

**Note for Windows/Mac users:**

Because of the underlying transport implementation on Windows/Mac, 
see [aiocoap FAQ](https://aiocoap.readthedocs.io/en/latest/faq.html) for more details, 
the LwM2M client needs the ``--address`` argument to be set to some specific IP address on your system, 
the default IP address "::" would not work here. 

See also

```sh
./client.py --help
```

for all options.


## Client Data Model

The data for LWM2M objects hold by the client is represented in the file ``data.json``. The data model
for well-defined LWM2M objects (e.g. Device object) must match the object data definition
specified in ``lwm2m-object-definitions.json``. For custom objects, both files must be adjusted.

## Execute Operations

Resources which provide an execute operation, are specified via string in ``data.json``. The
string name is evaluated to a method name, which should be contained in ``handlers.py``.
The signature for such a handler is  
  
  ```
      def method_name(*args, **kwargs):
         ...
  ```
  
The positional ``args`` arguments are not used. Provided arguments such as ``model``, ``path``, 
``payload`` and ``content_format`` are contained in the ``kwargs`` dictionary. See existing
handlers for example.

## Observe Operations

Resources which support Observe operations, must also be defined in ``handlers.py``. 
The signature of a handler for observe on object/instance/resource follows a convention:  

```
def observe_{object_id}_{instance_id}_{resource_id}(*args, **kwargs):
   ...
```
  
The positional ``args`` arguments are not used. Provided arguments such as ``notifier``, ``cancel``, 
``model``, ``path``,  ``payload`` and ``content_format`` are contained in the ``kwargs`` dictionary.  
A ``notifier`` argument is a function, which triggers a client-initiated notification and may be, e.g. called
periodically.  
A ``cancel`` argument can be used in order to cancel an existing observation.
See ``observe_3_0_13()`` example in ``handlers.py`` on how to trigger a periodic observation.  

# License

This project is licensed under the terms of [MIT License](LICENSE).

# ToDo

* [x] implement TLV encoding
* [x] implement Execute (via handlers)
* [x] implement Observe (via handlers)
* [x] implement Write 
* [ ] implement Cancel Observation (when [this issue](https://github.com/chrysn/aiocoap/issues/30) is resolved)
* [ ] improve data definition validation
* [ ] extend with REST API (for instrumenting it using 3rd party software)
* [ ] provide Dockerfile
* [ ] add DTLS support
* [ ] tests, docs & stuff
* [ ] fulfill SCRs from OMA (s. Tech Spec)
