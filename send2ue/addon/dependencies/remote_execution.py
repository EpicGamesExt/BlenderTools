# Copyright Epic Games, Inc. All Rights Reserved.

import sys as _sys
import json as _json
import uuid as _uuid
import time as _time
import socket as _socket
import logging as _logging
import threading as _threading


def hello():
    _logging.debug("Hello from remote")


# Protocol constants (see PythonScriptRemoteExecution.cpp for the full protocol definition)
_PROTOCOL_VERSION = 1  # Protocol version number
_PROTOCOL_MAGIC = 'ue_py'  # Protocol magic identifier
_TYPE_PING = 'ping'  # Service discovery request (UDP)
_TYPE_PONG = 'pong'  # Service discovery response (UDP)
_TYPE_OPEN_CONNECTION = 'open_connection'  # Open a TCP command connection with the requested server (UDP)
_TYPE_CLOSE_CONNECTION = 'close_connection'  # Close any active TCP command connection (UDP)
_TYPE_COMMAND = 'command'  # Execute a remote Python command (TCP)
_TYPE_COMMAND_RESULT = 'command_result'  # Result of executing a remote Python command (TCP)

_NODE_PING_SECONDS = 1  # Number of seconds to wait before sending another "ping" message to discover remote notes
_NODE_TIMEOUT_SECONDS = 5  # Number of seconds to wait before timing out a remote node that was discovered via UDP and has stopped sending "pong" responses

DEFAULT_MULTICAST_TTL = 0  # Multicast TTL (0 is limited to the local host, 1 is limited to the local subnet)
DEFAULT_MULTICAST_GROUP_ENDPOINT = ('239.0.0.1',
                                    6766)  # The multicast group endpoint tuple that the UDP multicast socket should join (must match the "Multicast Group Endpoint" setting in the Python plugin)
DEFAULT_MULTICAST_BIND_ADDRESS = '0.0.0.0'  # The adapter address that the UDP multicast socket should bind to, or 0.0.0.0 to bind to all adapters (must match the "Multicast Bind Address" setting in the Python plugin)
DEFAULT_COMMAND_ENDPOINT = ('127.0.0.1',
                            6776)  # The endpoint tuple for the TCP command connection hosted by this client (that the remote client will connect to)

# Execution modes (these must match the names given to LexToString for EPythonCommandExecutionMode in IPythonScriptPlugin.h)
MODE_EXEC_FILE = 'ExecuteFile'  # Execute the Python command as a file. This allows you to execute either a literal Python script containing multiple statements, or a file with optional arguments
MODE_EXEC_STATEMENT = 'ExecuteStatement'  # Execute the Python command as a single statement. This will execute a single statement and print the result. This mode cannot run files
MODE_EVAL_STATEMENT = 'EvaluateStatement'  # Evaluate the Python command as a single statement. This will evaluate a single statement and return the result. This mode cannot run files


class RemoteExecutionConfig(object):
    '''
    Configuration data for establishing a remote connection with a UE4 instance running Python.
    '''

    def __init__(self):
        self.multicast_ttl = DEFAULT_MULTICAST_TTL
        self.multicast_group_endpoint = DEFAULT_MULTICAST_GROUP_ENDPOINT
        self.multicast_bind_address = DEFAULT_MULTICAST_BIND_ADDRESS
        self.command_endpoint = DEFAULT_COMMAND_ENDPOINT


