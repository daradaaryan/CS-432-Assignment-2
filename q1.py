#!/usr/bin/env python

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import Node
from mininet.topo import Topo
from mininet.node import OVSController
from mininet.log import info

class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    # pylint: disable=arguments-differ
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class NetworkTopo(Topo):
    "A Router connecting three IP subnets"

    def build(self, **_opts):
        defaultIP1 = '10.0.0.254/24'
        defaultIP2 = '10.1.0.253/24'
        defaultIP3 = '10.2.0.254/24'

        ra = self.addHost('ra', cls=LinuxRouter, ip=defaultIP1)
        rb = self.addHost('rb', cls=LinuxRouter, ip=defaultIP2)
        rc = self.addHost('rc', cls=LinuxRouter, ip=defaultIP3)

        s1, s2, s3 = [self.addSwitch(s) for s in ('s1', 's2', 's3')]

       
        self.addLink(s1, ra, intfName2='r1-s1', params2={'ip': '10.0.0.254/24'})
        self.addLink(s2, rb, intfName2='r2-s2', params2={'ip': '10.1.0.253/24'})
        self.addLink(s3, rc, intfName2='r3-s3', params2={'ip': '10.2.0.254/24'})
        
        hosts_data = [
            {'name': 'h1', 'ip': '10.0.0.1/24', 'defaultRoute': 'via 10.0.0.254'},
            {'name': 'h2', 'ip': '10.0.0.2/24', 'defaultRoute': 'via 10.0.0.254'},
            {'name': 'h3', 'ip': '10.1.0.1/24', 'defaultRoute': 'via 10.1.0.254'},
            {'name': 'h4', 'ip': '10.1.0.2/24', 'defaultRoute': 'via 10.1.0.254'},
            {'name': 'h5', 'ip': '10.2.0.1/24', 'defaultRoute': 'via 10.2.0.254'},
            {'name': 'h6', 'ip': '10.2.0.2/24', 'defaultRoute': 'via 10.2.0.254'},
        ]

        for host_data in hosts_data:
            host = self.addHost(host_data['name'], ip=host_data['ip'], defaultRoute=host_data['defaultRoute'])
            self.addLink(host, s1 if '1' in host_data['name'] else (s2 if '3' in host_data['name'] else s3))

        self.addLink(ra, rb, intfName1='l1', intfName='m2', params1={'ip': '1.0.0.1/24'}, params2={'ip': '1.0.0.2/24'})
        self.addLink(rb, rc, intfName1='m1', intfName='n2', params1={'ip': '1.0.1.1/24'}, params2={'ip': '1.0.1.2/24'})
        self.addLink(rc, ra, intfName1='n1', intfName='l2', params1={'ip': '1.0.2.1/24'}, params2={'ip': '1.0.2.2/24'})

def run():
    "Test router"
    topo = NetworkTopo()
    net = Mininet(topo=topo, controller=None)
    net['ra'].cmd('ip route add 10.0.0.254/24 via 10.1.0.253')  # r1-r2
    net['ra'].cmd('ip route add 10.0.0.254/24 via 10.2.0.254')  # r1-r3

    net['rb'].cmd('ip route add 10.1.0.253/24 via 10.0.0.254')
    net['rb'].cmd('ip route add 10.1.0.253/24 via 10.2.0.254')

    net['rc'].cmd('ip route add 10.2.0.254/24 via 10.0.0.254')
    net['rc'].cmd('ip route add 10.2.0.254/24 via 10.1.0.253')

    net.start()
    info('*** Routing Table on Routers:\n')
    info(net['ra'].cmd('route'))
    info(net['rb'].cmd('route'))
    info(net['rc'].cmd('route'))
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()