# Are you looking for the source code for my book?

Please find it here: https://github.com/dvf/blockchain-book

The book is available on Amazon: https://www.amazon.com/Learn-Blockchain-Building-Understanding-Cryptocurrencies/dp/1484251709

# Learn Blockchains by Building One

[![Build Status](https://travis-ci.org/dvf/blockchain.svg?branch=master)](https://travis-ci.org/dvf/blockchain)

This is the source code for my post on [Building a Blockchain](https://medium.com/p/117428612f46). 

## Installation

1. Make sure [Python 3.6+](https://www.python.org/downloads/) is installed. 
2. Install [pipenv](https://github.com/kennethreitz/pipenv). 

```
$ pip install pipenv 
```
3. Install requirements  
```
$ pipenv install 
``` 

4. Run the server:
    * `$ pipenv run python blockchain.py` 
    * `$ pipenv run python blockchain.py -p 5001`
    * `$ pipenv run python blockchain.py --port 5002`

## IRC Hive Mind

The IRC Hive Mind is a collective interface to a blockchain node. Everyone in an IRC channel shares the same view of the chain and can mine blocks, send transactions, link peer nodes, and run consensus together.

1. Start a blockchain node (in one terminal):

```
$ pipenv run python blockchain.py
```

2. Start the hive mind bridge (in another terminal):

```
$ pipenv run python irc_hivemind.py --ssl --channel '#your-channel' --nick YourBotName
```

3. Join the channel and try hive commands:

| Command | Description |
| --- | --- |
| `!help` | List available commands |
| `!status` | Show current chain length |
| `!mine` | Forge a new block |
| `!chain [n]` | Show the last _n_ blocks (default 3) |
| `!tx <recipient> <amount>` | Queue a transaction (sender is your IRC nick) |
| `!peer <http://host:port>` | Register a peer node |
| `!sync` | Run consensus with linked peers |

Point multiple blockchain nodes at each other with `!peer`, then run `!sync` to let the hive agree on the longest valid chain.

## Docker

Another option for running this blockchain program is to use Docker.  Follow the instructions below to create a local Docker container:

1. Clone this repository
2. Build the docker container

```
$ docker build -t blockchain .
```

3. Run the container

```
$ docker run --rm -p 80:5000 blockchain
```

4. To add more instances, vary the public port number before the colon:

```
$ docker run --rm -p 81:5000 blockchain
$ docker run --rm -p 82:5000 blockchain
$ docker run --rm -p 83:5000 blockchain
```

## Installation (C# Implementation)

1. Install a free copy of Visual Studio IDE (Community Edition):
https://www.visualstudio.com/vs/

2. Once installed, open the solution file (BlockChain.sln) using the File > Open > Project/Solution menu options within Visual Studio.

3. From within the "Solution Explorer", right click the BlockChain.Console project and select the "Set As Startup Project" option.

4. Click the "Start" button, or hit F5 to run. The program executes in a console window, and is controlled via HTTP with the same commands as the Python version.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

