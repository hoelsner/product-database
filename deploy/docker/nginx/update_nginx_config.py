"""
small script that creates a nginx configuration with all reachable web container
"""
import os
import socket


if __name__ == "__main__":
    # try to resolve valid hostname for the web service
    entry_counter = 2
    hostname_prefix = os.environ.get("INSTANCE_NAME") + "_" if os.environ.get("INSTANCE_NAME", None) else ""
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
