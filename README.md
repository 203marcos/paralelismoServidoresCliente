# matrix_distributed — Demonstração de multiplicação de matrizes distribuída

Descrição
- Projeto didático que demonstra multiplicação de matrizes distribuída: o cliente divide a matriz A por linhas, envia submatrizes e a matriz B para servidores remotos/locais; cada servidor calcula seu produto parcial e devolve o resultado; o cliente monta a matriz resultante C.

Principais pontos
- Objetivo: entender comunicação cliente/servidor, divisão de trabalho e medidas de desempenho.
- Protocolos: TCP com mensagens prefixadas e objetos serializados (pickle).
- Bibliotecas: `numpy` para operações matriciais; stdlib para sockets e concorrência.

Arquivos importantes
- `matrix_distributed/client.py`: cliente que divide A, envia tarefas e junta resultados.
- `matrix_distributed/server.py`: servidor que recebe `A_sub` e `B`, calcula `A_sub.dot(B)` e retorna.
- `matrix_distributed/utils.py`: utilitários de envio/recebimento de mensagens.
- `matrix_distributed/README.md`: instruções internas do pacote (mais técnicas).
- `run_local.sh`: inicia N servidores locais (porta base 6000 por padrão).
- `run_local_stop.sh`: para servidores iniciados (usa `matrix_servers.pids` ou fallback por processo).
- `run_client.sh`: wrapper curto para rodar o cliente contra servidores locais.
- `matrix_servers.pids`: gerado pelo `run_local.sh`, contém PIDs dos servidores.
- `server_<porta>.log`: logs de cada servidor.

Pré-requisitos
- Python 3.8+ e `pip`.
- Instalar dependências:

```bash
pip install -r requirements.txt
```

Como rodar (exemplo local)
- Iniciar 4 servidores locais (puerta base 6000):

```bash
./run_local.sh 4
```

- Rodar o cliente com atalho (N = dimensão da matriz quadrada):

```bash
./run_client.sh 4 2048 60
```

  ou diretamente:

```bash
python3 -m matrix_distributed.client -s 4 -b 6000 -N 2048 --timeout 60
```

- Parar servidores:

```bash
./run_local_stop.sh
```

Design em poucas linhas
- O cliente gera duas matrizes A e B (ou usa entradas reais), divide A em blocos de linhas balanceados e envia cada bloco a um servidor (host:port) junto com B.
- Cada servidor calcula o produto parcial `A_block.dot(B)` e retorna a matriz parcial serializada.
- O cliente recebe todos os blocos e faz `np.vstack` para montar C.

Sugestões para apresentação
- Mostrar execução end-to-end: iniciar servidores, rodar cliente, mostrar tempos total e por-servidor (o cliente imprime essas métricas).
- Comparar com execução local (NumPy puro) para discutir overhead de comunicação.

Notas de segurança e limitações
- Protocolo usa `pickle` (não seguro para dados de fontes não confiáveis). Usar apenas em ambiente controlado/didático.
- O demonstrador é para ensino; não é uma solução de produção.
