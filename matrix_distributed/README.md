## Multiplicação de Matrizes Distribuída — resumo prático

Este repositório contém um protótipo cliente/servidor que divide a matriz A por
linhas, envia cada bloco a um servidor que calcula `A_sub.dot(B)` e retorna o
resultado parcial. O cliente concatena os blocos para formar C.

Arquivos importantes e responsabilidade rápida:
- `matrix_distributed/utils.py`: envio/recebimento seguro de objetos via socket
  (`send_msg` / `recv_msg`).
- `matrix_distributed/server.py`: aceita conexões, recebe {'A','B'} e responde
  com {'result': C_sub}.
- `matrix_distributed/client.py`: divide A, envia para servidores em paralelo
  e monta C. Mede tempos por servidor.
- `run_local.sh` / `run_local_stop.sh`: ajuda a iniciar/parar múltiplos servidores
  localmente. Logs: `server_<porta>.log`.
- `run_client.sh`: atalho para rodar o cliente com opções curtas.

Como rodar (passo a passo curto)
1) (opcional) criar virtualenv e instalar dependências:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r matrix_distributed/requirements.txt
```

2) iniciar N servidores locais (ex.: 4):
```bash
chmod +x run_local.sh run_local_stop.sh
./run_local.sh 4 6000   # inicia servidores em 6000..6003
```

3) rodar o cliente (atalho curto):
```bash
./run_client.sh 4 512 60   # 4 servidores, matrizes 512x512, timeout 60s
# ou diretamente:
python3 -m matrix_distributed.client -s 4 -N 512 --timeout 60
```

4) parar os servidores quando terminar:
```bash
./run_local_stop.sh
```

Notas sobre as funções (curto e direto)
- `send_msg(sock, obj)` — serializa `obj` e envia com prefixo de 8 bytes
  (tamanho). Isso evita mensagens partidas.
- `recv_msg(sock)` — lê o prefixo, depois a carga inteira, e desserializa.
- `split_matrix_rows(A, n)` — retorna n submatrizes de A (linhas balanceadas).
- `distributed_matmul(servers, A, B)` — envia cada submatriz ao servidor i,
  espera as respostas em paralelo e faz `np.vstack` para montar C.

Dicas rápidas de uso e experimentos
- Para medir tempo de computação em vez do overhead de comunicação, use
  matrizes maiores (ex.: 512 ou 1024).
- Para simular muitos servidores localmente, garanta portas livres e RAM/CPU
  suficiente; o script `run_local.sh` pula portas já em uso.

Segurança
- Este é um protótipo: usamos `pickle`. Não exponha a portas públicas sem
  medidas de segurança. Para produção considere formatos seguros (msgpack,
  numpy.save, protocolo RPC autenticado etc.).
