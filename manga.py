import os
import re
from bs4 import BeautifulSoup
from curl_cffi import requests

# Configurações iniciais
url = 'https://deliciousdungeon.com/manga/delicious-in-dungeon-chapter-01/'
pasta_destino = 'Delicious_in_Dungeon_Cap_01'

# Cria a pasta local
if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)
    print(f"Pasta '{pasta_destino}' pronta.")

print("Acessando a página contornando o bloqueio Anti-Bot e erros de SSL...")

# Usa o curl_cffi para imitar o Chrome 110 e ignora o SSL com verify=False
# Como ele não usa o motor padrão do Python, o ValueError não vai acontecer
response = requests.get(url, impersonate="chrome110", verify=False)

if response.status_code != 200:
    print(f"Erro ao acessar a página. Código: {response.status_code}")
else:
    soup = BeautifulSoup(response.content, 'html.parser')
    imagens = soup.find_all('img')
    
    padrao_url = re.compile(r'/s\d+/(\d+)\.jpg', re.IGNORECASE)
    
    imagens_baixadas = 0
    
    for img in imagens:
        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        
        if img_url:
            match = padrao_url.search(img_url)
            
            if match:
                numero_original = match.group(1)
                
                try:
                    # Baixa a imagem usando a mesma imitação de navegador
                    img_response = requests.get(img_url, impersonate="chrome110", verify=False)
                    img_data = img_response.content
                    
                    nome_arquivo = f"{int(numero_original):02d}.jpg"
                    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
                    
                    with open(caminho_completo, 'wb') as handler:
                        handler.write(img_data)
                        
                    print(f"Página {nome_arquivo} salva com sucesso!")
                    imagens_baixadas += 1
                    
                except Exception as e:
                    print(f"Erro ao baixar a página {numero_original}: {e}")

    if imagens_baixadas == 0:
         print("\nNenhuma imagem encontrada. O site pode ter mudado a estrutura.")
    else:
         print(f"\nConcluído! {imagens_baixadas} páginas foram baixadas para a pasta local.")