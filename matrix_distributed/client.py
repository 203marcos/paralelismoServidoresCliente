#!/usr/bin/env python3
"""Explicação: divide A por linhas; envia blocos; concatena resultados."""

import argparse
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from time import perf_counter
from matrix_distributed.utils import send_msg, recv_msg


def parse_host(s):
    # parse_host: 'host:port' -> (host, int(port)); porta padrão 6000
    host, port = s.split(':') if ':' in s else (s, '6000')
    return host, int(port)


def worker_send_and_recv(server, subA, B, task_id=None, timeout=30.0):
    # worker_send_and_recv: envia {'A','B'}; retorna {'result'|'error'} e 'time' (s)
    host, port = server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    start = perf_counter()
    try:
        sock.settimeout(timeout)
        sock.connect((host, port))
        send_msg(sock, {'A': subA, 'B': B, 'task_id': task_id})
        resp = recv_msg(sock)
        elapsed = perf_counter() - start
        # anexa tempo de ida-e-volta à resposta (em segundos)
        if isinstance(resp, dict):
            resp['time'] = elapsed
        return resp
    except socket.timeout:
        elapsed = perf_counter() - start
        return {'error': f'timeout ao conectar/receber de {host}:{port} (timeout={timeout}s)', 'time': elapsed}
    except ConnectionRefusedError:
        elapsed = perf_counter() - start
        return {'error': f'conexão recusada por {host}:{port}', 'time': elapsed}
    except Exception as e:
        elapsed = perf_counter() - start
        return {'error': f'erro de rede ao falar com {host}:{port}: {e}', 'time': elapsed}
    finally:
        try:
            sock.close()
        except Exception:
            pass


def split_matrix_rows(A, n_parts):
    # split_matrix_rows: divide A em n_parts blocos de linhas (balanceado)
    m = A.shape[0]
    sizes = [(m // n_parts) + (1 if i < (m % n_parts) else 0) for i in range(n_parts)]
    parts = []
    off = 0
    for size in sizes:
        parts.append((off, off + size))
        off += size
    return [A[s:e] for s, e in parts]


def distributed_matmul(servers, A, B, timeout=30.0):
    # distributed_matmul: envia blocos a servidores em paralelo; junta resultados com np.vstack; imprime tempos
    n = len(servers)
    parts = split_matrix_rows(A, n)
    results = [None] * n

    times = [None] * n
    with ThreadPoolExecutor(max_workers=len(servers)) as ex:
        futures = {}
        for i, srv in enumerate(servers):
            subA = parts[i]
            # dispara envio e aguarda resposta em paralelo
            futures[ex.submit(worker_send_and_recv, srv, subA, B, i, timeout)] = i

        t0 = perf_counter()
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                resp = fut.result()
            except Exception as e:
                raise RuntimeError(f"Erro interno ao obter resultado do worker {i} (servidor={servers[i]}): {e}")

            if resp is None:
                raise RuntimeError(f"Resposta vazia do servidor {servers[i]}")

            if 'error' in resp:
                # propagamos erro com informação do servidor
                raise RuntimeError(f"Servidor {servers[i]} retornou erro: {resp['error']}")

            # validação simples da resposta
            if 'result' not in resp:
                raise RuntimeError(f"Servidor {servers[i]} retornou dados inesperados: {resp}")
            # armazenamos resultado e tempo (se houver)
            results[i] = resp['result']
            times[i] = resp.get('time')

        # fim do for as_completed
        total = perf_counter() - t0

    # concatena os blocos verticalmente para formar C
    C = np.vstack(results)

    # imprime resumo de tempos
    print('\nResumo de tempos:')
    print(f'  tempo total (após envio das tasks): {total:.4f} s')
    for idx, srv in enumerate(servers):
        t = times[idx]
        if t is None:
            print(f'  servidor {srv}: sem tempo')
        else:
            print(f'  servidor {srv}: tempo RTT approx = {t:.4f} s')

    return C


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--servers', nargs='+', required=True,
                        help="lista de servidores 'host:port' ou um único número (ex: 2) para usar localhost:6000..")
    parser.add_argument('-b', '--base-port', type=int, default=6000, help='porta inicial ao usar número de servidores')
    parser.add_argument('-N', '--size', type=int, default=None, help='tamanho único para gerar matrizes quadradas (define m=k=n)')
    parser.add_argument('--example', action='store_true', help='usar as matrizes de exemplo dos slides')
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--m', type=int, default=256, help='linhas de A')
    parser.add_argument('--k', type=int, default=256, help='colunas de A / linhas de B')
    parser.add_argument('--n', type=int, default=256, help='colunas de B')
    parser.add_argument('--timeout', type=float, default=30.0, help='timeout (s) para operações de rede')
    args = parser.parse_args()

    # Permitir que o usuário passe um número para criar servidores locais automaticamente.
    if len(args.servers) == 1 and args.servers[0].isdigit():
        n = int(args.servers[0])
        if n <= 0:
            raise SystemExit('o número de servidores deve ser >= 1')
        servers = [('localhost', args.base_port + i) for i in range(n)]
        print(f'Cliente: interpretando --servers {n} → servidores locais {servers}')
    else:
        servers = [parse_host(s) for s in args.servers]

    if args.size is not None:
        args.m = args.k = args.n = args.size

    if args.example:
        A = np.array([[1, 0, -1], [4, -1, 2], [-1, 2, 4]])
        B = np.array([[-1, 2, -3], [5, -4, 2], [4, 1, 0]])
    else:
        if args.seed is not None:
            np.random.seed(args.seed)
        A = np.random.randint(-5, 6, size=(args.m, args.k)).astype(np.int64)
        B = np.random.randint(-5, 6, size=(args.k, args.n)).astype(np.int64)

    if A.shape[1] != B.shape[0]:
        raise SystemExit('Dimensões incompatíveis: A.colunas deve ser igual a B.linhas')

    print(f'Cliente: A.shape={A.shape}, B.shape={B.shape}, enviando para {len(servers)} servidores')
    C = distributed_matmul(servers, A, B, timeout=args.timeout)
    print('Matriz resultante C (shape):', C.shape)
    print(C)


if __name__ == '__main__':
    main()