class RemoteExecution(object):
    '''
    A remote execution session. This class can discover remote "nodes" (UE4 instances running Python), and allow you to open a command channel to a particular instance.

    Args:
        config (RemoteExecutionConfig): Configuration controlling the connection settings for this session.
    '''

    def __init__(self, config=RemoteExecutionConfig()):
        self._config = config
        self._broadcast_connection = None
        self._command_connection = None
        self._node_id = str(_uuid.uuid4())

    @property
    def remote_nodes(self):
        '''
        Get the current set of discovered remote "nodes" (UE4 instances running Python).

        Returns:
            list: A list of dicts containg the node ID and the other data.
        '''
        return self._broadcast_connection.remote_nodes if self._broadcast_connection else []

    def start(self):
        '''
        Start the remote execution session. This will begin the discovey process for remote "nodes" (UE4 instances running Python).
        '''
        self._broadcast_connection = _RemoteExecutionBroadcastConnection(self._config, self._node_id)
        self._broadcast_connection.open()

    def stop(self):
        '''
        Stop the remote execution session. This will end the discovey process for remote "nodes" (UE4 instances running Python), and close any open command connection.
        '''
        self.close_command_connection()
        if self._broadcast_connection:
            self._broadcast_connection.close()
            self._broadcast_connection = None

    def has_command_connection(self):
        '''
        Check whether the remote execution session has an active command connection.

        Returns:
            bool: True if the remote execution session has an active command connection, False otherwise.
        '''
        return self._command_connection is not None

    def open_command_connection(self, remote_node_id):
        '''
        Open a command connection to the given remote "node" (a UE4 instance running Python), closing any command connection that may currently be open.

        Args:
            remote_node_id (string): The ID of the remote node (this can be obtained by querying `remote_nodes`).
        '''
        self._command_connection = _RemoteExecutionCommandConnection(self._config, self._node_id, remote_node_id)
        self._command_connection.open(self._broadcast_connection)

    def close_command_connection(self):
        '''
        Close any command connection that may currently be open.
        '''
        if self._command_connection:
            self._command_connection.close(self._broadcast_connection)
            self._command_connection = None

    def run_command(self, command, unattended=True, exec_mode=MODE_EXEC_FILE, raise_on_failure=False):
        '''
        Run a command remotely based on the current command connection.

        Args:
            command (string): The Python command to run remotely.
            unattended (bool): True to run this command in "unattended" mode (suppressing some UI).
            exec_mode (string): The execution mode to use as a string value (must be one of MODE_EXEC_FILE, MODE_EXEC_STATEMENT, or MODE_EVAL_STATEMENT).
            raise_on_failure (bool): True to raise a RuntimeError if the command fails on the remote target.

        Returns:
            dict: The result from running the remote command (see `command_result` from the protocol definition).
        '''
        data = self._command_connection.run_command(command, unattended, exec_mode)
        if raise_on_failure and not data['success']:
            raise RuntimeError('Remote Python Command failed! {0}'.format(data['result']))
        return data


class _RemoteExecutionNode(object):
    '''
    A discovered remote "node" (aka, a UE4 instance running Python).

    Args:
        data (dict): The data representing this node (from its "pong" reponse).
        now (float): The timestamp at which this node was last seen.
    '''

    def __init__(self, data, now=None):
        self.data = data
        self._last_pong = _time_now(now)

    def should_timeout(self, now=None):
        '''
        Check to see whether this remote node should be considered timed-out.

        Args:
            now (float): The current timestamp.

        Returns:
            bool: True of the node has exceeded the timeout limit (`_NODE_TIMEOUT_SECONDS`), False otherwise.
        '''
        return (self._last_pong + _NODE_TIMEOUT_SECONDS) < _time_now(now)


class _RemoteExecutionBroadcastNodes(object):
    '''
    A thread-safe set of remote execution "nodes" (UE4 instances running Python).
    '''

    def __init__(self):
        self._remote_nodes = {}
        self._remote_nodes_lock = _threading.RLock()

    @property
    def remote_nodes(self):
        '''
        Get the current set of discovered remote "nodes" (UE4 instances running Python).

        Returns:
            list: A list of dicts containg the node ID and the other data.
        '''
        with self._remote_nodes_lock:
            remote_nodes_list = []
            for node_id, node in self._remote_nodes.items():
                remote_node_data = dict(node.data)
                remote_node_data['node_id'] = node_id
                remote_nodes_list.append(remote_node_data)
            return remote_nodes_list

    def update_remote_node(self, node_id, node_data, now=None):
        '''
        Update a remote node, replacing any existing data.

        Args:
            node_id (str): The ID of the remote node (from its "pong" reponse).
            node_data (dict): The data representing this node (from its "pong" reponse).
            now (float): The timestamp at which this node was last seen.
        '''
        now = _time_now(now)
        with self._remote_nodes_lock:
            if node_id not in self._remote_nodes:
                _logger.debug('Found Node {0}: {1}'.format(node_id, node_data))
            self._remote_nodes[node_id] = _RemoteExecutionNode(node_data, now)

    def timeout_remote_nodes(self, now=None):
        '''
        Check to see whether any remote nodes should be considered timed-out, and if so, remove them from this set.

        Args:
            now (float): The current timestamp.
        '''
        now = _time_now(now)
        with self._remote_nodes_lock:
            for node_id, node in list(self._remote_nodes.items()):
                if node.should_timeout(now):
                    _logger.debug('Lost Node {0}: {1}'.format(node_id, node.data))
                    del self._remote_nodes[node_id]


