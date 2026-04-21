from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
import pox.lib.packet as pkt

log = core.getLogger()

WHITELIST = ["10.0.0.1", "10.0.0.2"]  # h1 and h2

class AccessControl(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        log.info("Access Control System Started")

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        # Always allow ARP so hosts can find each other
        if packet.type == pkt.ethernet.ARP_TYPE:
            self.flood(event)
            return

        # Check IPv4 packets
        ip = packet.find('ipv4')
        if ip:
            src_ip = str(ip.srcip)
            if src_ip in WHITELIST:
                log.info("ALLOWED: %s", src_ip)
                self.flood(event)
            else:
                log.info("BLOCKED: %s", src_ip)
                self.drop(event)
        else:
            self.flood(event)

    def flood(self, event):
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        self.connection.send(msg)

    def drop(self, event):
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        self.connection.send(msg)

    def _handle_ConnectionUp(self, event):
        log.info("Switch connected: %s", dpid_to_str(event.dpid))

def launch():
    core.openflow.addListenerByName(
        "ConnectionUp",
        lambda event: AccessControl(event.connection)
    )
    log.info("SDN Access Control System Running")
