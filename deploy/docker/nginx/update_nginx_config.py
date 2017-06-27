"""
small script that creates a nginx configuration with all reachable web container
"""
import os
import socket
from docker import Client


if __name__ == "__main__":
    # try to resolve valid hostname for the web service
    entry_counter = 2

    if os.environ.get("INSTANCE_NAME", None):
        container_prefix = os.environ.get("INSTANCE_NAME", "production")

    else:
        # try to get the container name from the docker file
        cli = Client(base_url='unix://var/run/docker.sock')
        container_prefix = None
        for c in cli.containers():
            if c["Id"].startswith(socket.gethostname()):
                container_prefix = c["Names"][-1].split("_", 1)[0].lstrip("/")
                break

    hostname_prefix = container_prefix + "_" if container_prefix else ""

    hosts = ["%sweb_1" % hostname_prefix]
    while True:
        try:
            hostname = "%sweb_%d" % (hostname_prefix, entry_counter)
            socket.gethostbyname_ex(hostname)
            hosts.append(hostname)
            entry_counter += 1

        except:
            # host not found, that's it
            break

    with open(os.path.join("/etc/nginx/template/default.template.conf")) as f:
        content = f.read()

    server_list = "\n".join(["\tserver %s:8000 max_fails=5 fail_timeout=15s;" % host for host in hosts])

    content = """\
upstream webapp {
    least_conn;
%s
}

%s""" % (server_list, content)

    with open("/etc/nginx/conf.d/default.conf", "w+") as f:
        f.write(content)
