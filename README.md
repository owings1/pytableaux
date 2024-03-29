# pytableaux

A multi-logic proof and semantic model generator.

## Web UI

For the live site, [see here][site]. For documentation, [see here][doc].

## Implemented Logics

<!-- [logics-begin] -->

### Bivalent

- [**CPL** - Classical Predicate Logic][CPL]
- [**CFOL** - Classical First Order Logic][CFOL]

### Bivalent Modal

- [**K** - Kripke Normal Modal Logic][K]
- [**D** - Deontic Normal Modal Logic][D]
- [**T** - Reflexive Normal Modal Logic][T]
- [**S4** - S4 Normal Modal Logic][S4]
- [**S5** - S5 Normal Modal Logic][S5]

### Many-valued

- [**FDE** - First Degree Entailment][FDE]
- [**K<sub>3</sub>** - Strong Kleene Logic][K3]
- [**LP** - Logic of Paradox][LP]
- [**L<sub>3</sub>** - Łukasiewicz 3-valued Logic][L3]
- [**RM<sub>3</sub>** - R-mingle 3][RM3]
- [**K<sup>3</sup><sub>W</sub>** - Weak Kleene Logic][K3W]
- [**K<sup>3</sup><sub>WQ</sub>** - Weak Kleene alt-Q Logic][K3WQ]
- [**B<sup>3</sup><sub>E</sub>** - Bochvar 3 External Logic][B3E]
- [**G<sub>3</sub>** - Gödel 3-valued Logic][G3]
- [**MH** - Paracomplete Hybrid Logic][MH]
- [**NH** - Paraconsistent Hybrid Logic][NH]
- [**GO** - Gappy Object Logic][GO]
- [**P<sub>3</sub>** - Post 3-valued Logic][P3]

### Many-valued Modal

- [**KFDE** - FDE with K modal][KFDE]
- [**TFDE** - FDE with T modal][TFDE]
- [**S4FDE** - FDE with S4 modal][S4FDE]
- [**S5FDE** - FDE with S5 modal][S5FDE]
- [**KK<sub>3</sub>** - K<sub>3</sub> with K modal][KK3]
- [**TK<sub>3</sub>** - K<sub>3</sub> with T modal][TK3]
- [**S4K<sub>3</sub>** - K<sub>3</sub> with S4 modal][S4K3]
- [**S5K<sub>3</sub>** - K<sub>3</sub> with S5 modal][S5K3]
- [**KLP** - LP with K modal][KLP]
- [**TLP** - LP with T modal][TLP]
- [**S4LP** - LP with S4 modal][S4LP]
- [**S5LP** - LP with S5 modal][S5LP]
- [**KL<sub>3</sub>** - L<sub>3</sub> with K modal][KL3]
- [**TL<sub>3</sub>** - L<sub>3</sub> with T modal][TL3]
- [**S4L<sub>3</sub>** - L<sub>3</sub> with S4 modal][S4L3]
- [**S5L<sub>3</sub>** - L<sub>3</sub> with S5 modal][S5L3]
- [**KRM<sub>3</sub>** - RM<sub>3</sub> with K modal][KRM3]
- [**TRM<sub>3</sub>** - RM<sub>3</sub> with T modal][TRM3]
- [**S4RM<sub>3</sub>** - RM<sub>3</sub> with S4 modal][S4RM3]
- [**S5RM<sub>3</sub>** - RM<sub>3</sub> with S5 modal][S5RM3]
- [**KK<sup>3</sup><sub>W</sub>** - K<sup>3</sup><sub>W</sub> with K modal][KK3W]
- [**TK<sup>3</sup><sub>W</sub>** - K<sup>3</sup><sub>W</sub> with T modal][TK3W]
- [**TK<sup>3</sup><sub>WQ</sub>** - K<sup>3</sup><sub>WQ</sub> with T modal][TK3WQ]
- [**S4B<sup>3</sup><sub>E</sub>** - B<sup>3</sup><sub>E</sub> with S4 modal][S4B3E]
- [**S4K<sup>3</sup><sub>W</sub>** - K<sup>3</sup><sub>W</sub> with S4 modal][S4K3W]
- [**S4K<sup>3</sup><sub>WQ</sub>** - K<sup>3</sup><sub>WQ</sub> with S4 modal][S4K3WQ]
- [**S5K<sup>3</sup><sub>W</sub>** - K<sup>3</sup><sub>W</sub> with S5 modal][S5K3W]
- [**S5K<sup>3</sup><sub>WQ</sub>** - K<sup>3</sup><sub>WQ</sub> with S5 modal][S5K3WQ]
- [**KK<sup>3</sup><sub>WQ</sub>** - K<sup>3</sup><sub>WQ</sub> with K modal][KK3WQ]
- [**KB<sup>3</sup><sub>E</sub>** - B<sup>3</sup><sub>E</sub> with K modal][KB3E]
- [**TB<sup>3</sup><sub>E</sub>** - B<sup>3</sup><sub>E</sub> with T modal][TB3E]
- [**S5B<sup>3</sup><sub>E</sub>** - B<sup>3</sup><sub>E</sub> with S5 modal][S5B3E]
- [**S5G<sub>3</sub>** - G<sub>3</sub> with S5 modal][S5G3]
- [**KG<sub>3</sub>** - G<sub>3</sub> with K modal][KG3]
- [**TG<sub>3</sub>** - G<sub>3</sub> with T modal][TG3]
- [**S4G<sub>3</sub>** - G<sub>3</sub> with S4 modal][S4G3]
- [**S4GO** - GO S4 modal logic][S4GO]

