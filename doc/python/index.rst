.. include:: /include/attn-doc-freewheel.rst

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
    
    2. Install dependencies::

        pip install future jinja2 cherrypy prometheus_client simplejson

    3. Launch the web interface, for example::

        python src/web.py

    4. Then access http://localhost:8080

Quick Start
===========

The following is an example for building a proof in {@CPL} for Modus Ponens::

    from parsers import parse_argument
    from proof.tableaux import Tableau
    from proof.writers import write_tableau

    # Create an argument
    argument = parse_argument(conclusion='b', premises=['Uab', 'a'])

    # Build a tableau for the logic CPL
    tableau = Tableau('CPL', argument)
    tableau.build()

    # This one should be valid!
    assert proof.valid

    # Output the proof
    output = write_tableau(tableau)
    print(output)

This parses with the default notation (Polish), builds the proof, and outputs
a tableau in the default format (text).


API Reference
==============

The full API docs are available :doc:`here <modules/index>`.

If you are interested in building your own proofs, scripting, and
customizing the output, I recommend looking at the following modules:

* parsers
* lexicals
* proof.writers

If you are interested in customize rules, building your own logic, or
curious about how the internals, you could take a look at these modules:

* proof.tableaux
* logics.fde

.. toctree::
   :maxdepth: 2

   modules/index

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