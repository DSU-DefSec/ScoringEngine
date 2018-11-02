#!/usr/bin/python3
import random

def get_creds(num_creds, users, services):
    creds = {}
    for service in services:
        used = []
        for i in range(num_creds):
            user = random.choice(users)
            while user in used:
                user = random.choice(users)
            used.append(user)
            if not user in creds:
                creds[user] = []
            creds[user].append(service)
    return creds


if __name__ == '__main__':
    with open('users.txt', 'r') as f:
        users = [line.strip() for line in f.readlines()]
    local_services = ['lab01-ssh', 'lab02-ftp', 'lab02-ssh', 'mail-imap']
    domain_services = {
            'GOATS.LAN': ['dc01-ldap', 'dc02-ldap', 'share-smb', 'win7-rdp'],
    }
    num_creds = 25

    creds = get_creds(num_creds, users, local_services)
    print(' '*4 + 'local:')
    for user,services in creds.items():
        print(' '*8 + '{}:'.format(user))
        print(' '*12 + 'ios: {}'.format(services))

    print(' '*4 + 'domain:')
    for domain, dservices in domain_services.items():
        creds = get_creds(num_creds, users, dservices)
        print(' '*8 + '{}:'.format(domain))
        for user,services in creds.items():
            print(' '*12 + '{}:'.format(user))
            print(' '*16 + 'ios: {}'.format(services))
