# CCDC Scoring Engine

This is the [CCDC](http://nationalccdc.org) Scoring Engine used for the DSU Defensive Security Club's Mock Competitions.

## Getting Started

### Demos

Download a demo Scoring Engine VM and Test VM [here](https://drive.google.com/drive/folders/14993t1caA-poFq6SQS95CNCJokF4ll4b?usp=sharing).

### Installation Setup
1. Clone the repo: `git clone https://github.com/DSU-DefSec/ScoringEngine.git`.

2. Enter the install directory `cd install/`.

3. Install dependencies and set up the services: `./install.sh`.

4. If using the IALab API (DSU only), update `etc/vcloud.token` with the appropriate token value.

5. Write the configuration file, and load it into the database (see below).

6. When you want to begin scoring, start the services with `systemctl start scoring_engine scoring_web`.

## Information

#### Logical Architecture

![Logical Architecture of Scoring Engine](docs/imgs/arch.png)

#### Main Page of Scoring Engine

![Screenshot of Default Page](docs/imgs/mainscreen.png)

This project is composed of a few important parts.

```
├── docs # Documentation
├── install # Various files for installing the ScoringEngine
├── LICENSE
├── README.md
├── checkfiles # Contains temporary files created in checks
    └── ...
├── configs # Contains example configurations. Write yours in here.
    └── ...
├── model.py # class that lays out "Model" object. Stores all data and manages db
├── db.py # Contains functions for MySQL database access
├── db_writer.py # Contains specialized functions for writing scoring data to database
├── engine
    ├── polling # Contains poller files, which interact with system services
    ├── checker # Contains check files. Checks take poll results and return true or false
    └── ...
├── etc # Contains files needed to run scoring engine services (pid and conf files)
    └── ...
├── load_config.py # Loads a given config, deletes database beforehand
├── engine_manager.py # Starts and stop the ScoringEngine
├── vcloud.py # Orchestrates ialab integration (DSU specific)
├── utils.py # Loads a given module by string.
├── web # Contains flask files to create and run web server
    └── ...
└── wsgi.py # Runs wsgi web server (flask)
├── scripts # Contains various scripts not needed for scoring engine
```

## Configuration

Load a config with `./scoring/load_config.py [CONFIG_FILE]`. This will wipe the previous database.

### Config file format

The Scoring Engine is configured using a `yaml` config file. A few sample configs can be found in `configs/`. A basic configuration might look like:

```
settings:
    running: 1
    revert_penalty: 350
    webserver_ip: 10.1.0.5
    polling:
        interval: 150
        jitter: 30
        timeout: 20
    pcr:
        service_interval: 0
        service_jitter: 0

web_admins:
    admin: adminPassword # Password for web interface

teams:
    Team1: # Team number and password. Can add multiple teams. Number is used to determine subnet.
        team_num: 1
        user:
            username: team1
            password: FalseThreat # Team password for web interface

vapps:
    vapp_name1: # Name of vApp (or local machines)
        subnet: "10.20.{}.0"
        netmask: 255.255.255.0
        systems:
            DC01: # System name (can add multiple systems)
                host: 10 # Last octet of IP address
                checks:
                    DC01-ldap:
                        type: ldap
                        port: 389
                        checker: match_ldap_output # Poller
                        ios:
                            dc01-ldap:
                                input:
                                    base: cn=Users,dc=DOMAIN,dc=NET
                                    filter: (sAMAccountName=user.name)
                                    attributes: [objectGUID]
                                output:
                                    objectGUID: [mKE1LEJ7jESXEyETKW8Zww==]

credentials:
    default_password: Password1!
    local:
        celeste.nichols:
            ios: ['files-ssh']
        monique.reynolds:
            ios: ['files-ssh']

    domain:
        DOMAIN.NET:
            myra.gardner:
                ios: ['dc01-ldap']
            joel.boone:
                ios: ['dc01-ldap']
           
```
