# pytableaux

A multi-logic proof generator.

## Web UI

For the live site, [see here][site].

## Docker

The docker image is available on [Docker Hub][dockerhub].

```bash
docker run -d -p 8080:8080 --name pytableaux owings1/pytableaux:latest
```

The web UI should then be available on port 8080, e.g. `http://localhost:8080`.

## Documentation

For the live documentation, [see here][doc]. If you deployed the docker container,
the documentation is available at `/doc`, e.g. `http://localhost:8080/doc`.

## Contributing

Please file any issues on [bitbucket][issues].

## Copyright & License

Copyright (C) 2014-2017 Doug Owings. Released under the [GNU Affero General Public License 3.0][license] or later.

[site]: http://logic.dougowings.net
[doc]: http://logic.dougowings.net/doc/
[license]: https://www.gnu.org/licenses/agpl-3.0.en.html
[dockerhub]: https://hub.docker.com/r/owings1/pytableaux/
[issues]: https://bitbucket.org/owings1/pytableaux/issues