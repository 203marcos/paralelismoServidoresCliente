#!/usr/bin/env bash
# Para parar os servidores iniciados por run_local.sh

PIDS_FILE="matrix_servers.pids"
any_killed=0

# Se houver arquivo de PIDs, mata os PIDs listados
if [ -f "$PIDS_FILE" ]; then
  echo "Parando servidores listados em $PIDS_FILE"
  while read -r pid; do
    if [ -z "$pid" ]; then
      continue
    fi
    if kill -0 "$pid" 2>/dev/null; then
      echo "  matando PID $pid"
      kill "$pid" || true
      any_killed=1
    else
      echo "  PID $pid não está mais ativo"
    fi
  done < "$PIDS_FILE"
  rm -f "$PIDS_FILE"
fi

# Fallback: procura processos pelo nome e mata (útil quando pidfile não existe)
echo "Procurando processos 'matrix_distributed.server' ativos..."
PIDS=$(pgrep -f 'matrix_distributed.server' || true)
if [ -n "$PIDS" ]; then
  for pid in $PIDS; do
    if kill -0 "$pid" 2>/dev/null; then
      echo "  matando PID $pid (descoberto por pgrep)"
      kill "$pid" || true
      any_killed=1
    fi
  done
fi

if [ "$any_killed" -eq 0 ]; then
  echo "Nenhum servidor ativo encontrado."
else
  echo "Servidores parados."
fi

echo "Pronto."
