import os
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from seleniumbase import Driver
from PIL import Image
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# CONFIGURAÇÕES DE CAPÍTULOS
# ==========================================
capitulo_inicial = 74
capitulo_final = 80  # Mude aqui para baixar quantos capítulos quiser de uma vez

print(f"Iniciando download dos capítulos {capitulo_inicial} ao {capitulo_final}...")
print("Iniciando navegador no modo MÁSCARA MÁXIMA (Xvfb + Real Browser)...")

# Abre o navegador uma única vez para todos os capítulos
driver = Driver(uc=True, headless=False)

try:
    for capitulo in range(capitulo_inicial, capitulo_final + 1):
        
        # Formata o número com dois dígitos (01, 02, 03...)
        num_formatado = f"{capitulo:02d}"
        
        url = f'https://deliciousdungeon.com/manga/delicious-in-dungeon-chapter-{num_formatado}/'
        pasta_destino = f'capitulo_{num_formatado}_temp'
        nome_pdf = f'Delicious_in_Dungeon_Cap_{num_formatado}.pdf'

        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        print(f"\n[{num_formatado}] Acessando: {url}")
        driver.get(url)
        
        time.sleep(10) # Aguarda o Cloudflare validar
        
        print(f"[{num_formatado}] Rolando a página para disparar o Lazy-Load...")
        for i in range(1, 15):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/15});")
            time.sleep(1.5)
            
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        imagens = soup.find_all('img')
        
        imagens_baixadas = 0
        contador = 1
        
        print(f"[{num_formatado}] Mapeando e baixando as páginas...")
        for img in imagens:
            img_url = img.get('data-src') or img.get('data-lazy-src') or img.get('data-original') or img.get('src')
            
            if img_url and isinstance(img_url, str) and not img_url.startswith('data:image'):
                if 'googleusercontent' in img_url or 'uploads' in img_url:
                    if 'thumb' not in img_url.lower() and 'logo' not in img_url.lower():
                        try:
                            img_data = requests.get(img_url, verify=False, timeout=15).content
                            imagem_aberta = Image.open(io.BytesIO(img_data)).convert('RGB')
                            
                            nome_arquivo = f"{contador:02d}.jpg"
                            caminho = os.path.join(pasta_destino, nome_arquivo)
                            imagem_aberta.save(caminho, 'JPEG')
                            
                            print(f"  -> Página {nome_arquivo} salva!")
                            imagens_baixadas += 1
                            contador += 1
                        except Exception as e:
                            print(f"  -> Erro ao baixar a imagem: {img_url} - Erro: {e}")

        # --- GERAÇÃO DO PDF PARA O CAPÍTULO ATUAL ---
        if imagens_baixadas > 0:
            print(f"[{num_formatado}] Gerando PDF do capítulo...")
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
                print(f"[{num_formatado}] Sucesso! PDF gerado: {nome_pdf}")
        else:
            print(f"[{num_formatado}] Nenhuma imagem encontrada. Pode ser o fim do mangá ou erro de link.")
            # Salva o print do erro com o número do capítulo para debug
            driver.save_screenshot(f"debug_cap_{num_formatado}.png")
            break # Interrompe o loop se não achar nada (evita ficar rodando no vazio)

    print("\nProcesso concluído para todos os capítulos solicitados!")

finally:
    driver.quit()