##############################################################################
###                   DUAL SNAKE - Baseado no Python Crash                 ###
##############################################################################
### Arquitetura do Jogo:                                                   ###
### - Duas cobras controláveis simultaneamente (WASD e Setas)              ###
### - 5 fases progressivas com aumento de velocidade e obstáculos (bombas) ###
### - Mecânica de "Slither.io": cobras mortas viram orbs de pontuação      ###
### - Sistema de áudio híbrido (arquivos .mp3 e síntese via Numpy)         ###
### - Renderização em Grid (Células de 20px) com fallback de sprites       ###
##############################################################################

import pygame
import sys
import random
import numpy as np
import os

# =============================================================================
# BLOCO 1: INICIALIZAÇÃO E CONFIGURAÇÕES GERAIS
# =============================================================================
# Inicializa os subsistemas fundamentais do Pygame (Vídeo, Fontes e Áudio)
# O buffer de áudio é configurado em 512 para reduzir o atraso (latency) dos efeitos sonoros
pygame.init()
pygame.font.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Configurações da Janela Principal
LARGURA_TELA = 1200
ALTURA_TELA = 700
TITULO = "Dual Snake"

# --- Paleta de Cores (Padrão RGB) ---
# Definimos constantes de cores para facilitar a manutenção e manter a consistência visual
COR_FUNDO = (18, 24, 38)
COR_GRADE = (60, 80, 60)
COR_TEXTO = (220, 228, 240)
COR_TEXTO_DIM = (90, 110, 140)
COR_PAINEL = (12, 18, 30)

# Cores da Cobra 1 (Player 1 - Zumbi)
COR_CAB1 = (220, 50, 50)
COR_COR1 = (160, 30, 30)
COR_CAB1_MORTA = (80, 40, 40)

# Cores da Cobra 2 (Player 2 - Esqueleto)
COR_CAB2 = (50, 120, 220)
COR_COR2 = (30, 70, 160)
COR_CAB2_MORTA = (40, 50, 80)

# Cores dos Itens e Obstáculos no mapa
COR_MACA = (210, 60, 60)
COR_MACA_DEST = (240, 100, 80)
COR_BANANA = (220, 190, 30)
COR_BANANA_DEST = (255, 220, 50)
COR_BOMBA = (200, 60, 80)
COR_BOMBA_CENTRO = (255, 120, 80)

# Cores das orbs geradas quando uma cobra morre (Mecânica de recompensa)
COR_MORTE_C1 = (220, 100, 50)
COR_MORTE_C2 = (80, 180, 255)

# Efeito estroboscópico utilizado exclusivamente no background da Fase 5 (Fase Final)
CORES_STROBO = [(180, 40, 40), (40, 100, 200), (40, 160, 80), (180, 160, 30)]
VELOCIDADE_STROBO = 180

# --- Lógica de Grid (Malha Espacial) ---
# O jogo não usa coordenadas de pixel contínuas, mas sim uma malha discreta.
# Isso simplifica o cálculo de colisões (AABB) garantindo que as cobras andem em "blocos".
TAM = 20
COLS = LARGURA_TELA // TAM  # Total de colunas: 60
LINHAS = ALTURA_TELA // TAM  # Total de linhas: 35

# Criação da superfície principal de desenho e limitador de frames
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption(TITULO)
relogio = pygame.time.Clock()

# --- Gerenciamento de Telas e Menu ---
_menu_bg = None
_menu_livro = None
_menu_ativo = True  # Flag de controle de estado: True = no menu, False = em jogo

_gameover_bg = None


def _carregar_menu():
    """
    Carrega as imagens de fundo e assets visuais da interface do usuário.
    Utiliza caminhos relativos absolutos (os.path) para evitar erros de diretório
    quando o script é executado a partir de terminais diferentes.
    """
    global _menu_bg, _menu_livro, _gameover_bg
    base = os.path.dirname(os.path.abspath(__file__))
    p_bg = os.path.join(base, "assets/pngs/menu_bg_scaled.png")
    p_liv = os.path.join(base, "assets/pngs/livro_mc_scaled.png")
    p_go = os.path.join(base, "assets/pngs/gameover_bg_scaled.png")

    if os.path.exists(p_bg):
        _menu_bg = pygame.image.load(p_bg).convert()
    if os.path.exists(p_liv):
        _menu_livro = pygame.image.load(p_liv).convert_alpha()
    if os.path.exists(p_go):
        _gameover_bg = pygame.image.load(p_go).convert()


_carregar_menu()

# Fontes utilizadas no jogo
fonte_livro_titulo = pygame.font.SysFont("Consolas", 13, bold=True)
fonte_livro_corpo = pygame.font.SysFont("Consolas", 15)
fonte_livro_rodape = pygame.font.SysFont("Consolas", 12)
fonte_hud = pygame.font.SysFont("Consolas", 18, bold=True)
fonte_fase = pygame.font.SysFont("Consolas", 14)
fonte_big = pygame.font.SysFont("Consolas", 42, bold=True)
fonte_med = pygame.font.SysFont("Consolas", 22, bold=True)


