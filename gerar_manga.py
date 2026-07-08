import os
import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from seleniumbase import Driver
from PIL import Image

# Desativa avisos de segurança ao baixar imagens diretas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://deliciousdungeon.com/manga/delicious-in-dungeon-chapter-01/'
pasta_destino = 'capitulo_01_temp'
nome_pdf = 'Delicious_in_Dungeon_Cap_01.pdf'

if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)

print("Iniciando navegador fantasma para burlar o Cloudflare...")

# Inicializa o Undetected Chromedriver (Modo UC) em modo invisível (headless)
driver = Driver(uc=True, headless=True)

try:
    print("Acessando o site e aguardando verificação anti-bot...")
    driver.get(url)
    
    # Dá 10 segundos para o Cloudflare carregar e o site renderizar as imagens (Lazy Load)
    time.sleep(10) 
    
    # Pega o HTML final, já processado e validado
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    imagens = soup.find_all('img')
    
    padrao_url = re.compile(r'/s\d+/(\d+)\.jpg', re.IGNORECASE)
    imagens_baixadas = 0
    
    print("Mapeando imagens do capítulo...")
    for img in imagens:
        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if img_url:
            match = padrao_url.search(img_url)
            if match:
                numero = match.group(1)
                try:
                    # O link da imagem (Blogger) não costuma ter bloqueio forte, 
                    # então baixamos diretamente com requests
                    img_data = requests.get(img_url, verify=False, timeout=15).content
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
        arquivos = sorted([f for f in os.listdir(pasta_destino) if f.endswith('.jpg')])
        
        lista_imagens = []
        for arquivo in arquivos:
            caminho_img = os.path.join(pasta_destino, arquivo)
            img = Image.open(caminho_img).convert('RGB')
            lista_imagens.append(img)
            
        if lista_imagens:
            lista_imagens[0].save(
                nome_pdf, 
                save_all=True, 
                append_images=lista_imagens[1:]
            )
            print(f"Sucesso! PDF gerado: {nome_pdf}")
    else:
        print("\nNenhuma imagem encontrada. O bloqueio pode ser um Captcha visual ou a estrutura do site mudou.")
        exit(1)

finally:
    # Garante que o navegador vai ser fechado para não travar a máquina
    driver.quit()