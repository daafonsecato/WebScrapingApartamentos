# %%
import numpy as np
import pandas as pd
import json
from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
import time
import datetime as dt
from time import sleep
from IPython.display import clear_output
import os
from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
import hashlib

# Function to compute the SHA256 hash of a content
def compute_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()

# Load existing hashes if the file exists, otherwise start with an empty set
hashes_file = 'page_hashes.txt'
existing_hashes = set()
if os.path.exists(hashes_file):
    with open(hashes_file, 'r') as f:
        existing_hashes = set(f.readlines())


def txt_to_links(text_file):
    with open(text_file, 'r', encoding="utf-8") as f:
        lista_aptos_raw = f.read()
    soup = BeautifulSoup(lista_aptos_raw, 'html.parser')
    data_raw = soup.find(attrs={"class": "Ul-sctud2-0 jyGHXP realestate-results-list browse-results-list"})
    data_raw = data_raw.find_all(attrs={"class": "sc-bdVaJa ebNrSm"})
    list_links = list()
    for data in data_raw:
        try:
            list_links.append('https://www.metrocuadrado.com'+data['href'])
        except: None
    out = list(set(list_links))

    print(f'{text_file}. Enlaces importados: {len(out)}')
    return out

def enlace_to_rowdf(enlace):
    new_row = dict()
    new_row['Código inmueble'] = 'UNASIG 000'
    new_row['Enlace'] = enlace
    obs_text = ''
    try:
        page = urlopen(enlace)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, 'html.parser')

        try:
            data_raw_1 = soup.find('title')
            new_row['Tipo'] = data_raw_1.text.split(' ')[2]
        except:
            obs_text = obs_text + 'sin info_2'

        try:
            data_raw_2 = soup.find('p', attrs={"class": "P-sc-31hrrf-0 hGwghD card-subtitle"})
            new_row['Sector'] = ', '.join(data_raw_2.text.split(',')[0].upper().replace('SECTOR ', '').replace(' Y ALREDEDORES', '').split(' Y '))
        except:
            obs_text = obs_text + 'sin info_2'

        try:
            data_raw_3 = soup.find('ul', attrs={"class": "Ul-sctud2-0 kdIYsW inline-list-grid list-feature-detail"})
            data_raw_3 = data_raw_3.find_all('li')
            new_row['Habitaciones'] = int(data_raw_3[1].text[0])
            new_row['Baños'] = int(data_raw_3[2].text[0])
            new_row['Estrato'] = int(data_raw_3[3].text[0])
        except:
            new_row['Habitaciones'] = np.NaN
            new_row['Baños'] = np.NaN
            new_row['Estrato'] = np.NaN
            obs_text = obs_text + ', '+ 'sin info_3'

        try:
            data_raw_4 = soup.find_all(attrs={"class": "Col-sc-14ninbu-0 lfGZKA mb-3 pb-1 col-12 col-lg-3"})
            for element in data_raw_4:
                if element.h3.text == 'Precio' or element.h3.text == 'Valor administración':
                    text = int(element.p.text[1:].replace('.', ''))
                elif element.h3.text == 'Área construida' or element.h3.text == 'Área privada':
                    text = float(element.p.text[:-2].replace(' ', ''))
                elif element.h3.text == 'Parqueaderos':
                    text = int(element.p.text)
                elif element.h3.text == 'Barrio común':
                    text = element.p.text.upper()
                else:
                    text = element.p.text
                new_row[element.h3.text] = text
        except:
            obs_text = obs_text + ', '+  'sin info_4'
            new_row['Observaciones'] = obs_text

        try:
            card_block = soup.find_all('div', attrs={"class": "card-block"})
            try:
                lista_interiores_raw = card_block[3].find_all('ul', attrs={"class": "Ul-sctud2-0 kdIYsW inline-list-grid"})
                lista_interiores = list()
                for item in lista_interiores_raw:
                    lista_interiores.append(item.text)
                new_row['Interiores'] = ', '.join(lista_interiores)
            except:
                obs_text = obs_text + ', '+  'sin info_5.1'
                new_row['Observaciones'] = obs_text

            try:
                lista_exteriores_raw = card_block[4].find_all('ul', attrs={"class": "Ul-sctud2-0 kdIYsW inline-list-grid"})
                lista_exteriores = list()
                for item in lista_exteriores_raw:
                    lista_exteriores.append(item.text)
                new_row['Exteriores'] = ', '.join(lista_exteriores)
            except:
                obs_text = obs_text + ', '+  'sin info_5.2'
                new_row['Observaciones'] = obs_text
            try:
                lista_zonascomunes_raw = card_block[5].find_all('ul', attrs={"class": "Ul-sctud2-0 kdIYsW inline-list-grid"})
                lista_zonascomunes = list()
                for item in lista_zonascomunes_raw:
                    lista_zonascomunes.append(item.text)
                new_row['Zonas comunes'] = ', '.join(lista_zonascomunes)
            except:
                obs_text = obs_text + ', '+  'sin info_5.3'
                new_row['Observaciones'] = obs_text
        except:
            obs_text = obs_text + ', '+  'sin info_5'
            new_row['Observaciones'] = obs_text

        try:
            box_2 = soup.find('script', attrs={"id": "__NEXT_DATA__"})
            try:
                # Ubbicación / posición de coordenadas
                new_row['Ubicacion'] = json.loads(box_2.get_text())['props']['initialState']['realestate']['basic']['coordinates']
            except:
                new_row['Ubicacion'] = {'lon': None, 'lat': None}
                obs_text = obs_text + ', '+  'ubicación no disponible'
                new_row['Observaciones'] = obs_text
            try:
                # Imagenes
                list_images = json.loads(box_2.get_text())['props']['initialState']['realestate']['basic']['images']
                new_list_img = list()
                for img in list_images:
                    new_list_img.append(img['image'])
                new_list_img
                new_row['lista_imagenes'] = new_list_img
            except:
                new_row['lista_imagenes'] = 'NoInfo'
                obs_text = obs_text + ', '+  'imágenes no disponible'
                new_row['Observaciones'] = obs_text
            lat = new_row['Ubicacion']['lat']
            lon = new_row['Ubicacion']['lon']
            if lat is not None:
                new_row['G_maps'] = f'https://www.google.com/maps/place/{lat},{lon}'
            else:
                new_row['G_maps'] = 'NoInfo'
        except:
            pass

        try:
            box_3 = soup.find('p', attrs={"class": "d-none d-md-block card-text"})
            new_row['Descripcion'] = box_3.text
        except:
            new_row['Descripcion'] = 'NoInfo'


    except:
        obs_text = 'Sin acceso a enlace'
    new_row['Observaciones'] = obs_text
    return new_row

