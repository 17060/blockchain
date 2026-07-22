import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

from astrology import build_chart
from astroeconomics import daily_market_pulse, personal_briefing, sign_market_profile

BASE_DIR = Path(__file__).resolve().parent


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')


    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def new_chart_transaction(self, owner, birth_date):
        """
        Register a birth chart on the blockchain.

        :param owner: Address of the chart owner
        :param birth_date: Birth date in YYYY-MM-DD format
        :return: The index of the Block that will hold this transaction
        """
        chart = build_chart(birth_date)
        self.current_transactions.append({
            'sender': owner,
            'recipient': 'astrology-registry',
            'amount': 0,
            'transaction_type': 'birth_chart',
            'birth_date': chart['birth_date'],
            'sun_sign': chart['sun_sign'],
            'element': chart['element'],
            'modality': chart['modality'],
            'ruler': chart['ruler'],
            'glyph': chart['glyph'],
        })

        return self.last_block['index'] + 1

    def get_charts(self):
        """Return all birth chart transactions recorded on the chain."""
        charts = []
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction.get('transaction_type') == 'birth_chart':
                    charts.append(transaction)
        return charts

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.

        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)
try:
    app.json.ensure_ascii = False
except Exception:
    app.config['JSON_AS_ASCII'] = False

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


def mine_pending_block():
    """Run proof-of-work and seal current transactions into a new block."""
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
    )
    return blockchain.new_block(proof, blockchain.hash(last_block))


@app.route('/mine', methods=['GET'])
def mine():
    block = mine_pending_block()

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json(silent=True) or {}

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return jsonify({'error': 'sender, recipient, and amount are required'}), 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json(silent=True) or {}

    nodes = values.get('nodes')
    if nodes is None:
        return jsonify({'error': 'Please supply a valid list of nodes'}), 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'AstroEconomics',
        'charts': len(blockchain.get_charts()),
        'blocks': len(blockchain.chain),
    }), 200


@app.route('/')
def home():
    """Serve the AstroEconomics web app with server-rendered content."""
    css = (BASE_DIR / 'static' / 'app.css').read_text(encoding='utf-8')
    js = (BASE_DIR / 'static' / 'app.js').read_text(encoding='utf-8')
    try:
        pulse = daily_market_pulse()
    except Exception:
        pulse = None
    return render_template(
        'index.html',
        css=css,
        js=js,
        pulse=pulse,
        charts=blockchain.get_charts(),
    )


@app.route('/astrology/sign', methods=['GET'])
def astrology_sign():
    birth_date = request.args.get('birth_date')
    if not birth_date:
        return jsonify({'error': 'birth_date query parameter is required (YYYY-MM-DD)'}), 400

    try:
        chart = build_chart(birth_date)
        profile = sign_market_profile(chart['sun_sign'])
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    response = dict(chart)
    response['sectors'] = profile['sectors']
    response['bias'] = profile['bias']
    response['assets'] = profile['assets']
    return jsonify(response), 200


@app.route('/astrology/charts', methods=['GET'])
def astrology_charts():
    return jsonify({'charts': blockchain.get_charts()}), 200


@app.route('/astrology/charts', methods=['POST'])
def register_chart():
    values = request.get_json(silent=True) or {}

    required = ['owner', 'birth_date']
    if not all(k in values for k in required):
        return jsonify({'error': 'owner and birth_date are required'}), 400

    try:
        blockchain.new_chart_transaction(values['owner'], values['birth_date'])
        chart = build_chart(values['birth_date'])
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    # Persist the chart immediately so the app feels correct without a
    # separate mine step. Mining still works for classic blockchain demos.
    block = mine_pending_block()

    response = {
        'message': 'Birth chart registered and mined into block {0}'.format(block['index']),
        'chart': chart,
        'block_index': block['index'],
    }
    return jsonify(response), 201


@app.route('/astroeconomics/pulse', methods=['GET'])
def astroeconomics_pulse():
    """Daily sky + market pulse for the home screen."""
    on_date = request.args.get('date')
    try:
        pulse = daily_market_pulse(on_date)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify(pulse), 200


@app.route('/astroeconomics/briefing', methods=['GET', 'POST'])
def astroeconomics_briefing():
    """Personalized astrology + market briefing for a birth date."""
    if request.method == 'POST':
        values = request.get_json(silent=True) or {}
        birth_date = values.get('birth_date')
        on_date = values.get('date')
        owner = values.get('owner')
        persist = bool(values.get('register'))
    else:
        birth_date = request.args.get('birth_date')
        on_date = request.args.get('date')
        owner = request.args.get('owner')
        persist = request.args.get('register') in ('1', 'true', 'yes')

    if not birth_date:
        return jsonify({'error': 'birth_date is required (YYYY-MM-DD)'}), 400

    try:
        briefing = personal_briefing(birth_date, on_date=on_date, owner=owner)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    if persist:
        owner_name = owner or 'anonymous'
        index = blockchain.new_chart_transaction(owner_name, birth_date)
        block = mine_pending_block()
        briefing['registered'] = True
        briefing['block_index'] = block['index']
        briefing['message'] = 'Chart queued at index {0} and mined into block {1}'.format(
            index, block['index']
        )
    else:
        briefing['registered'] = False

    return jsonify(briefing), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, threaded=True)

