#!/bin/bash

# Iniciar o tracker
echo "Iniciando o tracker..."
python -m src.tracker &

# Espera o tracker subir
sleep 2

# Iniciar 15 peers
for i in $(seq 1 5)
do
    echo "Iniciando peer $i..."
    python -m src.implementacao --id=$i & 
    sleep 0.5
done

echo "Todos os peers estão rodando."
