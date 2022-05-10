.. include:: /_inc/attn-doc-freewheel.rsti

**********
Python API
**********

This document contains information for scripting in Python. The web interface
is `available here <https://logic.dougowings.net>`_.

.. contents:: :local:

Installation
============

Docker
------

To run the Docker image from Docker Hub:

    1. Run the command::

        docker run -p 8080:8080 owings1/pytableaux:latest

    2. Access the web interface at http://localhost:8080

Git
---

To install from git source, follow these steps. Note that Python 3.10.1
or later is required.

    1. Download the source, for example::

        git clone https://github.com/owings1/pytableaux
        cd pytableaux
    
    2. Install dependencies::

        python3 -m pip install --upgrade future jinja2 cherrypy prometheus_client simplejson

    3. Launch the web interface, for example::

        python3 -m pytableaux.web

    4. Then access http://localhost:8080

Running
=======

The following is an example for building a proof in {@CPL} for Modus Ponens::

    from pytableaux.lang import Parser
    from pytableaux.proof import Tableau, TabWriter

    # Create an argument
    argument = Parser().argument('b', ('Uab', 'a'))

    # Build a tableau for the logic CPL
    tableau = Tableau('CPL', argument).build()
    # This one should be valid!
    assert proof.valid

    # Output the proof
    text = TabWriter('text').write(tableau)
    print(text)

The full API docs are available :doc:`here <index>`.

Development
===========

For development information, refer to the `README on GitHub`_

Contributing
============

To contribute in any way (documentation, code, testing, suggestions, etc.), contact
me at doug@dougowings.net. You can also submit issues and merge requests
on `GitHub`_.

.. _GitHub: https://github.com/owings1/pytableaux
.. _README on GitHub: https://github.com/owings1/pytableaux/blob/main/README.md