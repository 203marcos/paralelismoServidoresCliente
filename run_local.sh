#!/usr/bin/env bash
# Script simples para iniciar N servidores em background
# Uso: ./run_local.sh <num_servidores> <porta_inicial>
# Ex: ./run_local.sh 2 6000  -> inicia servidores nas portas 6000 e 6001

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Uso: $0 <num_servidores> [porta_inicial]"
  exit 1
fi

NUM=${1}
START_PORT=${2:-6000}
PIDS_FILE="matrix_servers.pids"

echo "Iniciando $NUM servidores a partir da porta $START_PORT"
rm -f "$PIDS_FILE"

for i in $(seq 0 $((NUM-1))); do
  PORT=$((START_PORT + i))
  echo "  iniciando servidor na porta $PORT"
  # Verifica se a porta já está em uso; tentamos abrir conexão TCP localmente.
  # Usamos /dev/tcp (bash) para testar rapidamente.
  if (echo > /dev/tcp/127.0.0.1/${PORT}) >/dev/null 2>&1; then
    echo "  porta $PORT já em uso — pulando"
    continue
  fi

  # Start: executa o servidor como módulo (-u para evitar buffering)
  # Logs redirecionados para server_<porta>.log
  python3 -u -m matrix_distributed.server --port ${PORT} --workers 1 &>> server_${PORT}.log &
  PID=$!

  # Espera até 1s pela linha de confirmação no log
  started=0
  for i in $(seq 1 10); do
    if grep -q "Servidor ouvindo" server_${PORT}.log 2>/dev/null; then
      started=1
      break
    fi
    sleep 0.1
  done

  if [ "$started" -eq 1 ]; then
    echo $PID >> "$PIDS_FILE"
  else
    echo "  falha ao iniciar servidor na porta $PORT — ver server_${PORT}.log" >&2
    tail -n 50 server_${PORT}.log >&2 || true
  fi
done

echo "Servidores iniciados. PIDs em $PIDS_FILE"
echo "Logs: server_<porta>.log"
echo "Para parar, execute: ./run_local_stop.sh"
