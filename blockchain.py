import hashlib
import json
import threading
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

from astrology import build_chart
from astroeconomics import daily_market_pulse, personal_briefing, sign_market_profile
from ui import render_app


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
        if not isinstance(address, str) or not address.strip():
            raise ValueError('Invalid URL')

        candidate = address.strip()
        if '://' not in candidate:
            candidate = 'http://{0}'.format(candidate)

        parsed_url = urlparse(candidate)
        # Require host[:port] only — reject path-bearing or scheme-broken values.
        if not parsed_url.netloc or parsed_url.path not in ('', '/'):
            raise ValueError('Invalid URL')

        self.nodes.add(parsed_url.netloc)


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

        neighbours = list(self.nodes)
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            try:
                response = requests.get(
                    'http://{0}/chain'.format(node),
                    timeout=3,
                )
            except requests.RequestException:
                continue

            if response.status_code == 200:
                payload = response.json()
                length = payload['length']
                chain = payload['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            self.current_transactions = []
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

    def reset(self):
        """Reset chain state (used by tests)."""
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.new_block(previous_hash='1', proof=100)

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
_chain_lock = threading.Lock()


def mine_pending_block():
    """Run proof-of-work and seal current transactions into a new block."""
    with _chain_lock:
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block)
        blockchain.new_transaction(
            sender='0',
            recipient=node_identifier,
            amount=1,
        )
        return blockchain.new_block(proof, blockchain.hash(last_block))


def register_and_mine_chart(owner, birth_date):
    """Validate, append a birth chart, and mine it atomically."""
    chart = build_chart(birth_date)
    with _chain_lock:
        blockchain.current_transactions.append({
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
        index = blockchain.last_block['index'] + 1
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block)
        blockchain.new_transaction(
            sender='0',
            recipient=node_identifier,
            amount=1,
        )
        block = blockchain.new_block(proof, blockchain.hash(last_block))
        return index, block, chart


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

    amount = values['amount']
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        return jsonify({'error': 'amount must be a number'}), 400

    with _chain_lock:
        index = blockchain.new_transaction(
            values['sender'], values['recipient'], amount
        )

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
    if not isinstance(nodes, list) or not nodes:
        return jsonify({'error': 'Please supply a valid list of nodes'}), 400

    try:
        with _chain_lock:
            for node in nodes:
                blockchain.register_node(node)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    with _chain_lock:
        replaced = blockchain.resolve_conflicts()
        chain = list(blockchain.chain)

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': chain,
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': chain,
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


def _page(pulse=None, charts=None, briefing=None, error=None, form=None, status=200):
    html = render_app(
        pulse=pulse,
        charts=charts if charts is not None else blockchain.get_charts(),
        briefing=briefing,
        error=error,
        form=form,
    )
    return html, status, {'Content-Type': 'text/html; charset=utf-8'}


@app.errorhandler(404)
def not_found(_error):
    try:
        pulse = daily_market_pulse()
    except Exception:
        pulse = None
    return _page(
        pulse=pulse,
        error='Page not found. Use the home form below, or open /health for API status.',
        status=404,
    )


@app.route('/', methods=['GET', 'POST'])
def home():
    """Serve a plain HTML app. Works with no JavaScript."""
    error = None
    briefing = None
    form = {
        'owner': '',
        'birth_date': '',
        'register': True,
    }

    if request.method == 'POST':
        form['owner'] = (request.form.get('owner') or '').strip()
        form['birth_date'] = (request.form.get('birth_date') or '').strip()
        form['register'] = request.form.get('register') in ('1', 'on', 'true', 'yes')
        if not form['birth_date']:
            error = 'Birth date is required (YYYY-MM-DD).'
        else:
            try:
                briefing = personal_briefing(
                    form['birth_date'],
                    owner=form['owner'] or 'anonymous',
                )
                if form['register']:
                    owner_name = form['owner'] or 'anonymous'
                    _index, block, _chart = register_and_mine_chart(
                        owner_name, form['birth_date']
                    )
                    briefing['registered'] = True
                    briefing['block_index'] = block['index']
                else:
                    briefing['registered'] = False
            except ValueError as exc:
                error = str(exc)

    try:
        pulse = daily_market_pulse()
    except Exception:
        pulse = None

    return _page(pulse=pulse, briefing=briefing, error=error, form=form)


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
        _index, block, chart = register_and_mine_chart(
            values['owner'], values['birth_date']
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

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
        try:
            index, block, _chart = register_and_mine_chart(owner_name, birth_date)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
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

    print('AstroEconomics ready at http://127.0.0.1:{0}/'.format(port))
    print('In Cursor: open Ports panel -> port {0} -> Open in Browser'.format(port))
    app.run(host='0.0.0.0', port=port, threaded=True)

