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

## IRC Server for iOS

This repo includes a lightweight IRC server you can run locally and connect to from an iOS device on the same Wi‑Fi network.

### Start the server

```bash
$ pipenv run python irc_server.py
```

Optional flags:

```bash
$ pipenv run python irc_server.py --port 6667 --verbose
```

When the server starts, it prints your LAN IP address. Use that IP from your iPhone or iPad.

### Connect from iOS

1. Install an IRC client such as [LimeChat](https://limechat.net/), [Palaver](https://palaverapp.com/), or Colloquy.
2. Add a new server with these settings:
   - **Server / Host:** your computer's LAN IP (shown when the server starts)
   - **Port:** `6667`
   - **SSL / TLS:** off (this test server does not use TLS)
   - **Nickname:** any name you like
3. Join a channel, for example `#general`.
4. Chat with other clients connected to the same server.

### Notes

- The server binds to `0.0.0.0` so iOS devices on your local network can reach it.
- This is intended for local testing, not production use.
- If connection fails, confirm your Mac or Linux firewall allows inbound TCP on port `6667`.