class _RemoteExecutionBroadcastConnection(object):
    '''
    A remote execution broadcast connection (for UDP based messaging and node discovery).

    Args:
        config (RemoteExecutionConfig): Configuration controlling the connection settings.
        node_id (string): The ID of the local "node" (this session).
    '''

    def __init__(self, config, node_id):
        self._config = config
        self._node_id = node_id
        self._nodes = None
        self._running = False
        self._broadcast_socket = None
        self._broadcast_listen_thread = None

    @property
    def remote_nodes(self):
        '''
        Get the current set of discovered remote "nodes" (UE4 instances running Python).

        Returns:
            list: A list of dicts containg the node ID and the other data.
        '''
        return self._nodes.remote_nodes if self._nodes else []

    def open(self):
        '''
        Open the UDP based messaging and discovery connection. This will begin the discovey process for remote "nodes" (UE4 instances running Python).
        '''
        self._running = True
        self._last_ping = None
        self._nodes = _RemoteExecutionBroadcastNodes()
        self._init_broadcast_socket()
        self._init_broadcast_listen_thread()

    def close(self):
        '''
        Close the UDP based messaging and discovery connection. This will end the discovey process for remote "nodes" (UE4 instances running Python).
        '''
        self._running = False
        if self._broadcast_listen_thread:
            self._broadcast_listen_thread.join()
        if self._broadcast_socket:
            self._broadcast_socket.close()
            self._broadcast_socket = None
        self._nodes = None

    def _init_broadcast_socket(self):
        '''
        Initialize the UDP based broadcast socket based on the current configuration.
        '''
        self._broadcast_socket = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM,
                                                _socket.IPPROTO_UDP)  # UDP/IP socket
        if hasattr(_socket, 'SO_REUSEPORT'):
            self._broadcast_socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEPORT, 1)
        else:
            self._broadcast_socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        self._broadcast_socket.bind((self._config.multicast_bind_address, self._config.multicast_group_endpoint[1]))
        self._broadcast_socket.setsockopt(_socket.IPPROTO_IP, _socket.IP_MULTICAST_LOOP, 1)
        self._broadcast_socket.setsockopt(_socket.IPPROTO_IP, _socket.IP_MULTICAST_TTL, self._config.multicast_ttl)
        self._broadcast_socket.setsockopt(_socket.IPPROTO_IP, _socket.IP_ADD_MEMBERSHIP, _socket.inet_aton(
            self._config.multicast_group_endpoint[0]) + _socket.inet_aton('0.0.0.0'))
        self._broadcast_socket.settimeout(0.1)

    def _init_broadcast_listen_thread(self):
        '''
        Initialize the listen thread for the UDP based broadcast socket to allow discovery to run async.
        '''
        self._broadcast_listen_thread = _threading.Thread(target=self._run_broadcast_listen_thread)
        self._broadcast_listen_thread.daemon = True
        self._broadcast_listen_thread.start()

    def _run_broadcast_listen_thread(self):
        '''
        Main loop for the listen thread that handles processing discovery messages.
        '''
        while self._running:
            # Receive and process all pending data
            while True:
                try:
                    data = self._broadcast_socket.recv(4096)
                except _socket.timeout:
                    data = None
                if data:
                    self._handle_data(data)
                else:
                    break
            # Run tick logic
            now = _time_now()
            self._broadcast_ping(now)
            self._nodes.timeout_remote_nodes(now)
            _time.sleep(0.1)

    def _broadcast_message(self, message):
        '''
        Broadcast the given message over the UDP socket to anything that might be listening.

        Args:
            message (_RemoteExecutionMessage): The message to broadcast.
        '''
        self._broadcast_socket.sendto(message.to_json_bytes(), self._config.multicast_group_endpoint)

    def _broadcast_ping(self, now=None):
        '''
        Broadcast a "ping" message over the UDP socket to anything that might be listening.

        Args:
            now (float): The current timestamp.
        '''
        now = _time_now(now)
        if not self._last_ping or ((self._last_ping + _NODE_PING_SECONDS) < now):
            self._last_ping = now
            self._broadcast_message(_RemoteExecutionMessage(_TYPE_PING, self._node_id))

    def broadcast_open_connection(self, remote_node_id):
        '''
        Broadcast an "open_connection" message over the UDP socket to be handled by the specified remote node.

        Args:
            remote_node_id (string): The ID of the remote node that we want to open a command connection with.
        '''
        self._broadcast_message(_RemoteExecutionMessage(_TYPE_OPEN_CONNECTION, self._node_id, remote_node_id, {
            'command_ip': self._config.command_endpoint[0],
            'command_port': self._config.command_endpoint[1],
        }))

    def broadcast_close_connection(self, remote_node_id):
        '''
        Broadcast a "close_connection" message over the UDP socket to be handled by the specified remote node.

        Args:
            remote_node_id (string): The ID of the remote node that we want to close a command connection with.
        '''
        self._broadcast_message(_RemoteExecutionMessage(_TYPE_CLOSE_CONNECTION, self._node_id, remote_node_id))

    def _handle_data(self, data):
        '''
        Handle data received from the UDP broadcast socket.

        Args:
            data (bytes): The raw bytes received from the socket.
        '''
        message = _RemoteExecutionMessage(None, None)
        if message.from_json_bytes(data):
            self._handle_message(message)

    def _handle_message(self, message):
        '''
        Handle a message received from the UDP broadcast socket.

        Args:
            message (_RemoteExecutionMessage): The message received from the socket.
        '''
        if not message.passes_receive_filter(self._node_id):
            return
        if message.type_ == _TYPE_PONG:
            self._handle_pong_message(message)
            return
        _logger.debug('Unhandled remote execution message type "{0}"'.format(message.type_))

    def _handle_pong_message(self, message):
        '''
        Handle a "pong" message received from the UDP broadcast socket.

        Args:
            message (_RemoteExecutionMessage): The message received from the socket.
        '''
        self._nodes.update_remote_node(message.source, message.data)


