#!/usr/bin/python
# coding: utf8
import os
import json
import re
import subprocess


def override(path, text):
    if not os.path.exists(path) and os.path.exists(path+"_temp"):
        os.rename(path+"_temp",path)
    fw = open(path+"_temp", 'wb')
    fw.write(text)
    fw.close()
    if os.path.exists(path):
        os.remove(path)
    os.rename(path+"_temp", path)


def read(path):
    try:
        fr = open(path, "rb")
    except IOError:
        print "The file don't exist, Please double check!"
        return
    lines = fr.readlines()
    ret = ''
    for line in lines:
        ret += line
    return ret


def read_jsonfile(path):
    return json.loads(read(path))


def cmd(command):
    return os.popen(command).read()


def get_name(container):
    return cmd("docker inspect -f '{{.Name}}' " + container).replace("/", "").replace('\n', '')


def get_ip(container):
    return cmd("docker inspect -f '{{.NetworkSettings.IPAddress}}' " + container).replace('\n', '')


def get_port(container):
    return cmd("docker inspect -f '{{.Config.ExposedPorts}}' " + container).replace('/tcp:{}]', '').replace('map[', '').replace('\n', '')


def get_info(container):
    filename = "/var/lib/docker/containers/" + container + "/config.v2.json"
    config = read_jsonfile(filename)

    name = config['Name'].replace("/", "")
    port = config['Config']['ExposedPorts'].keys()[0].replace('/tcp', '')
    ip = cmd("docker inspect -f '{{.NetworkSettings.IPAddress}}' " + name)
    # ip = config['NetworkSettings']['Networks']['bridge']['IPAddress']

    ret = {'name': name, 'port': port, 'ip': ip}
    return ret


tpl = """
    server {
        listen 80;
        server_name $name.zhgtrade.com;
        location / {
	        proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header Host $http_host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_pass http://$ip:$port;
        }
        #location /static {
        #    root /mnt/build/zhgtrade-parent/zhgtrade-newfront/src/main/webapp;
        #}
    }
"""


def generate_conf():
    print "generate_conf"
    out = cmd("docker ps | grep -v CONTAINER | awk '{print $1}'")
    containers = out.split("\n")
    servers = ''
    hosts = ''
    for con in containers:
        if con != '':
            name = get_name(con)
            ip = get_ip(con)
            port = get_port(con)
            print ip, port
            if len(port) >= 2:
                servers += tpl.replace("$name", name).replace("$ip", ip).replace("$port", port)
                hosts += "114.215.222.190 " + name + ".zhgtrade.com\n"
    override('/usr/local/openresty/nginx/conf/vhost.conf', servers)
    override('/usr/local/openresty/nginx/html/vhost.html', "<pre>" + hosts + "</pre>")


def reload_nginx():
    print "reload nginx"
    cmd('nginx -s reload')


def auto_reload():
    generate_conf()
    reload_nginx()

print " ==================== docker events ==================== "

# auto_reload()

proc = subprocess.Popen(["docker", "events"],
                        # shell=True,   # windows: true, linux: false
                        stdout=subprocess.PIPE)

auto_reload()

while 1:
    out = proc.stdout.readline()
    event = re.sub('\(|\)', "", out).split(" ")
    if out.find('container stop') != -1:
        auto_reload()
        print ' container stop '
        # print get_info(event[3])
    elif out.find('container start') != -1:
        auto_reload()
        print ' start container '
        # print get_info(event[3])
    if out == '':
        print "out "
        break

# nohup /mnt/deploy/docker-manager.py > /dev/null 2>&1 &
