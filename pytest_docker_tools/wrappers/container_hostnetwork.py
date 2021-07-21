from .container import Container

# TODO: remove this as it is not required anymore
class WrapperContainerHostNetwork(Container):
    def ready(self):
        self._container.reload()

        if self.status == "exited":
            raise ContainerFailed(
                self,
                f"Container {self.name} has already exited before we noticed it was ready",
            )

        if self.status != "running":
            return False

        host_mode = self._container.attrs["HostConfig"]["NetworkMode"]
        if host_mode != "host":
            networks = self._container.attrs["NetworkSettings"]["Networks"]
            for name, network in networks.items():
                if not network["IPAddress"]:
                    return False

        if host_mode != "host":
            # If a user has exposed a port then wait for LISTEN socket to show up in netstat
            ports = self._container.attrs["NetworkSettings"]["Ports"]
        else:
            ports = self._container.attrs["Config"]["ExposedPorts"]
            if not ports:
                return True

        for port, listeners in ports.items():
            if not listeners and host_mode != "host":
                continue

            port, proto = port.split("/")

            assert proto in ("tcp", "udp")

            if proto == "tcp" and port not in self.get_open_tcp_ports():
                return False

            if proto == "udp" and port not in self.get_open_udp_ports():
                return False

        return True