class _RemoteExecutionCommandConnection(object):
    '''
    A remote execution command connection (for TCP based command processing).

    Args:
        config (RemoteExecutionConfig): Configuration controlling the connection settings.
        node_id (string): The ID of the local "node" (this session).
        remote_node_id (string): The ID of the remote "node" (the UE4 instance running Python).
    '''

    def __init__(self, config, node_id, remote_node_id):
        self._config = config
        self._node_id = node_id
        self._remote_node_id = remote_node_id
        self._command_listen_socket = None
        self._command_channel_socket = _socket.socket()  # This type is only here to appease PyLint

    def open(self, broadcast_connection):
        '''
        Open the TCP based command connection, and wait to accept the connection from the remote party.

        Args:
            broadcast_connection (_RemoteExecutionBroadcastConnection): The broadcast connection to send UDP based messages over.
        '''
        self._nodes = _RemoteExecutionBroadcastNodes()
        self._init_command_listen_socket()
        self._try_accept(broadcast_connection)

    def close(self, broadcast_connection):
        '''
        Close the TCP based command connection, attempting to notify the remote party.

        Args:
            broadcast_connection (_RemoteExecutionBroadcastConnection): The broadcast connection to send UDP based messages over.
        '''
        broadcast_connection.broadcast_close_connection(self._remote_node_id)
        if self._command_channel_socket:
            self._command_channel_socket.close()
            self._command_channel_socket = None
        if self._command_listen_socket:
            self._command_listen_socket.close()
            self._command_listen_socket = None

    def run_command(self, command, unattended, exec_mode):
        '''
        Run a command on the remote party.

        Args:
            command (string): The Python command to run remotely.
            unattended (bool): True to run this command in "unattended" mode (suppressing some UI).
            exec_mode (string): The execution mode to use as a string value (must be one of MODE_EXEC_FILE, MODE_EXEC_STATEMENT, or MODE_EVAL_STATEMENT).

        Returns:
            dict: The result from running the remote command (see `command_result` from the protocol definition).
        '''
        self._send_message(_RemoteExecutionMessage(_TYPE_COMMAND, self._node_id, self._remote_node_id, {
            'command': command,
            'unattended': unattended,
            'exec_mode': exec_mode,
        }))
        result = self._receive_message(_TYPE_COMMAND_RESULT)
        return result.data

    def _send_message(self, message):
        '''
        Send the given message over the TCP socket to the remote party.

        Args:
            message (_RemoteExecutionMessage): The message to send.
        '''
        self._command_channel_socket.sendall(message.to_json_bytes())

    def _receive_message(self, expected_type):
        '''
        Receive a message over the TCP socket from the remote party.

        Args:
            expected_type (string): The type of message we expect to receive.

        Returns:
            The message that was received.
        '''
        data = self._command_channel_socket.recv(4096)
        if data:
            message = _RemoteExecutionMessage(None, None)
            if message.from_json_bytes(data) and message.passes_receive_filter(
                    self._node_id) and message.type_ == expected_type:
                return message
        raise RuntimeError('Remote party failed to send a valid response!')

    def _init_command_listen_socket(self):
        '''
        Initialize the TCP based command socket based on the current configuration, and set it to listen for an incoming connection.
        '''
        self._command_listen_socket = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM,
                                                     _socket.IPPROTO_TCP)  # TCP/IP socket
        if hasattr(_socket, 'SO_REUSEPORT'):
            self._command_listen_socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEPORT, 1)
        else:
            self._command_listen_socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        self._command_listen_socket.bind(self._config.command_endpoint)
        self._command_listen_socket.listen(1)
        self._command_listen_socket.settimeout(5)

    def _try_accept(self, broadcast_connection):
        '''
        Wait to accept a connection on the TCP based command connection. This makes 6 attempts to receive a connection, waiting for 5 seconds between each attempt (30 seconds total).

        Args:
            broadcast_connection (_RemoteExecutionBroadcastConnection): The broadcast connection to send UDP based messages over.
        '''
        for _n in range(6):
            broadcast_connection.broadcast_open_connection(self._remote_node_id)
            try:
                self._command_channel_socket = self._command_listen_socket.accept()[0]
                self._command_channel_socket.setblocking(True)
                return
            except _socket.timeout:
                continue
        raise RuntimeError('Remote party failed to attempt the command socket connection!')


