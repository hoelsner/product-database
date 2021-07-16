"""
small script that creates a nginx configuration with all reachable web container for the product database
"""
import os
from docker import Client


if __name__ == "__main__":
    cli = Client(base_url='unix://var/run/docker.sock')
    hosts = []
    for c in cli.containers(filters={"label": "productdb=web"}):
        # get a valid hostname for the nginx configuration, reachability on the same network is expected
        hosts.append(c["Names"][-1].lstrip("/"))

    with open(os.path.join("/etc/nginx/template/default.template.conf")) as f:
        content = f.read()

    server_list = "\n".join(["\tserver %s:8443 max_fails=5 fail_timeout=15s;" % host for host in hosts])

    content = """\
upstream webapp {
    least_conn;
%s
}

%s""" % (server_list, content)

    with open("/etc/nginx/conf.d/default.conf", "w+") as f:
        f.write(content)
