cd ~/Downloads
unzip -o boletin-senado-fase0.zip
git clone https://github.com/marcosadrianpb/Boletin-Senado.git repo
cp -r boletin-senado/. repo/
cd repo
git add .
git commit -m "Fase 0: script de reconocimiento"
git push
