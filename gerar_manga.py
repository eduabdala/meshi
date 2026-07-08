import os
import re
from bs4 import BeautifulSoup
from curl_cffi import requests
from PIL import Image

url = 'https://deliciousdungeon.com/manga/delicious-in-dungeon-chapter-01/'
pasta_destino = 'capitulo_01_temp'
nome_pdf = 'Delicious_in_Dungeon_Cap_01.pdf'

if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)

print("Iniciando o scraper...")

try:
    response = requests.get(url, impersonate="chrome110", verify=False, timeout=30)
    
    if response.status_code != 200:
        print(f"Erro fatal: Servidor retornou {response.status_code}. Bloqueio ativo.")
        exit(1)
        
    soup = BeautifulSoup(response.content, 'html.parser')
    imagens = soup.find_all('img')
    padrao_url = re.compile(r'/s\d+/(\d+)\.jpg', re.IGNORECASE)
    
    imagens_baixadas = 0
    
    for img in imagens:
        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if img_url:
            match = padrao_url.search(img_url)
            if match:
                numero = match.group(1)
                try:
                    img_data = requests.get(img_url, impersonate="chrome110", verify=False).content
                    nome_arquivo = f"{int(numero):02d}.jpg"
                    caminho = os.path.join(pasta_destino, nome_arquivo)
                    
                    with open(caminho, 'wb') as f:
                        f.write(img_data)
                    print(f"Página {nome_arquivo} baixada.")
                    imagens_baixadas += 1
                except Exception as e:
                    print(f"Erro na página {numero}: {e}")

    # --- GERAÇÃO DO PDF ---
    if imagens_baixadas > 0:
        print("\nGerando PDF...")
        # Pega todas as imagens da pasta e ordena numericamente
        arquivos = sorted([f for f in os.listdir(pasta_destino) if f.endswith('.jpg')])
        
        lista_imagens = []
        for arquivo in arquivos:
            caminho_img = os.path.join(pasta_destino, arquivo)
            # Converte para RGB (necessário para salvar como PDF no Pillow)
            img = Image.open(caminho_img).convert('RGB')
            lista_imagens.append(img)
            
        if lista_imagens:
            # Salva a primeira imagem e anexa o restante como páginas subsequentes
            lista_imagens[0].save(
                nome_pdf, 
                save_all=True, 
                append_images=lista_imagens[1:]
            )
            print(f"Sucesso! PDF gerado: {nome_pdf}")
    else:
        print("Nenhuma imagem baixada. Arquivo PDF não gerado.")
        exit(1)

except Exception as e:
    print(f"Erro na execução do script: {e}")
    exit(1)