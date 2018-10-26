# CCDC Scoring Engine
This is the [CCDC](http://nationalccdc.org) Scoring Engine used for DSU Defensive Security Club Mock Competitions.

## Architecture

### Logical Architecture

![](docs/imgs/arch.png)

## Installation & Setup

The poller modules and web server require a number of dependencies.

Install dependencies: `./install.sh`

Edit `db.py` and replace the MySQL credentials with your own.

Setup database: `./setup.py`

## Configuration

The Scoring Engine is configured using a flat config file. A few sample configs can be found in `configs/`.

### Config File Format

The config file consists of a few `.ini`-like sections. The `Global` section holds all of the options related to polling and scoring. Each of the subsequent sections describe different parts of the expected environment like `Teams`, `Services`, and `Credentials`. Each line in a section must start with an ID for the object it is describing which is used to reference it by other parts of the config. Requirements for each section are described in a comment under the section header.

Ex:
```
[Services]
# id:host,port
# 1:8,53
```

### Loading the Config

Load the config: `./load_config.py [CONFIG_FILE]`

## Using the Engine

The scoring engine can be run on a single system, or it can be split between systems -- one team per system.

Single system: `./engine.py`

Multiple systems: `./engine.py [TEAM_NUM]`

## Running the webserver

Start the webserver: `./start_server`
