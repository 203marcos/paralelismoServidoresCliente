#!/usr/bin/env python3
"""Explicação: Loop principal: cria socket, faz bind/listen e aceita conexões."""

import argparse
import socket
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from matrix_distributed.utils import recv_msg, send_msg


def compute_block(A_block, B):
    # compute_block: retorna A_block.dot(B)
    return A_block.dot(B)


def handle_client(conn, use_pool, workers):
    # handle_client: lê {'A','B'}; calcula produto; envia {'result'}; conn.close() fecha o socket
    try:
        data = recv_msg(conn)
        A = data['A']
        B = data['B']
        task_id = data.get('task_id')

        # Se solicitado, dividimos as linhas em pedaços e calculamos em paralelo
        if use_pool and workers > 1 and A.shape[0] >= workers:
            rows = A.shape[0]
            # calcula tamanhos de cada pedaço (distribuição equilibrada)
            chunk_sizes = [(rows // workers) + (1 if i < (rows % workers) else 0) for i in range(workers)]
            starts = []
            s = 0
            for size in chunk_sizes:
                starts.append((s, s + size))
                s += size
            chunks = [A[s:e] for (s, e) in starts if e > s]
            with Pool(processes=len(chunks)) as p:
                parts = p.starmap(compute_block, [(chunk, B) for chunk in chunks])
            C_part = np.vstack(parts) if parts else np.zeros((0, B.shape[1]))
        else:
            # caminho rápido: NumPy calcula o produto direto
            C_part = A.dot(B)

        send_msg(conn, {'result': C_part, 'task_id': task_id})
    except Exception as e:
        # Em caso de erro, enviamos uma mensagem com campo 'error'
        try:
            send_msg(conn, {'error': str(e)})
        except Exception:
            pass
    finally:
        conn.close()


def serve(host, port, use_pool=False, workers=1, max_workers=10):
    # serve: Loop principal: cria socket, SO_REUSEADDR, bind/listen, accept() e delega a threads; sock.close() fecha o socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
    except OSError as e:
        print(f"ERRO: não foi possível bind em {host}:{port}: {e}", flush=True)
        sock.close()
        import sys
        # encerra sem traceback (exit code não-zero indica falha)
        sys.exit(1)
    sock.listen()
    print(f"Servidor ouvindo em {host}:{port} (pool_local={use_pool}, workers={workers})", flush=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        try:
            while True:
                conn, addr = sock.accept()
                # handle_client espera (conn, use_pool, workers)
                executor.submit(handle_client, conn, use_pool, workers)
        except KeyboardInterrupt:
            print('Servidor encerrado (KeyboardInterrupt)', flush=True)
        finally:
            sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--workers', type=int, default=1, help='número de processos locais para cálculo')
    parser.add_argument('--max-conns', type=int, default=10, help='máximo de handlers concorrentes (threads)')
    args = parser.parse_args()

    serve(args.host, args.port, use_pool=(args.workers > 1), workers=args.workers, max_workers=args.max_conns)


if __name__ == '__main__':
    main()