<!-- [logics-end] -->

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
Copyright (C) 2014-2023, Doug Owings. Released under the [GNU Affero General Public License v3.0 or later][license].
<!-- [copyright-end] -->

[dockerhub]: https://hub.docker.com/r/owings1/pytableaux/
[dockerfile]: Dockerfile

<!-- [refs-begin] -->
[site]: https://logic.dougowings.net
[doc]: https://logic.dougowings.net/doc
[license]: https://www.gnu.org/licenses/agpl-3.0.en.html
[issues]: https://github.com/owings1/pytableaux/issues
[mailto]: mailto:doug@dougowings.net
[CPL]: https://logic.dougowings.net/doc/logics/cpl.html
[CFOL]: https://logic.dougowings.net/doc/logics/cfol.html
[K]: https://logic.dougowings.net/doc/logics/k.html
[D]: https://logic.dougowings.net/doc/logics/d.html
[T]: https://logic.dougowings.net/doc/logics/t.html
[S4]: https://logic.dougowings.net/doc/logics/s4.html
[S5]: https://logic.dougowings.net/doc/logics/s5.html
[FDE]: https://logic.dougowings.net/doc/logics/fde.html
[K3]: https://logic.dougowings.net/doc/logics/k3.html
[LP]: https://logic.dougowings.net/doc/logics/lp.html
[L3]: https://logic.dougowings.net/doc/logics/l3.html
[RM3]: https://logic.dougowings.net/doc/logics/rm3.html
[K3W]: https://logic.dougowings.net/doc/logics/k3w.html
[K3WQ]: https://logic.dougowings.net/doc/logics/k3wq.html
[B3E]: https://logic.dougowings.net/doc/logics/b3e.html
[G3]: https://logic.dougowings.net/doc/logics/g3.html
[MH]: https://logic.dougowings.net/doc/logics/mh.html
[NH]: https://logic.dougowings.net/doc/logics/nh.html
[GO]: https://logic.dougowings.net/doc/logics/go.html
[P3]: https://logic.dougowings.net/doc/logics/p3.html
[KFDE]: https://logic.dougowings.net/doc/logics/kfde.html
[TFDE]: https://logic.dougowings.net/doc/logics/tfde.html
[S4FDE]: https://logic.dougowings.net/doc/logics/s4fde.html
[S5FDE]: https://logic.dougowings.net/doc/logics/s5fde.html
[KK3]: https://logic.dougowings.net/doc/logics/kk3.html
[TK3]: https://logic.dougowings.net/doc/logics/tk3.html
[S4K3]: https://logic.dougowings.net/doc/logics/s4k3.html
[S5K3]: https://logic.dougowings.net/doc/logics/s5k3.html
[KLP]: https://logic.dougowings.net/doc/logics/klp.html
[TLP]: https://logic.dougowings.net/doc/logics/tlp.html
[S4LP]: https://logic.dougowings.net/doc/logics/s4lp.html
[S5LP]: https://logic.dougowings.net/doc/logics/s5lp.html
[KL3]: https://logic.dougowings.net/doc/logics/kl3.html
[TL3]: https://logic.dougowings.net/doc/logics/tl3.html
[S4L3]: https://logic.dougowings.net/doc/logics/s4l3.html
[S5L3]: https://logic.dougowings.net/doc/logics/s5l3.html
[KRM3]: https://logic.dougowings.net/doc/logics/krm3.html
[TRM3]: https://logic.dougowings.net/doc/logics/trm3.html
[S4RM3]: https://logic.dougowings.net/doc/logics/s4rm3.html
[S5RM3]: https://logic.dougowings.net/doc/logics/s5rm3.html
[KK3W]: https://logic.dougowings.net/doc/logics/kk3w.html
[TK3W]: https://logic.dougowings.net/doc/logics/tk3w.html
[TK3WQ]: https://logic.dougowings.net/doc/logics/tk3wq.html
[S4B3E]: https://logic.dougowings.net/doc/logics/s4b3e.html
[S4K3W]: https://logic.dougowings.net/doc/logics/s4k3w.html
[S4K3WQ]: https://logic.dougowings.net/doc/logics/s4k3wq.html
[S5K3W]: https://logic.dougowings.net/doc/logics/s5k3w.html
[S5K3WQ]: https://logic.dougowings.net/doc/logics/s5k3wq.html
[KK3WQ]: https://logic.dougowings.net/doc/logics/kk3wq.html
[KB3E]: https://logic.dougowings.net/doc/logics/kb3e.html
[TB3E]: https://logic.dougowings.net/doc/logics/tb3e.html
[S5B3E]: https://logic.dougowings.net/doc/logics/s5b3e.html
[S5G3]: https://logic.dougowings.net/doc/logics/s5g3.html
[KG3]: https://logic.dougowings.net/doc/logics/kg3.html
[TG3]: https://logic.dougowings.net/doc/logics/tg3.html
[S4G3]: https://logic.dougowings.net/doc/logics/s4g3.html
[S4GO]: https://logic.dougowings.net/doc/logics/s4go.html
<!-- [refs-end] -->