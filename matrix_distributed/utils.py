import struct
import pickle

# Funções pequenas e reutilizáveis para enviar/receber objetos via socket.
# Implementação: pickle + prefixo de 8 bytes com o tamanho da carga.

# Estrutura para prefixo de tamanho: 8 bytes, ordem de rede
PREFIX_TAMANHO = struct.Struct('!Q')


def send_msg(sock, obj):
    """Serializa `obj` e envia com prefixo de 8 bytes (tamanho).

    Uso: send_msg(sock, {'A': subA, 'B': B}).
    """
    data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    sock.sendall(PREFIX_TAMANHO.pack(len(data)))
    sock.sendall(data)


def recv_all(sock, n):
    """Lê exatamente `n` bytes do socket; lança `ConnectionError` se fechar."""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionError('socket fechado enquanto lia dados')
        data.extend(packet)
    return bytes(data)


def recv_msg(sock):
    """Recebe objeto: lê 8 bytes de tamanho e desserializa o payload."""
    len_data = recv_all(sock, PREFIX_TAMANHO.size)
    (length,) = PREFIX_TAMANHO.unpack(len_data)
    payload = recv_all(sock, length)
    return pickle.loads(payload)
