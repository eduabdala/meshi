import os
import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from seleniumbase import Driver
from PIL import Image
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://deliciousdungeon.com/manga/delicious-in-dungeon-chapter-01/'
pasta_destino = 'capitulo_01_temp'
nome_pdf = 'Delicious_in_Dungeon_Cap_01.pdf'

if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)

print("Iniciando navegador no modo MÁSCARA MÁXIMA (Xvfb + Real Browser)...")

driver = Driver(uc=True, headless=False)

try:
    print("Acessando o site e aguardando verificação anti-bot...")
    driver.get(url)
    
    time.sleep(15) 
    
    print("Rolando a página para carregar as imagens...")
    for i in range(1, 11):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/10});")
        time.sleep(1.5)
        
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    imagens = soup.find_all('img')
    
    imagens_baixadas = 0
    contador = 1
    
    print("Iniciando o download das páginas...")
    for img in imagens:
        # Pega a URL de onde a imagem estiver escondida
        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        
        # Filtro Inteligente: Pega imagens do Google Blogger ou do próprio site, 
        # ignorando ícones, logos e avatares menores.
        if img_url and ('googleusercontent' in img_url or 'uploads' in img_url):
            if 'logo' not in img_url.lower() and 'avatar' not in img_url.lower():
                
                # Tenta extrair o número da URL se existir (ex: /05.webp -> 5)
                match = re.search(r'/(\d+)\.(jpg|png|webp|jpeg)', img_url, re.IGNORECASE)
                numero = int(match.group(1)) if match else contador
                
                try:
                    img_data = requests.get(img_url, verify=False, timeout=15).content
                    
                    # Converte a imagem na memória para garantir que seja salva como JPG limpo
                    # Isso resolve o problema de sites que usam .webp e quebram a geração do PDF
                    imagem_aberta = Image.open(io.BytesIO(img_data)).convert('RGB')
                    
                    nome_arquivo = f"{numero:02d}.jpg"
                    caminho = os.path.join(pasta_destino, nome_arquivo)
                    
                    imagem_aberta.save(caminho, 'JPEG')
                    
                    print(f"Página {nome_arquivo} baixada com sucesso!")
                    imagens_baixadas += 1
                    contador += 1
                except Exception as e:
                    print(f"Ignorando imagem inválida ou com erro: {img_url} - Erro: {e}")

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
        print("\nNenhuma imagem de mangá encontrada. Salvando HTML para debug...")
        driver.save_screenshot("debug_cloudflare.png")
        with open("codigo_do_site.html", "w", encoding="utf-8") as f:
            f.write(html)
        exit(1)

finally:
    driver.quit()