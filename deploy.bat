@echo off
echo --- A PREPARAR ENVIO PARA GITHUB ---
set /p msg="Escreva a mensagem do commit (Enter para 'Atualizacao'): "
if "%msg%"=="" set msg="Atualizacao automatica"

git add .
git commit -m "%msg%"
git push

echo --- CONCLUIDO! AGORA VÁ AO PYTHONANYWHERE E CORRA: bash update_server.sh ---
pause