def desenhar_menu(surface):
    """Renderiza a tela inicial do jogo, incluindo título, overlays e instruções de controle."""
    if _menu_bg:
        surface.blit(_menu_bg, (0, 0))
    else:
        surface.fill((30, 80, 40))

    # Overlay escuro suave para melhorar o contraste do texto com o fundo
    ov = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 100))
    surface.blit(ov, (0, 0))

    # Desenho do Título principal com sombreamento para efeito de profundidade
    cx = LARGURA_TELA // 2
    t_titulo = fonte_big.render("DUAL SNAKE", True, (255, 255, 255))
    sombra = fonte_big.render("DUAL SNAKE", True, (0, 0, 0))
    surface.blit(sombra, (cx - t_titulo.get_width() // 2 + 3, ALTURA_TELA // 2 - 120 + 3))
    surface.blit(t_titulo, (cx - t_titulo.get_width() // 2, ALTURA_TELA // 2 - 120))

    # Tabela de Controles
    fonte_ctrl = pygame.font.SysFont("Consolas", 20, bold=True)
    linhas_ctrl = [
        ("WASD", "Cobra 1  (Zumbi)"),
        ("Setas", "Cobra 2  (Esqueleto)"),
    ]
    for i, (tecla, desc) in enumerate(linhas_ctrl):
        t_tecla = fonte_ctrl.render(f"[ {tecla} ]", True, (255, 220, 60))
        t_desc = fonte_ctrl.render(desc, True, (220, 220, 220))
        y = ALTURA_TELA // 2 - 40 + i * 36
        surface.blit(t_tecla, (cx - 160, y))
        surface.blit(t_desc, (cx - 40, y))

    # Lógica para o texto "Pressione qualquer tecla" piscar na tela baseada em ticks do sistema
    t = pygame.time.get_ticks()
    if (t // 600) % 2 == 0:
        rod = fonte_med.render("Pressione qualquer tecla para iniciar", True, (255, 255, 180))
        srod = fonte_med.render("Pressione qualquer tecla para iniciar", True, (0, 0, 0))
        surface.blit(srod, (cx - rod.get_width() // 2 + 2, ALTURA_TELA // 2 + 80 + 2))
        surface.blit(rod, (cx - rod.get_width() // 2, ALTURA_TELA // 2 + 80))


# --- Gerenciamento de Áudio ---
def _carregar_som(nome_arquivo, volume):
    """Tenta carregar um arquivo de áudio. Retorna um objeto Sound ou None se falhar, evitando crashes."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_arquivo)
    if os.path.exists(caminho):
        try:
            s = pygame.mixer.Sound(caminho)
            s.set_volume(volume)
            return s
        except Exception as e:
            print(f"[SOM] Erro ao carregar {nome_arquivo}: {e}")
            return None
    print(f"[SOM] Arquivo não encontrado: {caminho}")
    return None


pygame.mixer.set_num_channels(8)  # Aumenta os canais simultâneos para evitar interrupções de som
SOM_MORTE = _carregar_som("assets/sons/som_morte.mp3", 0.8)
SOM_COMER = _carregar_som("assets/sons/som_comer.mp3", 0.3)
SOM_ANDAR = _carregar_som("assets/sons/som_andar.mp3", 0.06)

# Canais dedicados garantem que sons importantes não cortem uns aos outros
CANAL_MORTE = pygame.mixer.Channel(0)
CANAL_COMER = pygame.mixer.Channel(1)
CANAL_ANDAR = pygame.mixer.Channel(2)


def tocar_morte():
    if SOM_MORTE:
        CANAL_MORTE.stop()
        CANAL_MORTE.play(SOM_MORTE)


def tocar_comer():
    if SOM_COMER:
        CANAL_COMER.stop()
        CANAL_COMER.play(SOM_COMER)


def tocar_andar():
    if SOM_ANDAR and not CANAL_ANDAR.get_busy():
        CANAL_ANDAR.play(SOM_ANDAR, loops=-1)


def parar_andar():
    CANAL_ANDAR.stop()


# --- Gerador de Ondas Sonoras Sintetizadas (Matemática Computacional) ---
def _gerar_tom(freq, duracao, volume=0.5, sample_rate=44100, forma='quadrada'):
    """Gera um array numpy representando um som simples e o converte para um Sound do Pygame."""
    t = np.linspace(0, duracao, int(sample_rate * duracao), False)
    if forma == 'quadrada':
        onda = np.sign(np.sin(2 * np.pi * freq * t))
    elif forma == 'triangular':
        onda = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    else:
        onda = np.sin(2 * np.pi * freq * t)

    # Envelope ADSR simplificado (Fade in/Fade out) para evitar "estalos" nas caixas de som
    env = np.ones_like(onda)
    fade = int(sample_rate * 0.01)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)

    onda = (onda * env * volume * 32767).astype(np.int16)
    stereo = np.column_stack([onda, onda])
    return pygame.sndarray.make_sound(stereo)


def _gerar_sequencia(notas, volume=0.5, forma='quadrada'):
    """Concatena vários tons numa sequência matemática para formar jingles retrô."""
    sample_rate = 44100
    partes = []
    for freq, dur in notas:
        t = np.linspace(0, dur, int(sample_rate * dur), False)
        if forma == 'quadrada':
            onda = np.sign(np.sin(2 * np.pi * freq * t))
        elif forma == 'triangular':
            onda = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        else:
            onda = np.sin(2 * np.pi * freq * t)
        fade = int(sample_rate * 0.008)
        env = np.ones_like(onda)
        if len(env) > fade * 2:
            env[:fade] = np.linspace(0, 1, fade)
            env[-fade:] = np.linspace(1, 0, fade)
        onda = (onda * env * volume * 32767).astype(np.int16)
        partes.append(onda)
    combined = np.concatenate(partes)
    stereo = np.column_stack([combined, combined])
    return pygame.sndarray.make_sound(stereo)


# Jingles do sistema gerados em tempo de execução
_notas_gameover = [(494, 0.15), (440, 0.15), (392, 0.15), (349, 0.15), (330, 0.15), (294, 0.20), (262, 0.40)]
SOM_GAMEOVER = _gerar_sequencia(_notas_gameover, volume=0.25, forma='quadrada')

_notas_fase = [(330, 0.08), (392, 0.08), (494, 0.08), (523, 0.08), (587, 0.08), (659, 0.08), (784, 0.08), (880, 0.20),
               (784, 0.06), (880, 0.25)]
SOM_PASSOU_FASE = _gerar_sequencia(_notas_fase, volume=0.25, forma='triangular')

CANAL_GAMEOVER = pygame.mixer.Channel(3)
CANAL_PASSOU = pygame.mixer.Channel(4)

SOM_TNT = _carregar_som("assets/sons/som_tnt.mp3", 0.7)
CANAL_TNT = pygame.mixer.Channel(5)


def tocar_tnt():
    if SOM_TNT:
        CANAL_TNT.stop()
        CANAL_TNT.play(SOM_TNT)


# --- Gestão Dinâmica da Música de Fundo ---
_fase_musica_atual = None


def _iniciar_musica_fase(fase):
    """Altera a trilha sonora dependendo da progressão do jogador."""
    global _fase_musica_atual
    if fase == _fase_musica_atual:
        return
    _fase_musica_atual = fase
    pygame.mixer.music.stop()
    _base = os.path.dirname(os.path.abspath(__file__))
    if fase == 5:
        caminho = os.path.join(_base, "assets/musicas/musica_fase5.mp3")
    else:
        caminho = os.path.join(_base, "assets/musicas/musica_fases1_4.mp3")
    if os.path.exists(caminho):
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(0.18 if fase < 5 else 0.45)
        pygame.mixer.music.play(-1)


def _iniciar_musica_menu():
    global _fase_musica_atual
    if _fase_musica_atual == "menu":
        return
    _fase_musica_atual = "menu"
    pygame.mixer.music.stop()
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/musicas/musica_menu.mp3")
    if os.path.exists(caminho):
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)


def _parar_musica():
    global _fase_musica_atual
    pygame.mixer.music.stop()
    _fase_musica_atual = None


def tocar_gameover():
    CANAL_GAMEOVER.stop()
    CANAL_GAMEOVER.play(SOM_GAMEOVER)


def tocar_passou_fase():
    CANAL_PASSOU.stop()
    CANAL_PASSOU.play(SOM_PASSOU_FASE)


# --- Gerenciamento Visual: Carregamento de Sprites ---
def _carregar_sprite(nome, tamanho):
    """Carrega uma imagem com transparência alfa e redimensiona para a malha do jogo."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome)
    if os.path.exists(caminho):
        try:
            img = pygame.image.load(caminho).convert_alpha()
            return pygame.transform.scale(img, (tamanho, tamanho))
        except Exception as e:
            print(f"[SPRITE] Erro ao carregar {nome}: {e}")
            return None
    print(f"[SPRITE] Não encontrado: {caminho}")
    return None


SPRITE_COOKIE = _carregar_sprite("assets/pngs/cookie_16.png", TAM - 2)

# Sprites P1
SP1_CABECA = _carregar_sprite("assets/pngs/p1_cabeca_20.png", TAM)
SP1_CORPOS = [
    _carregar_sprite("assets/pngs/p1_corpo1_20.png", TAM),
    _carregar_sprite("assets/pngs/p1_corpo2_20.png", TAM),
    _carregar_sprite("assets/pngs/p1_corpo3_20.png", TAM),
    _carregar_sprite("assets/pngs/p1_corpo4_20.png", TAM),
    _carregar_sprite("assets/pngs/p1_corpo5_20.png", TAM),
]

# Sprites P2
SP2_CABECA = _carregar_sprite("assets/pngs/p2_cabeca_20.png", TAM)
SP2_CORPOS = [
    _carregar_sprite("assets/pngs/p2_corpo1_20.png", TAM),
    _carregar_sprite("assets/pngs/p2_corpo2_20.png", TAM),
    _carregar_sprite("assets/pngs/p2_corpo3_20.png", TAM),
    _carregar_sprite("assets/pngs/p2_corpo4_20.png", TAM),
]
SPRITE_ESTRELA = _carregar_sprite("assets/pngs/estrela_16.png", TAM - 2)
SPRITE_TNT = _carregar_sprite("assets/pngs/tnt_32.png", 32)
SPRITE_CORACAO = _carregar_sprite("assets/pngs/coracao_22.png", 22)

# Carregamento de Backgrounds baseados nas Fases
_bg_dir = os.path.dirname(os.path.abspath(__file__))
BACKGROUNDS = {}
for _i in range(1, 6):
    _path = os.path.join(_bg_dir, f"assets/pngs/bg_fase{_i}_scaled.png")
    if os.path.exists(_path):
        _surf = pygame.image.load(_path).convert()
        BACKGROUNDS[_i] = _surf
    else:
        BACKGROUNDS[_i] = None

# =============================================================================
# BLOCO 2: CONFIGURAÇÃO DE BALANÇEAMENTO DAS FASES
# =============================================================================
# Dicionário contendo as configurações de dificuldade de cada fase.
# - fps: Dita a velocidade do game loop (e quão rápida a cobra anda)
# - media_bombas: Base para a distribuição de Poisson ao gerar bombas.
# - tempo_item: Milissegundos até as frutas rotacionarem.
# - delay_respawn: Tempo de punição até a cobra morta renascer.
CONFIG_FASES = {
    1: {"fps": 6, "media_bombas": 1, "tempo_item": 6000, "meta_score": 15, "max_frutas": 4, "delay_respawn": 5000},
    2: {"fps": 9, "media_bombas": 2, "tempo_item": 5000, "meta_score": 35, "max_frutas": 6, "delay_respawn": 10000},
    3: {"fps": 12, "media_bombas": 3, "tempo_item": 4500, "meta_score": 60, "max_frutas": 6, "delay_respawn": 15000},
    4: {"fps": 15, "media_bombas": 4, "tempo_item": 4000, "meta_score": 90, "max_frutas": 8, "delay_respawn": 20000},
    5: {"fps": 21, "media_bombas": 6, "tempo_item": 3500, "meta_score": None, "max_frutas": 8, "delay_respawn": 25000},
}
FASE_MAXIMA = 5

# =============================================================================
# BLOCO 3: VARIÁVEIS DE ESTADO GLOBAL DO JOGO
# =============================================================================
score = 0
vidas = 3
fase_atual = 1
som_gameover_tocado = False
proximo_bonus_vida = 50

# Estruturas de dados responsáveis por gerenciar entidades no mapa
lista_frutas = []  # Tuplas no formato: (x, y, tipo)
lista_frutas_morte = []  # Quando a cobra morre, o corpo vira orbs aqui
lista_bombas = []  # Tuplas: (x, y) com posições das armadilhas
momento_geracao = 0


# =============================================================================
# BLOCO 4: CLASSES (POO) - ENTIDADE COBRA
# =============================================================================
class Cobra:
    """
    Classe que gerencia o estado lógico, visual e mecânico de uma Cobra no jogo.
    Utiliza listas de coordenadas (X, Y) para representar a "cauda", onde o índice 0
    é sempre a cabeça.
    """

    def __init__(self, cx, cy, dir_x, dir_y, cor_cab, cor_cor, cor_morta, nome,
                 sprite_cabeca=None, sprite_corpos=None):
        self.cor_cab = cor_cab
        self.cor_cor = cor_cor
        self.cor_morta = cor_morta
        self.nome = nome
        self.sprite_cabeca = sprite_cabeca
        self.sprite_corpos = sprite_corpos
        self.viva = True
        self._spawn(cx, cy, dir_x, dir_y)

    def _spawn(self, cx, cy, dir_x, dir_y):
        """Inicializa ou reseta a cobra no mapa, definindo 3 segmentos iniciais."""
        self.dir_x = dir_x
        self.dir_y = dir_y
        x = cx * TAM
        y = cy * TAM
        self.corpo = [
            [x, y],
            [x - dir_x * TAM, y - dir_y * TAM],
            [x - dir_x * TAM * 2, y - dir_y * TAM * 2],
        ]
        self.viva = True

    def cabeca(self):
        """Retorna a coordenada atual da cabeça para verificação de colisões."""
        return self.corpo[0]

    def proxima_cabeca(self):
        """Calcula o vetor da próxima posição matemática baseada na direção atual."""
        return [self.corpo[0][0] + self.dir_x * TAM,
                self.corpo[0][1] + self.dir_y * TAM]

    def mover(self, crescer=False):
        """
        Executa a lógica de locomoção. Insere a nova cabeça no início da lista.
        Se a flag 'crescer' for Falsa, remove a ponta da cauda. Se Verdadeira,
        mantém a cauda, simulando o crescimento.
        """
        nova = self.proxima_cabeca()
        self.corpo.insert(0, nova)
        if not crescer:
            self.corpo.pop()

    def mudar_direcao(self, dx, dy):
        """Filtra inputs para evitar que a cobra inverta 180 graus de uma vez (suicídio)."""
        if self.dir_x != 0 and dx != 0:
            return
        if self.dir_y != 0 and dy != 0:
            return
        self.dir_x = dx
        self.dir_y = dy

    def desenhar(self, superficie):
        """Responsável por renderizar dinamicamente a cabeça e cada segmento lógico do corpo."""
        for i, parte in enumerate(self.corpo):
            if i == 0:
                # --- CABEÇA ---
                if self.viva and self.sprite_cabeca:
                    # Rotação da matriz de pixels dependendo do vetor direcional
                    if self.dir_x == 1:
                        angulo = 270
                    elif self.dir_x == -1:
                        angulo = 90
                    elif self.dir_y == -1:
                        angulo = 0
                    else:
                        angulo = 180
                    rot = pygame.transform.rotate(self.sprite_cabeca, angulo)
                    superficie.blit(rot, (parte[0], parte[1]))
                else:
                    cor = self.cor_cab if self.viva else self.cor_morta
                    r = pygame.Rect(parte[0] + 1, parte[1] + 1, TAM - 2, TAM - 2)
                    pygame.draw.rect(superficie, cor, r, border_radius=4)
                    if self.viva:
                        ex, ey = parte[0], parte[1]
                        if self.dir_x == 1:
                            olhos = [(ex + TAM - 5, ey + 4), (ex + TAM - 5, ey + TAM - 6)]
                        elif self.dir_x == -1:
                            olhos = [(ex + 3, ey + 4), (ex + 3, ey + TAM - 6)]
                        elif self.dir_y == -1:
                            olhos = [(ex + 4, ey + 3), (ex + TAM - 6, ey + 3)]
                        else:
                            olhos = [(ex + 4, ey + TAM - 5), (ex + TAM - 6, ey + TAM - 5)]
                        for ox, oy in olhos:
                            pygame.draw.circle(superficie, (240, 240, 240), (ox, oy), 2)
            else:
                # --- CORPO ---
                if self.viva and self.sprite_corpos:
                    sp = self.sprite_corpos[i % len(self.sprite_corpos)]
                    if sp:
                        superficie.blit(sp, (parte[0], parte[1]))
                        continue
                cor = self.cor_cor if self.viva else self.cor_morta
                margem = 3
                r = pygame.Rect(parte[0] + margem, parte[1] + margem,
                                TAM - margem * 2, TAM - margem * 2)
                pygame.draw.rect(superficie, cor, r, border_radius=2)


# =============================================================================
# BLOCO 5: REGRAS DE NEGÓCIO E MECÂNICAS
# =============================================================================
def posicoes_ocupadas():
    """Retorna um Set iterável de todas as posições atualmente ocupadas pelo corpo das cobras, para impedir spawns em cima do jogador."""
    ocupadas = set()
    for p in cobra1.corpo: ocupadas.add(tuple(p))
    for p in cobra2.corpo: ocupadas.add(tuple(p))
    return ocupadas


def gerar_posicao_aleatoria():
    """Gera um par de coordenadas garantindo que estará alinhado à Grid (múltiplo de TAM)."""
    ocupadas = posicoes_ocupadas()
    for _ in range(500):
        x = random.randint(0, COLS - 1) * TAM
        y = random.randint(0, LINHAS - 1) * TAM
        if (x, y) not in ocupadas:
            return x, y
    return 0, 0


def spawnar_itens():
    """Distribui frutas e obstáculos pela arena utilizando a configuração de dificuldade da fase."""
    global lista_frutas, lista_bombas, momento_geracao
    momento_geracao = pygame.time.get_ticks()
    media_bombas = CONFIG_FASES[fase_atual]["media_bombas"]
    max_frutas = CONFIG_FASES[fase_atual]["max_frutas"]

    lista_frutas = []
    for _ in range(max_frutas):
        pos = gerar_posicao_aleatoria()
        tipo = random.choice(["maca", "banana"])
        lista_frutas.append((pos[0], pos[1], tipo))

    # Algoritmo de Distribuição de Poisson para variabilidade imprevisível da quantidade de bombas
    qtd_bombas = int(np.random.poisson(media_bombas))
    lista_bombas = []
    for _ in range(qtd_bombas):
        lista_bombas.append(gerar_posicao_aleatoria())


def reiniciar_cobras():
    cobra1._spawn(COLS // 3, LINHAS // 2 + 2, 1, 0)
    cobra2._spawn(COLS * 2 // 3 - 3, LINHAS // 2 + 2, -1, 0)


def aplicar_morte(cobra, motivo, penalidade_score=0, tocar_som=True):
    """
    Controlador de Mortes. Subtrai a pontuação de penalidade e invoca a mecânica
    'Slither.io' iterando sobre o corpo destruído para gerar itens coletáveis.
    """
    global score, vidas, lista_frutas_morte
    cobra.viva = False
    score = max(0, score - penalidade_score)
    print(f"[MORTE] {cobra.nome} — {motivo} | vidas: {vidas}")
    if tocar_som:
        tocar_morte()

    tipo_morte = "morte_c1" if cobra is cobra1 else "morte_c2"
    for i, parte in enumerate(cobra.corpo):
        pontos = 1
        lista_frutas_morte.append((parte[0], parte[1], tipo_morte, pontos))
    cobra.corpo = []  # Exclui referências do corpo no mapa (Limpador de Lixo Virtual)


def verificar_game_over():
    """Verifica se não sobrou nenhuma cobra no campo, decretando a perda de uma vida."""
    global vidas
    if not cobra1.viva and not cobra2.viva:
        vidas -= 1
        if vidas > 0:
            reiniciar_cobras()
            spawnar_itens()
    elif not cobra1.viva or not cobra2.viva:
        pass


def ressuscitar_cobras_mortas():
    """Restaura o player morto individualmente sem parar a partida se o outro ainda estiver vivo."""
    global lista_frutas_morte
    if not cobra1.viva and cobra2.viva:
        cobra1._spawn(COLS // 3, LINHAS // 2 + 2, 1, 0)
        lista_frutas_morte = [f for f in lista_frutas_morte if f[2] != "morte_c1"]
    if not cobra2.viva and cobra1.viva:
        cobra2._spawn(COLS * 2 // 3 - 3, LINHAS // 2 + 2, -1, 0)
        lista_frutas_morte = [f for f in lista_frutas_morte if f[2] != "morte_c2"]


# =============================================================================
# BLOCO 6: RENDERIZAÇÃO DE ITENS E INTERFACE (HUD)
# =============================================================================
def desenhar_maca(surface, pos):
    """Desenha o sprite nativo ou cria geometria primitiva como Fallback."""
    x, y = pos
    if SPRITE_COOKIE:
        surface.blit(SPRITE_COOKIE, (x + 1, y + 1))
    else:
        cx, cy = x + TAM // 2, y + TAM // 2
        r = TAM // 2 - 2
        pygame.draw.circle(surface, COR_MACA, (cx, cy + 1), r)
        pygame.draw.circle(surface, COR_MACA_DEST, (cx - 2, cy - 2), r // 2)
        pygame.draw.line(surface, (80, 120, 40), (cx, cy - r), (cx + 2, cy - r - 4), 2)


def desenhar_banana(surface, pos):
    x, y = pos
    if SPRITE_ESTRELA:
        surface.blit(SPRITE_ESTRELA, (x + 1, y + 1))
    else:
        cx, cy = x + TAM // 2, y + TAM // 2
        pontos = []
        for i in range(10):
            t = i / 9
            bx = int(x + 3 + t * (TAM - 6))
            by = int(cy + (TAM // 2 - 4) * (1 - 4 * (t - 0.5) ** 2))
            pontos.append((bx, by))
        if len(pontos) > 1:
            pygame.draw.lines(surface, COR_BANANA, False, pontos, 5)
            pygame.draw.lines(surface, COR_BANANA_DEST, False, pontos[:7], 2)


def desenhar_bomba(surface, pos):
    """Utiliza interpolação de tempo para criar uma animação de piscar nas bombas."""
    x, y = pos
    if SPRITE_TNT:
        offset = (TAM - 32) // 2  # Deslocamento matemático para centralização
        t = pygame.time.get_ticks()
        if (t // 300) % 2 == 0:
            surface.blit(SPRITE_TNT, (x + offset, y + offset))
        else:
            tmp = SPRITE_TNT.copy()
            tmp.fill((40, 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(tmp, (x + offset, y + offset))
    else:
        cx, cy = x + TAM // 2, y + TAM // 2 + 1
        r = TAM // 2 - 3
        pygame.draw.circle(surface, (50, 50, 50), (cx, cy), r)
        pygame.draw.circle(surface, COR_BOMBA, (cx, cy), r - 1)
        pygame.draw.circle(surface, COR_BOMBA_CENTRO, (cx - 2, cy - 2), r // 3)
        pygame.draw.line(surface, (180, 140, 60), (cx, cy - r), (cx + 4, cy - r - 5), 2)
        t = pygame.time.get_ticks()
        if (t // 200) % 2 == 0:
            pygame.draw.circle(surface, (255, 220, 50), (cx + 4, cy - r - 5), 2)


def desenhar_orb_morte(surface, pos, tipo):
    """Renderiza a orb estática com feedback visual de pulso oscilatório atrelado ao clock."""
    x, y = pos
    cx, cy = x + TAM // 2, y + TAM // 2
    r = TAM // 2 - 4
    cor_base = COR_MORTE_C1 if tipo == "morte_c1" else COR_MORTE_C2
    cor_brilho = (255, 200, 150) if tipo == "morte_c1" else (180, 230, 255)

    t = pygame.time.get_ticks()
    pulso = abs((t % 600) - 300) / 300
    r_atual = max(2, int(r * (0.8 + 0.2 * pulso)))
    pygame.draw.circle(surface, cor_base, (cx, cy), r_atual)
    pygame.draw.circle(surface, cor_brilho, (cx - 1, cy - 1), max(1, r_atual // 3))


def desenhar_grade(surface):
    for col in range(0, LARGURA_TELA, TAM):
        pygame.draw.line(surface, COR_GRADE, (col, 0), (col, ALTURA_TELA))
    for lin in range(0, ALTURA_TELA, TAM):
        pygame.draw.line(surface, COR_GRADE, (0, lin), (LARGURA_TELA, lin))


def desenhar_hud(surface):
    """Plota a interface de status (Score, Vidas, e Temporizadores dinâmicos)."""
    pygame.draw.rect(surface, COR_PAINEL, (0, 0, LARGURA_TELA, 36))
    pygame.draw.line(surface, (40, 55, 80), (0, 36), (LARGURA_TELA, 36), 1)

    txt_score = fonte_hud.render(f"SCORE  {score:05d}", True, COR_TEXTO)
    f_label = "FASE FINAL" if fase_atual == FASE_MAXIMA else f"FASE  {fase_atual}"
    txt_fase = fonte_hud.render(f_label, True, COR_TEXTO_DIM)

    surface.blit(txt_score, (LARGURA_TELA // 2 - txt_score.get_width() // 2, 8))
    surface.blit(txt_fase, (LARGURA_TELA - txt_fase.get_width() - 20, 8))

    if SPRITE_CORACAO:
        espaco = 26
        for i in range(vidas):
            surface.blit(SPRITE_CORACAO, (14 + i * espaco, 7))
    else:
        txt_vidas = fonte_hud.render(f"VIDAS  {vidas}", True, COR_TEXTO)
        surface.blit(txt_vidas, (20, 8))

    c1_cor = COR_CAB1 if cobra1.viva else COR_CAB1_MORTA
    c2_cor = COR_CAB2 if cobra2.viva else COR_CAB2_MORTA
    txt_c1 = fonte_fase.render("● COBRA 1  [WASD]", True, c1_cor)
    txt_c2 = fonte_fase.render("[↑↓←→]  COBRA 2 ●", True, c2_cor)
    surface.blit(txt_c1, (20, ALTURA_TELA - 22))
    surface.blit(txt_c2, (LARGURA_TELA - txt_c2.get_width() - 20, ALTURA_TELA - 22))

    if timer_morte_isolada > 0:
        tempo_passado = pygame.time.get_ticks() - timer_morte_isolada
        segundos_rest = max(1, (cfg["delay_respawn"] - tempo_passado) // 1000 + 1)
        if not cobra1.viva:
            msg = fonte_med.render(f"COBRA 1 renascendo em {segundos_rest}s...", True, COR_CAB1_MORTA)
            surface.blit(msg, (20, ALTURA_TELA - 48))
        if not cobra2.viva:
            msg = fonte_med.render(f"COBRA 2 renascendo em {segundos_rest}s...", True, COR_CAB2_MORTA)
            surface.blit(msg, (LARGURA_TELA - msg.get_width() - 20, ALTURA_TELA - 48))


def desenhar_tela_game_over(surface):
    """Exibição sobreposta quando as vidas chegam a zero."""
    if _gameover_bg:
        surface.blit(_gameover_bg, (0, 0))
    else:
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

    cx = LARGURA_TELA // 2
    t_score = fonte_med.render(f"Score final: {score}", True, (255, 220, 180))
    s_score = fonte_med.render(f"Score final: {score}", True, (0, 0, 0))
    surface.blit(s_score, (cx - t_score.get_width() // 2 + 2, ALTURA_TELA - 120 + 2))
    surface.blit(t_score, (cx - t_score.get_width() // 2, ALTURA_TELA - 120))

    t = pygame.time.get_ticks()
    if (t // 600) % 2 == 0:
        t2 = fonte_med.render("Pressione qualquer tecla para reiniciar", True, (255, 255, 180))
        s2 = fonte_med.render("Pressione qualquer tecla para reiniciar", True, (0, 0, 0))
        surface.blit(s2, (cx - t2.get_width() // 2 + 2, ALTURA_TELA - 80 + 2))
        surface.blit(t2, (cx - t2.get_width() // 2, ALTURA_TELA - 80))


# =============================================================================
# BLOCO 7: SETUP INICIAL DAS ENTIDADES NO GAME
# =============================================================================
# Instanciação dos objetos da Classe Cobra nos polos opostos da fase
cobra1 = Cobra(COLS // 3, LINHAS // 2 + 2, 1, 0,
               COR_CAB1, COR_COR1, COR_CAB1_MORTA, "Cobra Vermelha",
               sprite_cabeca=SP1_CABECA, sprite_corpos=SP1_CORPOS)
cobra2 = Cobra(COLS * 2 // 3 - 3, LINHAS // 2 + 2, -1, 0,
               COR_CAB2, COR_COR2, COR_CAB2_MORTA, "Cobra Azul",
               sprite_cabeca=SP2_CABECA, sprite_corpos=SP2_CORPOS)

spawnar_itens()
timer_morte_isolada = 0

# =============================================================================
# BLOCO 8: GAME LOOP PRINCIPAL DO MOTOR (WHILE VERDADEIRO)
# =============================================================================
# Coração do jogo - executa a captura de Eventos, Logica de Colisão e Renderização gráfica
rodando = True
while rodando:
    tempo_atual = pygame.time.get_ticks()
    cfg = CONFIG_FASES[fase_atual]

    # --- 8.1 EVENTOS (INPUT DO TECLADO E JANELA) ---
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        elif evento.type == pygame.KEYDOWN:
            if _menu_ativo:
                globals()['_menu_ativo'] = False
                _iniciar_musica_fase(fase_atual)
                continue

            # Handler de resert caso o jogo acabe
            if vidas <= 0:
                score = 0
                vidas = 3
                fase_atual = 1
                som_gameover_tocado = False
                proximo_bonus_vida = 50
                lista_frutas_morte.clear()
                CANAL_GAMEOVER.stop()
                _parar_musica()
                reiniciar_cobras()
                spawnar_itens()
                continue

            # Mapping Cobra 1
            if evento.key == pygame.K_w: cobra1.mudar_direcao(0, -1)
            if evento.key == pygame.K_s: cobra1.mudar_direcao(0, 1)
            if evento.key == pygame.K_a: cobra1.mudar_direcao(-1, 0)
            if evento.key == pygame.K_d: cobra1.mudar_direcao(1, 0)

            # Mapping Cobra 2
            if evento.key == pygame.K_UP:    cobra2.mudar_direcao(0, -1)
            if evento.key == pygame.K_DOWN:  cobra2.mudar_direcao(0, 1)
            if evento.key == pygame.K_LEFT:  cobra2.mudar_direcao(-1, 0)
            if evento.key == pygame.K_RIGHT: cobra2.mudar_direcao(1, 0)

    # Controle musical contínuo atrelado ao loop
    if _menu_ativo:
        _iniciar_musica_menu()
    elif vidas > 0:
        _iniciar_musica_fase(fase_atual)
    else:
        _parar_musica()

    # --- 8.2 LÓGICA CORE (ATUALIZAÇÃO DE MATEMÁTICA E REGRAS) ---
    if vidas > 0 and not _menu_ativo:

        # Temporizador assíncrono para expiração dos itens sem travar a thread
        if tempo_atual - momento_geracao > cfg["tempo_item"]:
            spawnar_itens()

        if timer_morte_isolada > 0 and tempo_atual - timer_morte_isolada >= cfg["delay_respawn"]:
            ressuscitar_cobras_mortas()
            spawnar_itens()
            timer_morte_isolada = 0

        # Iteração de Movimento para ambas as cobras
        for cobra in [cobra1, cobra2]:
            if not cobra.viva:
                continue

            nx, ny = cobra.proxima_cabeca()

            # Condição de Falha 1: Parede (Boundary Box do mapa, excluindo o Menu superior - Y:36)
            if nx < 0 or nx >= LARGURA_TELA or ny < 36 or ny >= ALTURA_TELA:
                aplicar_morte(cobra, "Parede")
                continue

            nova_cab = [nx, ny]

            # Condição de Falha 2: Colisão com o próprio corpo
            if nova_cab in cobra.corpo[1:]:
                aplicar_morte(cobra, "Auto-colisão")
                continue

            # Condição de Falha 3: Intersecção com Cobra inimiga/aliada
            outra = cobra2 if cobra is cobra1 else cobra1
            if nova_cab in outra.corpo:
                aplicar_morte(cobra, f"Colidiu com {outra.nome}")
                continue

            # Condição de Falha 4: Armadilhas Explosivas
            if any(nova_cab == [bx, by] for bx, by in lista_bombas):
                aplicar_morte(cobra, "Bomba", penalidade_score=50, tocar_som=False)
                tocar_tnt()
                continue

            crescer = False
            # Mecânica Hitbox Orbs:
            for orb in lista_frutas_morte[:]:
                ox, oy, otipo, opontos = orb
                if nova_cab == [ox, oy]:
                    score += opontos
                    lista_frutas_morte.remove(orb)
                    crescer = True
                    tocar_comer()
                    if fase_atual < FASE_MAXIMA:
                        meta = CONFIG_FASES[fase_atual]["meta_score"]
                        if score >= meta:
                            fase_atual += 1
                            tocar_passou_fase()
                    break

            # Mecânica Hitbox Frutas:
            for fruta in lista_frutas:
                fx, fy, ftipo = fruta
                if nova_cab == [fx, fy]:
                    crescer = True
                    pontos = 5 if ftipo == "banana" else 3
                    score += pontos
                    lista_frutas.remove(fruta)
                    tocar_comer()

                    if not lista_frutas:
                        spawnar_itens()

                    # Escalonamento de Dificuldade contínuo
                    if fase_atual < FASE_MAXIMA:
                        meta = CONFIG_FASES[fase_atual]["meta_score"]
                        if score >= meta:
                            fase_atual += 1
                            tocar_passou_fase()
                            print(f"[FASE] Avançou para fase {fase_atual}!")
                    break

            cobra.mover(crescer=crescer)

        # Triggers de Feedback sonoro
        if cobra1.viva or cobra2.viva:
            tocar_andar()
        else:
            parar_andar()

        # Condição de Vitória/Recompensa: Score
        if score >= proximo_bonus_vida:
            vidas += 1
            proximo_bonus_vida += 50
            print(f"[BONUS] Vida extra! Vidas: {vidas} | Próximo bônus: {proximo_bonus_vida}")

        if not cobra1.viva and not cobra2.viva:
            vidas -= 1
            if vidas > 0:
                reiniciar_cobras()
                spawnar_itens()
            else:
                if not som_gameover_tocado:
                    parar_andar()
                    tocar_gameover()
                    som_gameover_tocado = True
        elif (not cobra1.viva or not cobra2.viva) and timer_morte_isolada == 0:
            timer_morte_isolada = tempo_atual

    # --- 8.3 FLUXO DE RENDERIZAÇÃO (DRAWING PIPELINE) ---
    # Background e Overlay condicional da Última Fase
    if fase_atual == FASE_MAXIMA and vidas > 0:
        idx = (tempo_atual // VELOCIDADE_STROBO) % len(CORES_STROBO)
        cor_f = CORES_STROBO[idx]
        cor_fundo_final = (
            min(COR_FUNDO[0] + cor_f[0] // 5, 80),
            min(COR_FUNDO[1] + cor_f[1] // 5, 80),
            min(COR_FUNDO[2] + cor_f[2] // 5, 80),
        )
    else:
        cor_fundo_final = COR_FUNDO

    # Swap de buffers para transição de Menus
    if _menu_ativo:
        desenhar_menu(tela)
        pygame.display.flip()
        relogio.tick(30)
        continue

    bg = BACKGROUNDS.get(fase_atual)
    if bg:
        tela.blit(bg, (0, 0))
        overlay_bg = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        overlay_bg.fill((0, 0, 0, 80))
        tela.blit(overlay_bg, (0, 0))
    else:
        tela.fill(cor_fundo_final)

    desenhar_grade(tela)

    # Iterações Gráficas das matrizes de itens
    for fruta in lista_frutas:
        fx, fy, ftipo = fruta
        if ftipo == "maca":
            desenhar_maca(tela, (fx, fy))
        else:
            desenhar_banana(tela, (fx, fy))

    for bx, by in lista_bombas:
        desenhar_bomba(tela, (bx, by))

    for orb in lista_frutas_morte:
        ox, oy, otipo, _ = orb
        desenhar_orb_morte(tela, (ox, oy), otipo)

    # Draw principal dos Players
    cobra2.desenhar(tela)
    cobra1.desenhar(tela)

    desenhar_hud(tela)

    # UI Blocking de Fim de Partida
    if vidas <= 0:
        desenhar_tela_game_over(tela)

    # Push de Frame Rate
    pygame.display.flip()
    relogio.tick(cfg["fps"])

# Fim da execução e limpeza do sistema operacional
pygame.quit()
sys.exit()