# pytableaux

A multi-logic proof and semantic model generator.

## Web UI

For the live site, [see here][site].

## Docker

The docker image is available on [Docker Hub][dockerhub].

```bash
docker run -p 8080:8080 owings1/pytableaux:latest
```

The web UI should then be available on port 8080, e.g. `http://localhost:8080`.

## Documentation

For the live documentation, [see here][doc]. If you deployed the docker container,
the documentation is available at `/doc`, e.g. `http://localhost:8080/doc`.

## Implemented Logics

Bivalent

- **CPL** - Classical Predicate Logic
- **CFOL** - Classical First-Order Logic

Many-valued

- **FDE** - First Degree Entailment
- **K3** - Strong Kleene Logic
- **K3W** - Weak Kleene Logic
- **K3WQ** - Weak Kleene with alternate quantification
- **B3E** - Bochvar 3-valued External Logic
- **GO** - Gappy Object Logic
- **MH** - Paracomplete Hybrid Logic
- **L3** - Łukasiewicz 3-valued Logic
- **G3** - Gödel 3-valued Logic
- **LP** - Logic of Paradox
- **NH** - Paraconsistent Hybrid Logic
- **P3** - Emil Post 3-valued Logic
- **RM3** - R-mingle 3

Bivalent Modal

- **K** - Kripke Normal Modal Logic
- **D** - Deontic Normal Modal Logic
- **T** - Reflexive Normal Modal Logic
- **S4** - S4 Normal Modal Logic
- **S5** - S5 Normal Modal Logic

## Dependencies

Python **3.11** or later is required.

To install requirements:

```bash
pip3 install -r requirements.txt
```

For system-level dependencies, refer to the [Dockerfile][dockerfile].

## Development

Run tests:

```bash
python3 -m pytest test
```

<!-- optional: python-Levenshtein -->

Build docs:

```bash
cd doc && make clean html
```

Build docker image

```bash
docker build  .
```

## Contributing

You can file any issues on [github][issues], or contact me directly [via email][mailto].

## Copyright & License

<!-- [copyright-begin] -->
Copyright (C) 2014-2023 Doug Owings. Released under the [GNU Affero General Public License 3.0][license] or later.
<!-- [copyright-end] -->

[site]: http://logic.dougowings.net
[doc]: http://logic.dougowings.net/doc/
[dockerhub]: https://hub.docker.com/r/owings1/pytableaux/
[dockerfile]: res/python3.dockerfile

<!-- [refs-begin] -->
[license]: https://www.gnu.org/licenses/agpl-3.0.en.html
[issues]: https://github.com/owings1/pytableaux/issues
[mailto]: mailto:doug@dougowings.net
<!-- [refs-end] -->