def reposo(time2sleep, n):
    clear_output(wait=True)
    print(f'>> REPOSO DE {time2sleep} SEGUNDOS, APARTAMENTOS BUSCADOS: {n}')
    print('------------------------------------------')
    time.sleep(time2sleep)
    return None

columnas = ['Código inmueble', 'Tipo', 'Habitaciones', 'Baños', 'Estrato', 'Precio', 'Antigüedad',
            'Área construida', 'Área privada', 'Valor administración', 'Parqueaderos', 'Sector',
            'Barrio común', 'Ubicacion','G_maps', 'Descripcion', 'Interiores', 'Exteriores', 'Zonas comunes', 'Valor arriendo',
            'Enlace', 'lista_imagenes', 'Observaciones']

def enlaces_to_df(lista_enlaces, columnas=columnas, verbose=False, new=False, no_reposo=50, seg_reposo=30):
    """
    dataframe
    lista enlaces
    bath_size
    """
    if len(lista_enlaces) < no_reposo:
        no_reposo = len(lista_enlaces)
        seg_reposo = 1
    lista_dict_aptos = list()
    if not new: df_aptos = pd.read_excel('main_aptos.xlsx')
    else: df_aptos = pd.DataFrame(columns=columnas)
    n = 0
    for enlace in lista_enlaces:
        cod = enlace.split('/')[-1]
        if cod not in list(df_aptos['Código inmueble']):
            print(f'{n+1}: {cod}')
            new_row = enlace_to_rowdf(enlace) # diccionario
            if verbose: print(new_row)
            print('--------')
            lista_dict_aptos.append(new_row)
            time.sleep(0.5)
            # cod = new_row['Código inmueble']
            n += 1
            if n % no_reposo == 0:
                if verbose: print(f'{n} apartamentos agregados')
                df_dict_aptos=pd.DataFrame(lista_dict_aptos)
                df_aptos = pd.concat([df_aptos, df_dict_aptos])
                df_aptos.drop_duplicates(subset=['Código inmueble'], keep='last', inplace=True)
                if verbose:
                    df_aptos.to_excel(dt.datetime.now().strftime('%Y%m%d_%H%M')+'_aptos'+'.xlsx', index=False) # checkpoint excel
                df_aptos.to_excel('main_aptos.xlsx', index=False) # sobreescribe principal
                reposo(seg_reposo, n) # descanso

        else:
            print(f'{cod} ya existe en base')

    print(f'FINALIZADO: {n} apartamentos agregados')
    df_aptos.to_excel(dt.datetime.now().strftime('%Y%m%d_%H%M')+'_aptos'+'.xlsx', index=False)
    # df_aptos.to_excel('main_aptos.xlsx', index=False)
    return df_aptos
