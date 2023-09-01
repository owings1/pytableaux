# pytableaux

A multi-logic proof and semantic model generator.

## Web UI

For the live site, [see here][site]. For documentation, [see here][doc].

## Implemented Logics

### Bivalent

- [**CPL** - Classical Predicate Logic][CPL]
- [**CFOL** - Classical First-Order Logic][CFOL]

### Bivalent Modal

- [**K** - Kripke Normal Modal Logic][K]
- [**D** - Deontic Normal Modal Logic][D]
- [**T** - Reflexive Normal Modal Logic][T]
- [**S4** - S4 Normal Modal Logic][S4]
- [**S5** - S5 Normal Modal Logic][S5]

### Many-valued

- [**FDE** - First Degree Entailment][FDE]
- [**K<sub>3</sub>** - Strong Kleene Logic][K3]
- [**K<sup>3</sup><sub>W</sub>** - Weak Kleene Logic][K3W]
- [**K<sup>3</sup><sub>WQ</sub>** - Weak Kleene with alternate quantification][K3WQ]
- [**B<sup>3</sup><sub>E</sub>** - Bochvar 3-valued External Logic][B3E]
- [**GO** - Gappy Object Logic][GO]
- [**MH** - Paracomplete Hybrid Logic][MH]
- [**L<sub>3</sub>** - Łukasiewicz 3-valued Logic][L3]
- [**G<sub>3</sub>** - Gödel 3-valued Logic][G3]
- [**LP** - Logic of Paradox][LP]
- [**NH** - Paraconsistent Hybrid Logic][NH]
- [**P<sub>3</sub>** - Emil Post 3-valued Logic][P3]
- [**RM<sub>3</sub>** - R-mingle 3][RM3]

### Many-valued Modal

- [**KFDE** - FDE with K modal][KFDE]
- [**KK<sub>3</sub>** - K<sub>3</sub> with K modal][KK3]
- [**KL<sub>3</sub>** - L<sub>3</sub> with K modal][KL3]
- [**KLP** - LP with K modal][KLP]

## Docker

The docker image is available on [Docker Hub][dockerhub].

```bash
docker run -p 8080:8080 owings1/pytableaux:latest
```

The web UI will then be available on port 8080, e.g. `http://localhost:8080`.

## Documentation

For the live documentation, [see here][doc]. If you deployed the docker container,
the documentation is available at `/doc`, e.g. `http://localhost:8080/doc`.

## Dependencies

Python **3.11** or later is required.

To install basic requirements:

```bash
pipenv install
```

To install requirements for the web interface:

```bash
pipenv install --categories="web-packages"
```

## Development

To install dev dependencies:

```bash
pipenv install --categoies="dev-packages web-packages"
```

Run tests:

```bash
python -m test
```

<!-- optional: python-Levenshtein -->
### Docs

To install doc building dependencies:

```bash
pipenv install --categoies="doc-packages"
```

Build docs:

```bash
python -m doc clean html
```

### Docker

Build docker image

```bash
docker build -t localhost/pytableaux:dev  .
```

For other targets (doc, test, etc.), seel the [Dockerfile][dockerfile]
## Contributing

You can file any issues on [github][issues], or contact me directly [via email][mailto].

## Copyright & License

<!-- [copyright-begin] -->
Copyright (C) 2014-2023 Doug Owings. Released under the [GNU Affero General Public License 3.0][license] or later.
<!-- [copyright-end] -->

[site]: http://logic.dougowings.net
[doc]: http://logic.dougowings.net/doc/
[dockerhub]: https://hub.docker.com/r/owings1/pytableaux/
[dockerfile]: Dockerfile

<!-- [refs-begin] -->
[license]: https://www.gnu.org/licenses/agpl-3.0.en.html
[issues]: https://github.com/owings1/pytableaux/issues
[mailto]: mailto:doug@dougowings.net
<!-- [refs-end] -->

[CPL]: http://logic.dougowings.net/doc/logics/cpl.html
[CFOL]: http://logic.dougowings.net/doc/logics/cfol.html

[K]: http://logic.dougowings.net/doc/logics/k.html
[D]: http://logic.dougowings.net/doc/logics/d.html
[T]: http://logic.dougowings.net/doc/logics/t.html
[S4]: http://logic.dougowings.net/doc/logics/s4.html
[S5]: http://logic.dougowings.net/doc/logics/s5.html

[FDE]: http://logic.dougowings.net/doc/logics/fde.html
[K3]: http://logic.dougowings.net/doc/logics/k3.html
[K3W]: http://logic.dougowings.net/doc/logics/k3w.html
[K3WQ]: http://logic.dougowings.net/doc/logics/k3wq.html
[B3E]: http://logic.dougowings.net/doc/logics/b3e.html
[GO]: http://logic.dougowings.net/doc/logics/go.html
[MH]: http://logic.dougowings.net/doc/logics/mh.html
[L3]: http://logic.dougowings.net/doc/logics/l3.html
[G3]: http://logic.dougowings.net/doc/logics/g3.html
[LP]: http://logic.dougowings.net/doc/logics/lp.html
[NH]: http://logic.dougowings.net/doc/logics/nh.html
[P3]: http://logic.dougowings.net/doc/logics/p3.html
[RM3]: http://logic.dougowings.net/doc/logics/rm3.html

[KFDE]: http://logic.dougowings.net/doc/logics/kfde.html
[KK3]: http://logic.dougowings.net/doc/logics/kk3.html
[KL3]: http://logic.dougowings.net/doc/logics/kl3.html
[KLP]: http://logic.dougowings.net/doc/logics/klp.html