#!/usr/bin/env bash
# run_client.sh — atalho para executar o cliente com opções curtas
# Uso: ./run_client.sh <num_servidores> [size] [timeout]
# Ex: ./run_client.sh 4 512 60   -> 4 servidores, matrizes 512x512, timeout 60s

if [ "$#" -lt 1 ]; then
  echo "Uso: $0 <num_servidores> [size] [timeout]"
  exit 1
fi

# número de servidores locais a usar (ex.: 4 → localhost:6000..6003)
N=$1
# tamanho das matrizes (opcional) — define m=k=n
SIZE=${2:-}
# timeout de rede em segundos (opcional)
TIMEOUT=${3:-60}

# monta comando reduzido que chama o cliente como módulo
CMD=(python3 -m matrix_distributed.client -s "$N" -b 6000 --timeout "$TIMEOUT")
if [ -n "$SIZE" ]; then
  CMD+=( -N "$SIZE" )
fi

# informa e executa — útil para integração/CI rápida
echo "Executando: ${CMD[*]}"
"${CMD[@]}"
