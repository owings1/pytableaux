************
Python API
************

Pytableaux consists of a web interface, `available here <https://logic.dougowings.net>`_,
as well as a Python package for scripting. 

Quick Start
===========

The following is an example for building a proof in {@CPL} for Modus Ponens::

    from parsers import parse_argument
    from tableaux import Tableau
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

Installation
============

To run the Docker image from Docker Hub:

    1. Run the command::

        docker run -p 8080:8080 owings1/pytableaux:latest

    2. Access the web interface at http://localhost:8080

To install natively:

    1. Download the source, for example::

        git clone https://github.com/owings1/pytableaux
    
    2. Install dependencies::

        pip install future jinja2 cherrypy prometheus_client

    3. Launch the web interface, for example::

        python src/web.py

    4. Then access http://localhost:8080

API Docs
=========

If you are interseted in building your own proofs, scripting, and
customizing the output, I recommend looking at the following modules:

* parsers
* proof.writers
* lexicals

If you are interested in customize rules, building your own logic, or
curious about how the internals, you could take a look at these modules:

* tableaux
* proof.rules
* logics.fde

The full API docs are available :ref:`here <api-index>`

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