# pytest-docker-tools

You have written a software application (in any language) and have packaged in as a Docker image. Now you want to smoke test the built image or do some integration testing with other containers before releasing it. You:

 * want to reason about your environment in a similar way to a `docker-compose.yml`
 * want the environment to be automatically created and destroyed as tests run
 * don't want to have to write loads of boilerplate code for creating the test environment
 * want to be able to run the tests in parallel
 * want the tests to be reliable

`pytest-docker-tools` is a set of opinionated helpers for creating `py.test` fixtures for your smoke testing and integration testing needs.

This library gives you a set of 'fixture factories'. You can define your fixtures in your `conftest.py` and access them from all your tests.

```
from pytest_docker_tools import *

my_image = fetch('redis:latest')

my_image_2 = build(
  path='db'
)

my_data = volume()

my_microservice_backend = container(
    image='{my_image.id}',
    volumes={
      '{my_data.id}': {'bind': '/var/tmp'},
    }
)

my_microservice = container(
    image='{my_image_2.id}',
    environment={
      'DATABASE_IP': '{mydatabase.ips.primary}',
    },
    ports={
      '3679/tcp': None,
    }
)
```

You can now create a test that exercises your microservice:

```
def test_my_frobulator(my_microservice):
    socket = socket.socket()
    socket.connect('127.0.0.1', my_microservice.ports['3679/tcp'][0])
    ....
```

In this example all the dependencies will be resolved in order and once per session:

 * The latest redis:latest will be fetched
 * A container image will be build from the `Dockerfile` in the `db` folder.

Then once per test:

 * A new volume will be created
 * A new 'backend' container will be created from `redis:latest`. It will be attached to the new volume.
 * A new 'frontend' container will be created from the freshly built container. It will be given the IP if the backend via an environment variable. Port 3679 in the container will be exposed as an ephemeral port on the host.

The test can then run and access the container via its ephemeral high port. At the end of the test the environment will be thrown away.

If the test fails the `docker logs` output from each container will be captured and added to the test output.


## Factories

### Containers

To create a container in your tests use the `container` fixture factory.

```
from pytest_docker_tools import container

my_microservice_backend = container(image='redis:latest')
```

The default scope for this factory is `function`. This means a new container will be created for each test.

The `container` fixture factory supports all parameters that can be passed to the docker-py `run` method. See [here](https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run) for them all.

Any variables are interpolated against other defined fixtures. This means that a fixture can depend on other fixtures, and they will be built and run in order.

For example:

```
from pytest_docker_tools import container, fetch

my_microservice_backend_image = fetch('redis:latest')
my_microservice_backend = container(image='{my_microservice_backend_image.id}')
```

This will fetch the latest `redis:latest` first, and then run a container from the exact image that was pulled.

The container will be automatically deleted after the test has finished.


### Images

To pull an image from your default repository use the `fetch` fixture factory. To build an image from local source use the `build` fixture factory.

```
from pytest_docker_tools import build, fetch

my_image = fetch('redis:latest')

my_image_2 = build(
  path='db'
)
```

The default scope for this factory is `session`. This means the fixture will only build or fetch once per py.test invocation. The fixture will not be triggered until a test (or other fixture) tries to use it. This means you won't waste time building an image if you aren't running the test that uses it.


### Networks

By default any containers you create with the `container()` fixture factory will run on your default docker network. You can create a dedicated network for your test with the `network()` fixture factory.

```
from pytest_docker_tools import network

frontend_network = network()
```

The default scope for this factory is `function`. This means a new network will be created for each test that is executed.

The network will be removed after the test using it has finished.


#### Volumes

In the ideal case a Docker container instance is read only. No data inside the container is written to, if it is its to a volume. If you are testing that your service can run read only you might want to mount a rw volume. You can use the `volume()` fixture factory to create a Docker volume with a lifecycle tied to your tests.

```
from pytest_docker_tools import volume

backend_storage = volume()
```

The default scope for this factory is `function`. This means a new volume will be created for each test that is executed. The volume will be removed after the test using it has finished.
