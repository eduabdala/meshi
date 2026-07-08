import os
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from seleniumbase import Driver
from PIL import Image
import io
import sys
from functools import partial

# MÁGICA PARA O GITHUB ACTIONS: Força o log a atualizar em tempo real
print = partial(print, flush=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# CONFIGURAÇÕES DE CAPÍTULOS
# ==========================================
capitulo_inicial = 1
capitulo_final = 98  

print(f"Iniciando download dos capítulos {capitulo_inicial} ao {capitulo_final}...")
print("Iniciando navegador no modo MÁSCARA MÁXIMA (Xvfb + Real Browser)...")

driver = Driver(uc=True, headless=False)

try:
    for capitulo in range(capitulo_inicial, capitulo_final + 1):
        num_formatado = f"{capitulo:02d}"
        
        url = f'https://deliciousdungeon.com/manga/delicious-in-dungeon-chapter-{num_formatado}/'
        pasta_destino = f'capitulo_{num_formatado}_temp'
        nome_pdf = f'Delicious_in_Dungeon_Cap_{num_formatado}.pdf'

        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        print(f"\n{'='*50}")
        print(f"[{num_formatado}] Acessando: {url}")
        driver.get(url)
        
        time.sleep(10) 
        
        print(f"[{num_formatado}] Rolando a página para disparar o Lazy-Load...")
        for i in range(1, 15):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/15});")
            time.sleep(1.5)
            
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        imagens = soup.find_all('img')
        
        imagens_baixadas = 0
        contador = 1
        
        print(f"[{num_formatado}] Mapeando as páginas...")
        for img in imagens:
            img_url = img.get('data-src') or img.get('data-lazy-src') or img.get('data-original') or img.get('src')
            
            if img_url and isinstance(img_url, str) and not img_url.startswith('data:image'):
                if 'googleusercontent' in img_url or 'uploads' in img_url:
                    if 'thumb' not in img_url.lower() and 'logo' not in img_url.lower():
                        nome_arquivo = f"{contador:02d}.jpg"
                        
                        # Log ANTES de baixar para você saber se ele não travou no download
                        print(f"  -> Baixando página {nome_arquivo}...", end=" ")
                        
                        try:
                            img_data = requests.get(img_url, verify=False, timeout=15).content
                            imagem_aberta = Image.open(io.BytesIO(img_data)).convert('RGB')
                            
                            caminho = os.path.join(pasta_destino, nome_arquivo)
                            imagem_aberta.save(caminho, 'JPEG')
                            
                            # Log DEPOIS de concluir
                            print(f"OK!") 
                            imagens_baixadas += 1
                            contador += 1
                        except Exception as e:
                            print(f"ERRO! Detalhe: {e}")

        # --- GERAÇÃO DO PDF PARA O CAPÍTULO ATUAL ---
        if imagens_baixadas > 0:
            print(f"\n[{num_formatado}] Download concluído. Carregando {imagens_baixadas} imagens na memória para o PDF...")
            arquivos = sorted([f for f in os.listdir(pasta_destino) if f.endswith('.jpg')])
            
            lista_imagens = []
            for idx, arquivo in enumerate(arquivos, 1):
                caminho_img = os.path.join(pasta_destino, arquivo)
                img = Image.open(caminho_img).convert('RGB')
                lista_imagens.append(img)
                
                # Feedback a cada 20 páginas processadas para saber que não travou
                if idx % 20 == 0:
                    print(f"  - Processando imagens para o PDF ({idx}/{imagens_baixadas})...")
                
            if lista_imagens:
                print(f"[{num_formatado}] Todas as imagens processadas. Salvando arquivo final (isso pode demorar uns minutos)...")
                lista_imagens[0].save(
                    nome_pdf, 
                    save_all=True, 
                    append_images=lista_imagens[1:]
                )
                print(f"[{num_formatado}] 🎉 SUCESSO! PDF gerado e salvo: {nome_pdf}")
        else:
            print(f"[{num_formatado}] Nenhuma imagem encontrada. Interrompendo loop para não gastar tempo de servidor.")
            driver.save_screenshot(f"debug_cap_{num_formatado}.png")
            break 

    print(f"\n{'='*50}")
    print("PROCESSO CONCLUÍDO PARA TODOS OS CAPÍTULOS SOLICITADOS!")

finally:
    driver.quit()