browser = webdriver.Edge(EdgeChromiumDriverManager().install())
url = 'https://www.metrocuadrado.com/?search=form'
browser.get(url)
browser.maximize_window()
sleep(2)

filtro_tipo_inmueble = browser.find_elements(By.CLASS_NAME, "m2-select__control")[0]
actions_tipo_inmueble = ActionChains(browser)
actions_tipo_inmueble.send_keys_to_element(filtro_tipo_inmueble, Keys.ARROW_RIGHT)
actions_tipo_inmueble.send_keys(Keys.ARROW_DOWN)
actions_tipo_inmueble.send_keys(Keys.SPACE)
actions_tipo_inmueble.send_keys(Keys.ARROW_DOWN)
actions_tipo_inmueble.send_keys(Keys.SPACE)
actions_tipo_inmueble.perform()
sleep(2)

filtro_estado = browser.find_elements(By.CLASS_NAME, "m2-select__control")[1]
actions_filtro_estado = ActionChains(browser)
actions_filtro_estado.send_keys_to_element(filtro_estado, Keys.ARROW_RIGHT)
actions_filtro_estado.send_keys(Keys.ARROW_DOWN)
actions_filtro_estado.send_keys(Keys.ARROW_DOWN)
actions_filtro_estado.send_keys(Keys.TAB)
actions_filtro_estado.perform()
sleep(2)

selecting_city = browser.find_element(By.NAME, "location")
selecting_city.send_keys("Bogo")
sleep(1)

actions_selecting_city = ActionChains(browser)
actions_selecting_city.send_keys_to_element(selecting_city, Keys.ARROW_RIGHT)
actions_selecting_city.send_keys(Keys.ARROW_DOWN)
actions_selecting_city.send_keys(Keys.ARROW_DOWN)
actions_selecting_city.send_keys(Keys.ENTER)
actions_selecting_city.perform()
sleep(6)

ordenar = browser.find_elements(By.CLASS_NAME, "m2-select__control")[2]
actions = ActionChains(browser)
actions.send_keys_to_element(ordenar, Keys.ARROW_RIGHT)
actions.send_keys(Keys.ARROW_DOWN)
actions.send_keys(Keys.ARROW_DOWN)
actions.send_keys(Keys.ENTER)
actions.perform()
# %%
run = True
pag = 1
while run:
    html = browser.page_source
    content_hash = compute_hash(html)
    
    # Only save the page content if its hash is not in the existing_hashes set
    if content_hash not in existing_hashes:
        date_name = dt.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        name_file = f'temporal_inmuebles_{date_name}.txt'
        with open(f'data_raw/{name_file}', 'w', encoding="utf-8") as file:
            file.write(html)
            print(f'Página {pag} exportada y guardada')
            existing_hashes.add(content_hash)
    else:
        print(f'Página {pag} already scraped and saved previously')

    pag += 1
    sleep(1)
    try:
        browser.find_element(By.CLASS_NAME, "item-icon-next").click()
        sleep(4)
    except:
        print(f'Proceso terminado, páginas agregadas: {pag-1}')
        run = False

# Save the updated set of hashes
with open(hashes_file, 'w') as f:
    for h in existing_hashes:
        f.write(h + '\\n')
# TODO: Terminar el proceso, por ahora sigue indefinidamente cargando la última página
# run = True
# pag = 1
# while run:
#     html = browser.page_source
#     date_name = dt.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
#     name_file = f'temporal_inmuebles_{date_name}.txt'
#     with open(f'data_raw/{name_file}', 'w', encoding="utf-8") as file:
#         file.write(html)
#         print(f'Página {pag} exportada y guardada')
#     pag += 1
#     sleep(1)
#     try:
#         browser.find_element(By.CLASS_NAME, "item-icon-next").click()
#         sleep(4)
#     except:
#         print(f'Proceso terminado, páginas agregadas: {pag-1}')
#         run = False
path = "./data_raw"
dir_list = os.listdir(path)

lista_enlaces = list()
for doc in dir_list:
    out = txt_to_links(f'{path}/{doc}')
    lista_enlaces.append(out)
lista_enlaces = [item for sublist in lista_enlaces for item in sublist]
print(f'Total enlaces: {len(lista_enlaces)}')
lista_enlaces = list(dict.fromkeys(lista_enlaces))
print(f'Eliminando enlaces duplicados...\n'
      f'Total enlaces: {len(lista_enlaces)}')
enlaces_to_df(lista_enlaces, new=False, verbose=False)
# %%
