# pytableaux

A multi-logic proof generator.

For the deployed site, [see here][site]. For the documentation, [see here][doc].

## Docker

```bash
cd ~/git/pytableaux

# build the image
docker build -t owings1/pytableaux:latest docker

# set container parameters, choose different host port, container name if desired.
REPO_HOME=`pwd`
HOST_PORT=8080
CONT_NAME=pytableaux

# create the container
docker create --name $CONT_NAME -v $REPO_HOME:/mnt/repo -p $HOST_PORT:8080 -e PY_HOST=0.0.0.0 owings1/pytableaux

# start the container
docker start $CONT_NAME
```

## Copyright & License

Copyright (C) 2014-2017 Doug Owings. Released under the [GNU Affero General Public License 3.0][license] or later.

[site]: http://logic.dougowings.net
[doc]: http://logic.dougowings.net/doc/
[license]: https://www.gnu.org/licenses/agpl-3.0.en.html