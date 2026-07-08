import os
import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from seleniumbase import Driver
from PIL import Image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://deliciousdungeon.com/manga/delicious-in-dungeon-chapter-01/'
pasta_destino = 'capitulo_01_temp'
nome_pdf = 'Delicious_in_Dungeon_Cap_01.pdf'

if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)

print("Iniciando navegador no modo MÁSCARA MÁXIMA (Xvfb + Real Browser)...")

# A MÁGICA ESTÁ AQUI: headless=False
# Como o GitHub não tem monitor, o Xvfb (que configuramos no .yml) vai absorver a tela
driver = Driver(uc=True, headless=False)

try:
    print("Acessando o site e aguardando verificação anti-bot...")
    driver.get(url)
    
    # Damos 15 segundos porque servidores do GitHub podem ser um pouco mais lentos 
    # e precisamos que o Cloudflare termine de rodar os scripts dele
    time.sleep(15) 
    
    # Rolagem de página suave para enganar o anti-bot e ativar o Lazy-Load
    print("Rolando a página para carregar as imagens...")
    for i in range(1, 10):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/10});")
        time.sleep(1.5)
        
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    imagens = soup.find_all('img')
    
    padrao_url = re.compile(r'/s\d+/(\d+)\.jpg', re.IGNORECASE)
    imagens_baixadas = 0
    
    print("Iniciando o download das páginas...")
    for img in imagens:
        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if img_url:
            match = padrao_url.search(img_url)
            if match:
                numero = match.group(1)
                try:
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
        # SISTEMA DE DEBUG: Tira print se falhar!
        print("\nNenhuma imagem encontrada. O bloqueio ainda está ativo.")
        print("Tirando um print da tela para investigarmos...")
        driver.save_screenshot("debug_cloudflare.png")
        exit(1)

finally:
    driver.quit()