class _RemoteExecutionMessage(object):
    '''
    A message sent or received by remote execution (on either the UDP or TCP connection), as UTF-8 encoded JSON.

    Args:
        type_ (string): The type of this message (see the `_TYPE_` constants).
        source (string): The ID of the node that sent this message.
        dest (string): The ID of the destination node of this message, or None to send to all nodes (for UDP broadcast).
        data (dict): The message specific payload data.
    '''

    def __init__(self, type_, source, dest=None, data=None):
        self.type_ = type_
        self.source = source
        self.dest = dest
        self.data = data

    def passes_receive_filter(self, node_id):
        '''
        Test to see whether this message should be received by the current node (wasn't sent to itself, and has a compatible destination ID).

        Args:
            node_id (string): The ID of the local "node" (this session).

        Returns:
            bool: True if this message should be received by the current node, False otherwise.
        '''
        return self.source != node_id and (not self.dest or self.dest == node_id)

    def to_json(self):
        '''
        Convert this message to its JSON representation.

        Returns:
            str: The JSON representation of this message.
        '''
        if not self.type_:
            raise ValueError('"type" cannot be empty!')
        if not self.source:
            raise ValueError('"source" cannot be empty!')
        json_obj = {
            'version': _PROTOCOL_VERSION,
            'magic': _PROTOCOL_MAGIC,
            'type': self.type_,
            'source': self.source,
        }
        if self.dest:
            json_obj['dest'] = self.dest
        if self.data:
            json_obj['data'] = self.data
        return _json.dumps(json_obj, ensure_ascii=False)

    def to_json_bytes(self):
        '''
        Convert this message to its JSON representation as UTF-8 bytes.

        Returns:
            bytes: The JSON representation of this message as UTF-8 bytes.
        '''
        json_str = self.to_json()
        return json_str.encode('utf-8')

    def from_json(self, json_str):
        '''
        Parse this message from its JSON representation.

        Args:
            json_str (str): The JSON representation of this message.

        Returns:
            bool: True if this message could be parsed, False otherwise.
        '''
        try:
            json_obj = _json.loads(json_str)
            # Read and validate required protocol version information
            if json_obj['version'] != _PROTOCOL_VERSION:
                raise ValueError(
                    '"version" is incorrect (got {0}, expected {1})!'.format(json_obj['version'], _PROTOCOL_VERSION))
            if json_obj['magic'] != _PROTOCOL_MAGIC:
                raise ValueError(
                    '"magic" is incorrect (got "{0}", expected "{1}")!'.format(json_obj['magic'], _PROTOCOL_MAGIC))
            # Read required fields
            local_type = json_obj['type']
            local_source = json_obj['source']
            self.type_ = local_type
            self.source = local_source
            # Read optional fields
            self.dest = json_obj.get('dest')
            self.data = json_obj.get('data')
        except Exception as e:
            _logger.error('Failed to deserialize JSON "{0}": {1}'.format(json_str, str(e)))
            return False
        return True

    def from_json_bytes(self, json_bytes):
        '''
        Parse this message from its JSON representation as UTF-8 bytes.

        Args:
            json_bytes (bytes): The JSON representation of this message as UTF-8 bytes.

        Returns:
            bool: True if this message could be parsed, False otherwise.
        '''
        json_str = json_bytes.decode('utf-8')
        return self.from_json(json_str)


def _time_now(now=None):
    '''
    Utility function to resolve a potentially cached time value.

    Args:
        now (float): The cached timestamp, or None to return the current time.

    Returns:
        float: The cached timestamp (if set), otherwise the current time.
    '''
    return _time.time() if now is None else now


# Log handling
_logger = _logging.getLogger(__name__)
_log_handler = _logging.StreamHandler()
_logger.addHandler(_log_handler)


def set_log_level(log_level):
    _logger.setLevel(log_level)
    _log_handler.setLevel(log_level)
