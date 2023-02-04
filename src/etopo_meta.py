
bbalp_names = {
    -1: 'alps-z612',
    0: 'alps0-Corse-Maures-Esterel', #'alps0-Cannes-Mimosas-Flayosc',
    1: 'alps1-Mercantour-Ubaye-Cuneese',
    2: 'alps2-Gap-Digne-Toulon-Apt',
    3: 'alps3-Vercors-Ecrins-Queyras-Cozie',
    # it3: Alpes Cozie (Cotiennes) ; Monviso
    4: 'alps4-Grenoble-Savoie-Susa-Lanzo-GParadiso',
    # Chartreuse, Belledonne, Grandes Rousses N, Arves N, Cerces N, Lauzière, Vanoise, Mont-Cenis
    # it4: Alpes Grées/Alpi Graie: Lanzo, Susa
    #5: 'alps5-Mont-Blanc-Leman-Cervino-Cogne'
    5 : 'alps5-Mont-Blanc-Chambery-Leman',
    # 6 : 'alps6-Aoste-Martigny-Gruyère',
    6 : 'alps6-Aoste-Martigny-Monch-MtRosa', # Aoste-Valais
    # it6: Gran Paradiso N, Cervino
    7: 'alps7-Ticino-Finsteraarhorn-Lorenzhorn', #  Ticino
    # 8: old: 'alps8-Como-Mesolcina-Adamello-Ortler',
    8: 'alps8-Lombardia-Como-StMoritz-Adamello', # (upper engadine)
    9: 'alps9-CHCW-Vaud-Luzern-Grimselpass',  
    # better:   Vaud-Berner-Oberland
    10: 'alps10-CHCE-Realp-Pfunds',
    # better:   Uri-Grisons-Realp-Pfunds
    11: 'alps11-CHNE-Zurich-LH-Lechtal',
    # better:   Zurich-Appenzell-LH-Vorarlberg
    12: 'alps12-Arco-Innsbruck-Bruneck-Marmolada',
    # better:   Tirol-Arco-Innsbruck-Bruneck-Marmolada
    13: 'alps13-Civetta--Unterwossen',
}


desct_fr = '''IGN Top 25 et Top 100 (2021). https://www.geoportail.gouv.fr'''
desct_it = '''Bugianen 2205 (2022) : Mappa escursionistica delle alpi piemontesi, valdostane e dintorni.
Per la legenda e l'origine dei dati visita <a href="https://tartamillo.wordpress.com/bugianen/'''
desct_ch = '''SwissTopo mix-scale (2021): Switzerland SwissTopo national map. https://map.geo.admin.ch
Unlike the website, this is a downscaled version when possible (1 zoom level up for each layer).'''
desct_ks = '''Kompass (2021). https://www.kompass.de/wanderkarte/'''

prefix = 'Carte topographique de la zone %s'

desc_fr = prefix + ': ' + desct_fr
desc_ch = prefix + ': ' + desct_ch
desc_ks = prefix + ': ' + desct_ks
desc_frit = f'''{prefix}, fusion de cartes IGN et Bugianen:
* {desct_fr}
* {desct_it}
'''
desc_fritch = desc_frit + desct_ch + '\n'
desc_fritch = f'''{prefix}, fusion de cartes IGN, Bugianen et SwissTopo:
* {desct_fr}
* {desct_it}
* {desct_ch}
'''
desc_itch = f'''{prefix}, fusion de cartes Bugianen et SwissTopo:
* {desct_it}
* {desct_ch}
'''
desc_chks = f'''{prefix}, fusion de cartes SwissTopo et Kompass:
* {desct_ch}
* {desct_ks}
'''
desc_frchks = f'''{prefix}, fusion de cartes IGN, SwissTopo et Kompass:
* {desct_fr}
* {desct_ch}
* {desct_ks}
'''


mbt2maps = {
    -1: 'frchks',
    0: 'fr',
    1: 'frit',
    2: 'fr',
    3: 'frit',
    4: 'fritch',
    5: 'fritch',
    6: 'fritch', # tiny fr in the W at z12
    7: 'itch',
    8: 'chks',
    9: 'ch',
    10: 'chks',  # tiny ks in the NW, z14-15
    11: 'chks',
    12: 'ks',  # TODO put CH z9,10,12 up to 10.8 - for z11 see etopo#2
    13: 'ks',
}

maps2desc = {
    'frchks': desc_frchks,
    'fr': desc_fr,
    'frit': desc_frit,
    'fritch': desc_fritch,
    'itch': desc_itch,
    'ch': desc_ch,
    'chks': desc_chks,
    'ks': desc_ks,
}

map2attrib = {
    'fr': '© <a href="https://geoservices.ign.fr/cgu-licences">IGN 2021</a>',
    'it': '© <a href="https://tartamillo.wordpress.com/bugianen/">CC BY-NC-SA 3.0 Maki</a>',
    'ch': '© <a href="https://shop.swisstopo.admin.ch/fr/geodonnees-gratuites">SwissTopo OGD</a>',
    'ks': '© <a href="https://www.kompass.de/b2b/lizenzen/">Kompass.de</a>',
}
def maps2attrib(maps):
    mcuts = [m for m in (maps[0:2], maps[2:4], maps[4:6], maps[6:8]) if m]
    return ' / '.join(map2attrib[m] for m in mcuts)

DESC = {i: maps2desc[mbt2maps[i]] % name for i, name in bbalp_names.items()}
ATTRIB = {i: maps2attrib(mbt2maps[i]) for i in bbalp_names}
