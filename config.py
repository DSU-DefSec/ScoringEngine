from polling.dns_poll import DnsPoller, DnsPollInput


def load_config():
    poll_input = DnsPollInput('A','reddit.com','8.8.8.8')
