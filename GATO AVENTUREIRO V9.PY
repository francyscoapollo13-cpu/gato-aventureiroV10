"""
GATO AVENTUREIRO - Versao MOBILE (tela cheia + controles touch)
==================================================================
Feito para rodar no Pydroid 3 (Android).

COMO INSTALAR NO PYDROID 3:
1. Abra o Pydroid 3
2. Toque no menu e va em "Pip"
3. Pesquise por "pygame" e instale
4. (OPCIONAL, mas recomendado) pesquise por "numpy" e instale tambem --
   com numpy instalado, a geracao dos sons e da musica de fundo fica
   MUITO mais rapida (o jogo carrega em uma fracao do tempo). Sem
   numpy o jogo continua funcionando normalmente, so demora um pouco
   mais pra carregar na primeira vez.
5. Cole este codigo em um novo arquivo .py e toque em Play
6. O jogo abre em TELA CHEIA automaticamente

CONTROLES (TOUCH NA TELA):
- Botao esquerda (canto inferior esquerdo): mover para a esquerda
- Botao direita (canto inferior esquerdo): mover para a direita
- Botao PULAR (canto inferior direito): pular
- Tambem funciona com teclado (setas + espaco) se estiver no PC
- Objetivo: pegar todas as moedinhas, quebrar blocos e chegar na
  bandeira no final da fase!

CORRECOES NESTA VERSAO:
- Corrigido o crash ao comecar a fase (deslocamento_x colado num
  pygame.Rect, o que o pygame nao permite).
- Corrigido o botao de PULAR: antes, um toque bem rapido (aperta e
  solta no mesmo quadro) podia ser perdido, porque o jogo so olhava
  o estado "final" do toque depois de processar todos os eventos.
  Agora o toque no botao de pular fica guardado (buffer) ate ser
  consumido pelo gato, entao nenhum toque se perde. Tambem foi
  adicionado "coyote time" (uma pequena margem pra pular mesmo
  alguns quadros depois de sair da borda de uma plataforma) e
  "jump buffer" (se pular um pouco antes de tocar o chao, o pulo
  ainda acontece assim que aterrissar) -- isso deixa o pulo bem
  mais responsivo.
- Blocos quebraveis agora tem fisica de verdade: ao quebrar, viram
  4 pedacinhos que voam, giram e caem com gravidade, em vez do
  bloco inteiro "flutuando" pra cima como antes.
- Colisao das plataformas (fixas e moveis) melhorada: agora tambem
  resolve colisao pela lateral, entao o gato nao atravessa mais o
  lado de uma plataforma flutuante -- antes so a colisao por cima/
  por baixo era tratada.
- FASE REORGANIZADA (v8): o layout inteiro foi refeito em 6 zonas
  claras (aquecimento, inimigos, pontes moveis, platô alto, reta
  final), usando so 4 alturas fixas de plataforma. Antes as alturas
  e posicoes eram meio soltas e alguns grupos de blocos ficavam
  perto demais de outras coisas; agora cada plataforma, grupo de
  blocos, inimigo e espinho tem seu lugar dentro de uma zona, sem
  sobreposicoes.
- BLOCOS COM MAIS FISICA (v8): ao ser acertado por baixo, o bloco
  primeiro da um pequeno solavanco pra cima (como um bloco de
  verdade levando um golpe) antes de se estilhacar de vez em 6
  pedacos de tamanhos variados saindo de pontos aleatorios do
  bloco, alem de uma nuvem de poeira -- em vez de sempre 4 pedacos
  identicos saindo dos mesmos 4 cantos.
- MUSICA NOVA (v8): trilha de fundo recomposta do zero com clima de
  aventura (onda triangular no lead, mais parecida com flauta/
  ocarina, e um baixo em arpejo trocando de acorde a cada frase).
  Continua sendo uma composicao 100% original, gerada por formulas
  matematicas -- nao reproduz nenhuma musica existente.
- OTIMIZACAO DE CARREGAMENTO: a geracao de audio, que
  era o principal motivo do jogo demorar pra abrir no celular, foi
  otimizada de duas formas:
    1) Taxa de amostragem reduzida (22050 -> 11025 Hz) e a musica de
       fundo ficou um pouco mais curta. Isso ja corta o tempo de
       geracao praticamente pela metade em qualquer aparelho, sem
       perda perceptivel de qualidade nos efeitos (que sao ondas
       simples, tipo 8-bit).
    2) Se a biblioteca numpy estiver instalada, os sons passam a ser
       calculados em bloco (a "matematica da onda" para todas as
       amostras de uma vez, usando vetores) em vez de calcular
       amostra por amostra num loop Python puro. Isso e dezenas de
       vezes mais rapido. Se numpy nao estiver disponivel, o jogo
       cai automaticamente no metodo antigo (loop puro), entao nada
       quebra -- so fica um pouco mais lento pra carregar.
- BLOCOS COM FISICA REAL AO CAIR (v9): os fragmentos de um bloco
  quebrado agora "sentem" as plataformas de verdade -- eles quicam
  na plataforma ou no chao que estiver logo abaixo deles, e nao
  mais sempre numa altura fixa (o que fazia fragmentos criados em
  cima de plataformas altas atravessarem tudo e so pararem la
  embaixo, no chao).
- BLOCOS EM CIMA DE PLATAFORMA CORRIGIDO (v9): alguns grupos de
  blocos (platô alto da zona 5 e o trio final da zona 6) estavam
  posicionados perto demais da plataforma logo abaixo -- perto o
  bastante para o proprio gato ficar "preso" dentro do bloco so de
  ficar em pe na plataforma. Agora todo grupo de blocos guarda a
  mesma distancia da plataforma abaixo dele (espaco suficiente para
  o gato inteiro passar por baixo e pular ate o bloco), igual ja
  acontecia nas zonas 1, 2 e 4.
- GATO PODE PISAR NOS BLOCOS (v10): antes, os blocos intactos so
  reagiam quando o gato batia neles por baixo (pra quebrar) -- se o
  gato caisse em cima de um bloco, ele simplesmente atravessava e
  caia por dentro. Agora o topo de todo bloco intacto (e tambem
  durante o pequeno solavanco antes de quebrar) e solido: o gato
  pode pousar, ficar em pe e andar por cima normalmente, igual faz
  numa plataforma. Bater por baixo continua quebrando o bloco como
  antes.
"""

import pygame
import sys
import math
import array
import random

pygame.init()

# tenta usar numpy para acelerar a geracao de audio; se nao tiver
# instalado, o jogo continua funcionando normalmente (so mais lento
# na hora de gerar os sons)
try:
    import numpy as np
    NUMPY_DISPONIVEL = True
except ImportError:
    NUMPY_DISPONIVEL = False

# ---------------------------------------------------------
# AUDIO - inicializa o mixer (com protecao caso o aparelho nao
# tenha suporte a audio, o jogo continua funcionando sem som)
# ---------------------------------------------------------
# Taxa de amostragem reduzida (era 22050): ainda soa bem para ondas
# simples (quadrada/triangular/senoide) e corta pela metade a
# quantidade de numeros que precisam ser gerados -- ou seja, corta
# pela metade o tempo de carregamento, tanto com quanto sem numpy.
TAXA_AMOSTRAGEM = 11025
SOM_ATIVADO = True
try:
    pygame.mixer.init(frequency=TAXA_AMOSTRAGEM, size=-16, channels=1, buffer=512)
except pygame.error:
    SOM_ATIVADO = False

# ---------------------------------------------------------
# TELA CHEIA - usamos pygame.SCALED: o jogo desenha sempre numa
# resolucao fixa (LARGURA x ALTURA) e o proprio SDL escala isso
# pra tela real usando a placa de video (muito mais rapido do que
# escalar "na mao" com smoothscale a cada quadro).
# ---------------------------------------------------------
LARGURA, ALTURA = 800, 450
VERSAO_JOGO = "v10 - gato pisa em cima dos blocos"

MODO_SCALED = True
try:
    TELA = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN | pygame.SCALED)
except pygame.error:
    MODO_SCALED = False
    TELA = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

pygame.display.set_caption("Gato Aventureiro")

if MODO_SCALED:
    CANVAS = TELA
    TELA_LARGURA, TELA_ALTURA = LARGURA, ALTURA
else:
    CANVAS = pygame.Surface((LARGURA, ALTURA))
    TELA_LARGURA, TELA_ALTURA = TELA.get_size()

RELOGIO = pygame.time.Clock()
FPS = 60

GRAVIDADE = 0.95
PULO_FORCA = -17.5
VELOCIDADE = 7.5

# ---------------------------------------------------------
# CORES
# ---------------------------------------------------------
CEU_TOPO = (135, 206, 250)
CEU_BASE = (255, 223, 186)
VERDE_GRAMA = (86, 200, 90)
VERDE_GRAMA_ESCURO = (60, 160, 65)
VERDE_TUFO = (50, 140, 55)
MARROM_TERRA = (150, 100, 60)
LARANJA_GATO = (255, 150, 40)
LARANJA_GATO_ESCURO = (220, 110, 20)
BRANCO = (255, 255, 255)
PRETO = (20, 20, 20)
ROSA = (255, 180, 200)
AMARELO_MOEDA = (255, 215, 0)
AMARELO_MOEDA_ESCURO = (200, 160, 0)
VERMELHO = (230, 60, 60)
AZUL_NUVEM = (255, 255, 255)
ROXO = (170, 90, 220)
ROXO_CLARO = (200, 150, 235)
CINZA_BOTAO = (60, 60, 60, 140)
BRANCO_BOTAO = (255, 255, 255, 180)
TIJOLO = (200, 120, 70)
TIJOLO_ESCURO = (150, 85, 45)
AMARELO_SOL = (255, 236, 150)
HUD_FUNDO = (30, 30, 40, 120)
CINZA_PLATAFORMA = (140, 140, 160)
CINZA_PLATAFORMA_ESCURO = (95, 95, 115)
VERDE_SPEED = (80, 230, 150)

FONTE = pygame.font.SysFont("Arial", 24, bold=True)
FONTE_GRANDE = pygame.font.SysFont("Arial", 46, bold=True)
FONTE_PEQUENA = pygame.font.SysFont("Arial", 16, bold=True)


# ===========================================================
# SONS - gerados na hora com ondas simples (sem arquivos .wav)
# ===========================================================
def _forma_onda(tipo, t, freq):
    """Versao escalar (um numero por vez) -- usada apenas quando numpy
    NAO esta disponivel."""
    fase = (t * freq) % 1.0
    if tipo == "quadrada":
        return 1.0 if fase < 0.5 else -1.0
    if tipo == "triangular":
        return 4 * abs(fase - 0.5) - 1
    if tipo == "serra":
        return 2 * fase - 1
    return math.sin(2 * math.pi * freq * t)  # senoide


def _forma_onda_vetorizada(tipo, t, freq):
    """Mesma formula de _forma_onda, mas calculada para um array
    inteiro de instantes 't' de uma so vez (numpy). Isso e o que
    torna a geracao de som muito mais rapida: em vez de um loop
    Python calculando amostra por amostra, o numpy calcula todas as
    amostras numa unica operacao vetorial (em codigo C por baixo)."""
    fase = np.mod(t * freq, 1.0)
    if tipo == "quadrada":
        return np.where(fase < 0.5, 1.0, -1.0)
    if tipo == "triangular":
        return 4 * np.abs(fase - 0.5) - 1
    if tipo == "serra":
        return 2 * fase - 1
    return np.sin(2 * np.pi * freq * t)  # senoide


def _array_de_int16(valores_numpy):
    """Converte um array numpy (float) num array.array('h') de 16
    bits, com clamp pra nao estourar o volume."""
    clampado = np.clip(valores_numpy, -32767, 32767).astype(np.int16)
    resultado = array.array("h")
    resultado.frombytes(clampado.tobytes())
    return resultado


def gerar_tom(frequencia, duracao, volume=0.5, tipo="senoide"):
    """Gera um unico tom com um pequeno envelope pra evitar clique.
    Usa numpy (rapido) quando disponivel; senao cai no loop puro."""
    n = max(1, int(TAXA_AMOSTRAGEM * duracao))
    amp = int(32767 * volume)
    ataque = max(1, int(n * 0.05))
    solto = max(1, int(n * 0.25))

    if NUMPY_DISPONIVEL:
        t = np.arange(n, dtype=np.float64) / TAXA_AMOSTRAGEM
        onda = _forma_onda_vetorizada(tipo, t, frequencia)
        envelope = np.ones(n, dtype=np.float64)
        envelope[:ataque] = np.linspace(0.0, 1.0, ataque, endpoint=False)
        envelope[n - solto:] = np.minimum(envelope[n - solto:], np.linspace(1.0, 0.0, solto))
        return _array_de_int16(onda * amp * envelope)

    # --- caminho sem numpy (mais lento, mas funciona igual) ---
    amostras = array.array("h", [0]) * n
    for i in range(n):
        t = i / TAXA_AMOSTRAGEM
        valor = _forma_onda(tipo, t, frequencia)
        if i < ataque:
            fator = i / ataque
        elif i > n - solto:
            fator = max(0.0, (n - i) / solto)
        else:
            fator = 1.0
        amostras[i] = int(valor * amp * fator)
    return amostras


def gerar_ruido(duracao, volume=0.45):
    """Ruido branco com fade-out, usado pro som de quebrar bloco."""
    n = max(1, int(TAXA_AMOSTRAGEM * duracao))
    amp = int(32767 * volume)

    if NUMPY_DISPONIVEL:
        fator = np.clip(1 - np.arange(n, dtype=np.float64) / n, 0.0, 1.0)
        ruido = np.random.uniform(-1.0, 1.0, n)
        return _array_de_int16(ruido * amp * fator)

    # --- caminho sem numpy ---
    amostras = array.array("h", [0]) * n
    for i in range(n):
        fator = max(0.0, 1 - i / n)
        amostras[i] = int(random.uniform(-1, 1) * amp * fator)
    return amostras


def gerar_melodia(notas, volume=0.4, tipo="quadrada"):
    """notas: lista de (frequencia_em_hz_ou_0_para_silencio, duracao_em_s)"""
    partes = []
    for freq, dur in notas:
        if freq <= 0:
            n = max(1, int(TAXA_AMOSTRAGEM * dur))
            partes.append(array.array("h", [0]) * n)
        else:
            partes.append(gerar_tom(freq, dur, volume, tipo))
    total = array.array("h")
    for p in partes:
        total.extend(p)
    return total


def mixar(*arrays, volume_total=0.9):
    """Soma varias trilhas geradas em uma so (ex: melodia + baixo),
    preenchendo com silencio a mais curta e evitando estourar o volume."""
    tamanho = max(len(a) for a in arrays)

    if NUMPY_DISPONIVEL:
        soma = np.zeros(tamanho, dtype=np.float64)
        for a in arrays:
            np_a = np.frombuffer(a.tobytes(), dtype=np.int16).astype(np.float64)
            soma[:len(np_a)] += np_a
        return _array_de_int16(soma * volume_total)

    # --- caminho sem numpy ---
    resultado = array.array("h", [0]) * tamanho
    for i in range(tamanho):
        soma = 0
        for a in arrays:
            if i < len(a):
                soma += a[i]
        soma = int(soma * volume_total)
        resultado[i] = max(-32767, min(32767, soma))
    return resultado


def criar_som(amostras):
    if not SOM_ATIVADO:
        return None
    try:
        return pygame.mixer.Sound(buffer=amostras.tobytes())
    except Exception:
        return None


SONS = {}
MUSICA_CANAL = None


def carregar_audio():
    """Gera todos os sons do jogo. Chamado uma vez, com tela de espera."""
    global MUSICA_CANAL
    if not SOM_ATIVADO:
        return

    SONS["pulo"] = criar_som(gerar_tom(500, 0.12, 0.35, "quadrada"))
    SONS["pulo_duplo"] = criar_som(gerar_melodia([(500, 0.08), (750, 0.1)], 0.35, "quadrada"))
    SONS["powerup"] = criar_som(gerar_melodia([(660, 0.08), (880, 0.08), (1180, 0.14)], 0.4, "senoide"))
    SONS["moeda"] = criar_som(gerar_melodia([(880, 0.06), (1318, 0.10)], 0.35, "senoide"))
    SONS["quebrar"] = criar_som(gerar_ruido(0.18, 0.4))
    SONS["stomp"] = criar_som(gerar_melodia([(400, 0.05), (200, 0.08)], 0.4, "quadrada"))
    SONS["perder_vida"] = criar_som(gerar_tom(150, 0.35, 0.4, "serra"))
    SONS["vencer"] = criar_som(gerar_melodia(
        [(523, 0.15), (659, 0.15), (784, 0.15), (1047, 0.35)], 0.4, "quadrada"))
    SONS["perder_jogo"] = criar_som(gerar_melodia(
        [(392, 0.2), (349, 0.2), (294, 0.2), (196, 0.5)], 0.4, "triangular"))

    # Musica de fundo original, composta na hora (nao usa nenhum
    # arquivo de audio nem trecho de musica existente -- e uma melodia
    # 100% nova, entao nao ha risco de direitos autorais; nao e e nem
    # pode ser uma reproducao de nenhuma trilha de nenhum jogo). O que
    # foi buscado aqui foi um CLIMA parecido com trilhas classicas de
    # aventura (tipo as de Zelda): onda triangular no lead (um timbre
    # mais suave e "assoprado", parecido com flauta/ocarina, em vez da
    # onda quadrada mais "8-bit" de antes), um motivo em arpejo
    # ascendente que da uma sensacao heroica/de descoberta logo no
    # inicio, e um baixo em ostinato (padrao curto que se repete)
    # trocando de acorde a cada frase, tambem em onda triangular --
    # esse tipo de baixo triangular e uma marca registrada da sonoridade
    # chiptune classica de aventura.
    frase_a = [  # motivo de abertura: arpejo subindo, clima heroico
        (329.63, 0.18), (392.00, 0.18), (440.00, 0.18), (523.25, 0.30),
        (440.00, 0.15), (392.00, 0.15), (329.63, 0.45),
    ]
    frase_b = [  # trecho mais corrido, com mais movimento (sensacao de exploracao)
        (440.00, 0.15), (523.25, 0.15), (587.33, 0.15), (523.25, 0.15),
        (440.00, 0.15), (392.00, 0.15), (440.00, 0.30), (0, 0.1),
        (493.88, 0.15), (523.25, 0.15), (587.33, 0.30),
    ]
    frase_c = [  # resolucao triunfante, fechando o ciclo
        (392.00, 0.18), (440.00, 0.18), (523.25, 0.18), (587.33, 0.18),
        (659.25, 0.5), (523.25, 0.25), (392.00, 0.6),
    ]
    melodia_lead = frase_a + frase_b + frase_c

    # baixo em ostinato: raiz + quinta repetidas, trocando de acorde
    # (Lam -> Do -> Sol -> Re -> Lam) para acompanhar as frases acima
    linha_baixo = [
        (110.00, 0.36), (164.81, 0.36), (110.00, 0.36), (164.81, 0.36),  # Lam
        (130.81, 0.36), (196.00, 0.36), (130.81, 0.36), (196.00, 0.36),  # Do
        (98.00, 0.36), (146.83, 0.36), (98.00, 0.36), (146.83, 0.36),    # Sol
        (146.83, 0.36), (220.00, 0.36), (146.83, 0.36), (220.00, 0.36),  # Re
        (110.00, 0.72), (110.00, 0.72),                                   # Lam final
    ]
    trilha_lead = gerar_melodia(melodia_lead, 0.28, "triangular")
    trilha_baixo = gerar_melodia(linha_baixo, 0.22, "triangular")
    amostras_musica = mixar(trilha_lead, trilha_baixo, volume_total=0.8)
    musica = criar_som(amostras_musica)
    if musica is not None:
        MUSICA_CANAL = musica


def tocar(nome):
    if not SOM_ATIVADO:
        return
    som = SONS.get(nome)
    if som is not None:
        som.play()


def tocar_musica():
    if SOM_ATIVADO and MUSICA_CANAL is not None:
        MUSICA_CANAL.play(loops=-1)


def atualizar_tela_real():
    """Copia o CANVAS pra tela de verdade (quando nao ha suporte a SCALED)
    e manda o SDL mostrar o quadro."""
    if not MODO_SCALED:
        tela_final = pygame.transform.scale(CANVAS, (TELA_LARGURA, TELA_ALTURA))
        TELA.blit(tela_final, (0, 0))
    pygame.display.flip()


def tela_carregando():
    CANVAS.fill(CEU_TOPO)
    texto = FONTE_GRANDE.render("Carregando...", True, BRANCO)
    CANVAS.blit(texto, (LARGURA // 2 - texto.get_width() // 2, ALTURA // 2 - 30))
    atualizar_tela_real()


# ---------------------------------------------------------
# CONTROLES TOUCH NA TELA
# ---------------------------------------------------------
class ControlesTouch:
    def __init__(self):
        self.btn_esquerda = pygame.Rect(20, 340, 60, 60)
        self.btn_direita = pygame.Rect(90, 340, 60, 60)
        self.btn_pular = pygame.Rect(700, 330, 75, 75)

        self.esquerda = False
        self.direita = False
        self.pular = False
        self.dedos = {}
        # Guarda um toque no botao de pular ate ele ser "consumido" pelo
        # gato. Sem isso, um toque bem rapido (aperta e solta dentro do
        # mesmo quadro) podia ser perdido, pois so olhavamos o estado
        # final apos processar todos os eventos do quadro.
        self.pulo_solicitado = False

    def consumir_pulo(self):
        """Retorna True uma unica vez se houve um toque no botao de
        pular desde a ultima chamada, e reseta o pedido."""
        if self.pulo_solicitado:
            self.pulo_solicitado = False
            return True
        return False

    def tela_para_canvas(self, pos):
        x, y = pos
        escala_x = LARGURA / TELA_LARGURA
        escala_y = ALTURA / TELA_ALTURA
        return (x * escala_x, y * escala_y)

    def processar_evento(self, evento):
        if evento.type == pygame.FINGERDOWN:
            pos = (evento.x * TELA_LARGURA, evento.y * TELA_ALTURA)
            cpos = self.tela_para_canvas(pos)
            self._pressionar(evento.finger_id, cpos)
        elif evento.type == pygame.FINGERUP:
            self._soltar(evento.finger_id)
        elif evento.type == pygame.FINGERMOTION:
            pos = (evento.x * TELA_LARGURA, evento.y * TELA_ALTURA)
            cpos = self.tela_para_canvas(pos)
            self._soltar(evento.finger_id)
            self._pressionar(evento.finger_id, cpos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            cpos = self.tela_para_canvas(evento.pos)
            self._pressionar("mouse", cpos)
        elif evento.type == pygame.MOUSEBUTTONUP:
            self._soltar("mouse")

    def _pressionar(self, fid, cpos):
        if self.btn_esquerda.collidepoint(cpos):
            self.dedos[fid] = "esquerda"
        elif self.btn_direita.collidepoint(cpos):
            self.dedos[fid] = "direita"
        elif self.btn_pular.collidepoint(cpos):
            self.dedos[fid] = "pular"
            self.pulo_solicitado = True
        self._atualizar_estado()

    def _soltar(self, fid):
        if fid in self.dedos:
            del self.dedos[fid]
        self._atualizar_estado()

    def _atualizar_estado(self):
        valores = self.dedos.values()
        self.esquerda = "esquerda" in valores
        self.direita = "direita" in valores
        self.pular = "pular" in valores

    def desenhar(self, canvas):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

        cor = BRANCO_BOTAO if self.esquerda else CINZA_BOTAO
        pygame.draw.rect(overlay, cor, self.btn_esquerda, border_radius=12)
        cx, cy = self.btn_esquerda.center
        pygame.draw.polygon(overlay, PRETO, [(cx + 8, cy - 12), (cx - 10, cy), (cx + 8, cy + 12)])

        cor = BRANCO_BOTAO if self.direita else CINZA_BOTAO
        pygame.draw.rect(overlay, cor, self.btn_direita, border_radius=12)
        cx, cy = self.btn_direita.center
        pygame.draw.polygon(overlay, PRETO, [(cx - 8, cy - 12), (cx + 10, cy), (cx - 8, cy + 12)])

        cor = BRANCO_BOTAO if self.pular else CINZA_BOTAO
        pygame.draw.ellipse(overlay, cor, self.btn_pular)
        cx, cy = self.btn_pular.center
        pygame.draw.polygon(overlay, PRETO, [(cx, cy - 14), (cx - 12, cy + 10), (cx + 12, cy + 10)])

        canvas.blit(overlay, (0, 0))


CONTROLES = ControlesTouch()


# ---------------------------------------------------------
# PARTICULAS (usadas ao quebrar blocos e pegar moedas)
# ---------------------------------------------------------
class Particula:
    def __init__(self, x, y, cor, vx=None, vy=None, vida=30, raio=4):
        self.x = x
        self.y = y
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-6, -2)
        self.cor = cor
        self.vida = vida
        self.vida_max = vida
        self.raio = raio

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.4
        self.vida -= 1

    def viva(self):
        return self.vida > 0

    def desenhar(self, canvas, camera_x):
        x = self.x - camera_x
        if -20 < x < LARGURA + 20:
            fator = max(0.0, self.vida / self.vida_max)
            raio = max(1, int(self.raio * fator))
            pygame.draw.rect(canvas, self.cor, (x - raio, self.y - raio, raio * 2, raio * 2))


PARTICULAS = []


def espalhar_particulas(x, y, cor, quantidade=8):
    for _ in range(quantidade):
        PARTICULAS.append(Particula(x, y, cor, vida=random.randint(20, 35)))


def atualizar_particulas():
    for p in PARTICULAS:
        p.atualizar()
    PARTICULAS[:] = [p for p in PARTICULAS if p.viva()]


def desenhar_particulas(canvas, camera_x):
    for p in PARTICULAS:
        p.desenhar(canvas, camera_x)


# ---------------------------------------------------------
# FRAGMENTOS DE BLOCO (fisica de verdade ao quebrar um bloco:
# cada pedaco tem velocidade propria, gravidade, giro e quica
# no que estiver logo abaixo dele -- uma plataforma ou o chao --
# em vez de sempre cair ate uma altura fixa)
# ---------------------------------------------------------
class Fragmento:
    def __init__(self, x, y, tamanho, cor, vx, vy):
        self.x = x
        self.y = y
        self.tamanho = tamanho
        self.cor = cor
        self.vx = vx
        self.vy = vy
        self.rotacao = random.uniform(0, 360)
        self.vel_rotacao = random.uniform(-10, 10)
        self.vida = 45
        self.quicou = False

    def _chao_abaixo(self, plataformas):
        """Acha a superficie solida (plataforma ou chao) mais proxima
        logo abaixo da posicao atual do fragmento, olhando so pra
        quem esta na mesma faixa horizontal. Se nao achar nenhuma,
        usa o fundo da tela como ultimo recurso."""
        melhor = ALTURA + 40
        for plat in plataformas:
            if plat.left - 6 <= self.x <= plat.right + 6 and plat.top >= self.y:
                if plat.top < melhor:
                    melhor = plat.top
        return melhor

    def atualizar(self, plataformas=None):
        self.vx *= 0.97
        self.vy += 0.85
        self.x += self.vx
        self.y += self.vy
        self.rotacao += self.vel_rotacao

        # quica uma vez de leve ao "tocar" a superficie solida mais
        # proxima abaixo dele (plataforma real ou chao), em vez de
        # sempre usar uma altura fixa -- assim um fragmento criado em
        # cima de uma plataforma alta para na propria plataforma, e
        # nao atravessa tudo ate o chao la embaixo.
        if not self.quicou:
            chao_y = self._chao_abaixo(plataformas) if plataformas else ALTURA - 50
            if self.y > chao_y:
                self.y = chao_y
                self.vy *= -0.35
                self.vx *= 0.5
                self.quicou = True

        self.vida -= 1

    def viva(self):
        return self.vida > 0

    def desenhar(self, canvas, camera_x):
        x = self.x - camera_x
        if -30 < x < LARGURA + 30:
            fator = max(0.0, self.vida / 45)
            tam = max(1, int(self.tamanho * (0.5 + 0.5 * fator)))
            superficie = pygame.Surface((tam, tam), pygame.SRCALPHA)
            superficie.fill(self.cor)
            girado = pygame.transform.rotate(superficie, self.rotacao)
            rect_girado = girado.get_rect(center=(x, self.y))
            canvas.blit(girado, rect_girado)


FRAGMENTOS = []


def espalhar_fragmentos_bloco(rect_bloco):
    """Quebra um bloco em 6 pedacos de tamanhos levemente variados que
    voam para os lados com fisica de verdade (gravidade + giro + quique),
    saindo de pontos aleatorios dentro do bloco -- fica mais parecido
    com um tijolo estilhacando de verdade do que 4 quadrados identicos
    saindo sempre dos mesmos 4 cantos."""
    cx, cy = rect_bloco.centerx, rect_bloco.centery
    cores = [TIJOLO, TIJOLO_ESCURO]
    for i in range(6):
        cor = cores[i % 2]
        tam = random.randint(6, max(7, rect_bloco.width // 3))
        origem_x = cx + random.uniform(-rect_bloco.width / 2, rect_bloco.width / 2)
        origem_y = cy + random.uniform(-rect_bloco.height / 2, rect_bloco.height / 2)
        vx = random.uniform(-5.0, 5.0)
        vy = random.uniform(-6.0, -1.5)
        FRAGMENTOS.append(Fragmento(origem_x, origem_y, tam, cor, vx, vy))


def atualizar_fragmentos(plataformas=None):
    for f in FRAGMENTOS:
        f.atualizar(plataformas)
    FRAGMENTOS[:] = [f for f in FRAGMENTOS if f.viva()]


def desenhar_fragmentos(canvas, camera_x):
    for f in FRAGMENTOS:
        f.desenhar(canvas, camera_x)


# ---------------------------------------------------------
# CLASSE DO GATO (JOGADOR)
# ---------------------------------------------------------
class Gato:
    def __init__(self, x, y):
        self.largura = 40
        self.altura = 40
        self.x = x
        self.y = y
        self.vel_y = 0
        self.no_chao = False
        self.direcao = 1
        self.andando = 0
        self.vidas = 3
        self.invencivel = 0
        self.pontos = 0
        self.tem_pulo_duplo = False
        self.pulo_duplo_usado = False
        self._teclado_pulo_antes = False
        self.turbo_timer = 0
        # coyote time: quantos quadros faz que o gato deixou de estar no
        # chao (permite pular por uma pequena margem mesmo depois de sair
        # da borda de uma plataforma)
        self.quadros_fora_do_chao = 0
        # jump buffer: se o jogador pediu pulo um pouco antes de aterrissar,
        # o pulo ainda acontece assim que tocar o chao
        self.buffer_pulo = 0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)

    def velocidade_atual(self):
        return VELOCIDADE * 1.6 if self.turbo_timer > 0 else VELOCIDADE

    def atualizar(self, teclas, plataformas_solidas, controles, deslocamentos=None):
        mover = 0
        ir_esquerda = teclas[pygame.K_LEFT] or controles.esquerda
        ir_direita = teclas[pygame.K_RIGHT] or controles.direita

        vel = self.velocidade_atual()
        if ir_esquerda:
            mover = -vel
            self.direcao = -1
            self.andando += 1
        elif ir_direita:
            mover = vel
            self.direcao = 1
            self.andando += 1
        else:
            self.andando = 0

        self.x += mover
        self.x = max(0, self.x)

        # --- PEDIDO DE PULO --------------------------------------------
        # Teclado: deteccao de borda (so conta o instante em que a tecla
        # foi pressionada, nao enquanto ela fica segurada).
        pular_teclado = teclas[pygame.K_SPACE] or teclas[pygame.K_UP]
        pulo_borda_teclado = pular_teclado and not self._teclado_pulo_antes
        self._teclado_pulo_antes = pular_teclado

        # Touch: consumir_pulo() ja devolve True uma unica vez por toque,
        # mesmo que o dedo tenha encostado e saido do botao no mesmo
        # quadro -- e o que corrige toques rapidos que antes se perdiam.
        pulo_solicitado_agora = pulo_borda_teclado or controles.consumir_pulo()

        # Jump buffer: guarda o pedido por alguns quadros, assim se o
        # jogador pedir o pulo um pouco antes de tocar o chao, o pulo
        # ainda acontece assim que aterrissar.
        if pulo_solicitado_agora:
            self.buffer_pulo = 6
        elif self.buffer_pulo > 0:
            self.buffer_pulo -= 1

        # Coyote time: mesmo alguns quadros depois de sair da borda de
        # uma plataforma, ainda conta como "no chao" pra fins de pulo.
        pode_pular_normal = self.no_chao or self.quadros_fora_do_chao <= 6

        if self.buffer_pulo > 0 and pode_pular_normal:
            self.vel_y = PULO_FORCA
            self.no_chao = False
            self.quadros_fora_do_chao = 999
            self.pulo_duplo_usado = False
            self.buffer_pulo = 0
            tocar("pulo")
        elif self.buffer_pulo > 0 and self.tem_pulo_duplo and not self.pulo_duplo_usado and not self.no_chao:
            self.vel_y = PULO_FORCA * 0.85
            self.pulo_duplo_usado = True
            self.buffer_pulo = 0
            tocar("pulo_duplo")
            espalhar_particulas(self.x + self.largura // 2, self.y + self.altura, (120, 220, 255), 10)

        self.vel_y += GRAVIDADE
        if self.vel_y > 20:
            self.vel_y = 20
        self.y += self.vel_y

        # colisao vertical com plataformas (caindo)
        estava_no_chao = self.no_chao
        self.no_chao = False
        gato_rect = self.rect()
        plataforma_embaixo = None
        if self.vel_y >= 0:
            for plat in plataformas_solidas:
                if gato_rect.colliderect(plat):
                    if gato_rect.bottom - self.vel_y <= plat.top + 10:
                        self.y = plat.top - self.altura
                        self.vel_y = 0
                        self.no_chao = True
                        self.pulo_duplo_usado = False
                        gato_rect = self.rect()
                        plataforma_embaixo = plat

        if self.no_chao:
            self.quadros_fora_do_chao = 0
        elif estava_no_chao:
            self.quadros_fora_do_chao = 0
        else:
            self.quadros_fora_do_chao += 1

        # colisao vertical com plataformas (batendo a cabeca por baixo)
        if self.vel_y < 0:
            gato_rect = self.rect()
            for plat in plataformas_solidas:
                if gato_rect.colliderect(plat) and gato_rect.top - self.vel_y >= plat.bottom - 10:
                    self.y = plat.bottom
                    self.vel_y = 0
                    gato_rect = self.rect()

        # colisao lateral com plataformas: so entra em acao quando o
        # gato realmente afundou pela lateral (bastante sobreposicao
        # vertical), pra nao interferir com o "pousar em cima" normal,
        # onde a sobreposicao vertical e praticamente zero.
        gato_rect = self.rect()
        for plat in plataformas_solidas:
            if not gato_rect.colliderect(plat):
                continue
            sobreposicao_topo = gato_rect.bottom - plat.top
            sobreposicao_base = plat.bottom - gato_rect.top
            if sobreposicao_topo > 8 and sobreposicao_base > 8:
                centro_gato = gato_rect.centerx
                if centro_gato < plat.centerx:
                    self.x = plat.left - self.largura
                else:
                    self.x = plat.right
                gato_rect = self.rect()

        # se a plataforma embaixo for movel, o gato anda junto com ela
        # (o deslocamento de cada plataforma movel fica num dicionario
        # a parte, ja que o pygame.Rect nao aceita atributos extras)
        if plataforma_embaixo is not None and deslocamentos:
            self.x += deslocamentos.get(id(plataforma_embaixo), 0)

        if self.invencivel > 0:
            self.invencivel -= 1
        if self.turbo_timer > 0:
            self.turbo_timer -= 1

        if self.y > ALTURA + 200:
            self.perder_vida()

    def perder_vida(self):
        self.vidas -= 1
        self.x = 60
        self.y = 100
        self.vel_y = 0
        self.invencivel = 90
        self.quadros_fora_do_chao = 999
        self.buffer_pulo = 0
        tocar("perder_vida")

    def desenhar(self, canvas, camera_x):
        cx = self.x - camera_x
        cy = self.y

        sombra = pygame.Surface((self.largura, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 70), sombra.get_rect())
        canvas.blit(sombra, (cx, cy + self.altura - 4))

        if self.invencivel > 0 and self.invencivel % 10 < 5:
            return

        pulinho = 3 if (self.andando // 6) % 2 == 0 and self.no_chao and self.andando > 0 else 0

        # cauda comprida e curva, mais parecida com a de um gato de verdade
        if self.direcao == 1:
            pygame.draw.arc(canvas, LARANJA_GATO_ESCURO, (cx - 20, cy + pulinho, 28, 36), -0.6, 2.4, 5)
        else:
            pygame.draw.arc(canvas, LARANJA_GATO_ESCURO, (cx + self.largura - 8, cy + pulinho, 28, 36), 0.7, 3.7, 5)

        # patinhas
        pata_y = cy + self.altura - 5 + pulinho
        for dx in (5, 27):
            pygame.draw.ellipse(canvas, LARANJA_GATO_ESCURO, (cx + dx, pata_y, 9, 7))

        # corpo (mais alongado e ovalado, como o de um gato)
        corpo = pygame.Rect(cx, cy + pulinho + 4, self.largura, self.altura - pulinho - 6)
        pygame.draw.ellipse(canvas, LARANJA_GATO, corpo)
        pygame.draw.ellipse(canvas, LARANJA_GATO_ESCURO, corpo, 2)

        # listras tigradas nas costas
        for lx in (8, 18, 28):
            pygame.draw.arc(canvas, LARANJA_GATO_ESCURO,
                             (cx + lx - 5, cy + pulinho + 2, 12, 14), 3.6, 5.8, 2)

        # cabeca (circulo separado do corpo, mais redonda)
        raio_cabeca = 15
        cabeca_cx = cx + 26 if self.direcao == 1 else cx + 14
        cabeca_cy = cy + pulinho + 13
        pygame.draw.circle(canvas, LARANJA_GATO, (cabeca_cx, cabeca_cy), raio_cabeca)
        pygame.draw.circle(canvas, LARANJA_GATO_ESCURO, (cabeca_cx, cabeca_cy), raio_cabeca, 2)

        # orelhas triangulares com interior rosa
        base_orelha_y = cabeca_cy - raio_cabeca + 4
        orelha_esq = [(cabeca_cx - 13, base_orelha_y + 4), (cabeca_cx - 8, base_orelha_y - 13), (cabeca_cx - 1, base_orelha_y + 2)]
        orelha_dir = [(cabeca_cx + 1, base_orelha_y + 2), (cabeca_cx + 8, base_orelha_y - 13), (cabeca_cx + 13, base_orelha_y + 4)]
        pygame.draw.polygon(canvas, LARANJA_GATO, orelha_esq)
        pygame.draw.polygon(canvas, LARANJA_GATO, orelha_dir)
        pygame.draw.polygon(canvas, ROSA, [(cabeca_cx - 9, base_orelha_y), (cabeca_cx - 7, base_orelha_y - 7), (cabeca_cx - 3, base_orelha_y - 1)])
        pygame.draw.polygon(canvas, ROSA, [(cabeca_cx + 3, base_orelha_y - 1), (cabeca_cx + 7, base_orelha_y - 7), (cabeca_cx + 9, base_orelha_y)])

        # olhos com pupila vertical (caracteristico de gato)
        olho_x = cabeca_cx + 6 if self.direcao == 1 else cabeca_cx - 6
        olho_x2 = cabeca_cx - 6 if self.direcao == 1 else cabeca_cx + 6
        for ox in (olho_x, olho_x2):
            pygame.draw.ellipse(canvas, (150, 230, 100), (ox - 4, cabeca_cy - 4, 8, 8))
            pygame.draw.ellipse(canvas, PRETO, (ox - 1, cabeca_cy - 3, 2, 6))

        # focinho, nariz e boca
        focinho_x = cabeca_cx + 12 if self.direcao == 1 else cabeca_cx - 12
        pygame.draw.polygon(canvas, ROSA, [(focinho_x - 3, cabeca_cy + 4), (focinho_x + 3, cabeca_cy + 4), (focinho_x, cabeca_cy + 8)])
        pygame.draw.arc(canvas, PRETO, (focinho_x - 6, cabeca_cy + 6, 7, 6), 3.3, 6.3, 1)
        pygame.draw.arc(canvas, PRETO, (focinho_x - 1, cabeca_cy + 6, 7, 6), 2.9, 5.9, 1)

        # bigodes
        sinal = 1 if self.direcao == 1 else -1
        for dy in (-3, 0, 3):
            pygame.draw.line(canvas, BRANCO,
                              (focinho_x + 2 * sinal, cabeca_cy + 5 + dy),
                              (focinho_x + 14 * sinal, cabeca_cy + 3 + dy), 1)


# ---------------------------------------------------------
# PLATAFORMAS MOVEIS
# ---------------------------------------------------------
class PlataformaMovel:
    """Plataforma que anda de um lado a outro. O gato pode ficar em
    cima dela e e carregado junto (ver Gato.atualizar)."""

    def __init__(self, x, y, largura, altura, min_x, max_x, vel):
        self.x = x
        self.y = y
        self.width = largura
        self.height = altura
        self.min_x = min_x
        self.max_x = max_x
        self.vel = vel
        self.deslocamento_x = 0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def atualizar(self):
        antes = self.x
        self.x += self.vel
        if self.x < self.min_x or self.x > self.max_x:
            self.vel *= -1
            self.x = max(self.min_x, min(self.x, self.max_x))
        self.deslocamento_x = self.x - antes

    def desenhar(self, canvas, camera_x):
        x = self.x - camera_x
        if x + self.width < 0 or x > LARGURA:
            return
        r = pygame.Rect(x, self.y, self.width, self.height)
        pygame.draw.rect(canvas, CINZA_PLATAFORMA, r, border_radius=4)
        pygame.draw.rect(canvas, CINZA_PLATAFORMA_ESCURO, r, 3, border_radius=4)
        for tx in range(0, self.width, 16):
            pygame.draw.line(canvas, CINZA_PLATAFORMA_ESCURO, (x + tx, self.y), (x + tx, self.y + self.height), 1)


# ---------------------------------------------------------
# ESPINHOS (perigo instantaneo, sem poder pisar)
# ---------------------------------------------------------
def desenhar_espinhos(canvas, camera_x, espinhos):
    for e in espinhos:
        x = e.x - camera_x
        if x + e.width < 0 or x > LARGURA:
            continue
        num_picos = max(1, e.width // 14)
        largura_pico = e.width / num_picos
        for i in range(num_picos):
            px = x + i * largura_pico
            pygame.draw.polygon(canvas, (200, 200, 210), [
                (px, e.bottom), (px + largura_pico / 2, e.top), (px + largura_pico, e.bottom)
            ])
            pygame.draw.polygon(canvas, (130, 130, 145), [
                (px, e.bottom), (px + largura_pico / 2, e.top), (px + largura_pico, e.bottom)
            ], 2)


def checar_espinhos(espinhos, gato):
    if gato.invencivel > 0:
        return
    gato_rect = gato.rect()
    for e in espinhos:
        if gato_rect.colliderect(e):
            gato.perder_vida()
            espalhar_particulas(gato_rect.centerx, gato_rect.centery, VERMELHO, 8)
            return


# ---------------------------------------------------------
# GERACAO DA FASE
# ---------------------------------------------------------
def criar_fase():
    # Fase reorganizada em 6 zonas claras, cada uma com um proposito
    # (aquecimento, inimigo, ponte movel, etc), usando so 4 "andares"
    # de altura fixos -- assim tudo fica alinhado e nao ha mais blocos
    # ou plataformas flutuando meio aleatorios no meio do cenario.
    TERRENO = 400   # topo do chao
    ANDAR_1 = 320   # plataforma baixa
    ANDAR_2 = 260   # plataforma media
    ANDAR_3 = 195   # plataforma alta

    # Distancia vertical que TODO grupo de blocos guarda da plataforma
    # que fica logo abaixo dele. Precisa ser maior que a altura do
    # gato (40px) com folga, senao o gato fica com a cabeca "dentro"
    # do bloco so de ficar em pe na plataforma, e o bloco parece
    # grudado/sobreposto a plataforma em vez de flutuando no ar acima
    # dela (era exatamente esse o bug nos blocos do platô alto e nos
    # blocos da reta final).
    GAP_BLOCO_PLATAFORMA = 60
    ALTURA_BLOCO_PADRAO = 30

    ALTURA_BLOCOS = ANDAR_1 - GAP_BLOCO_PLATAFORMA - ALTURA_BLOCO_PADRAO          # blocos sobre ANDAR_1 (zonas 1, 2 e 4)
    ALTURA_BLOCOS_ALTOS = ANDAR_3 - GAP_BLOCO_PLATAFORMA - ALTURA_BLOCO_PADRAO    # blocos sobre ANDAR_3 (zona 5, platô alto)
    ALTURA_BLOCOS_ZONA6 = ANDAR_2 - GAP_BLOCO_PLATAFORMA - ALTURA_BLOCO_PADRAO    # blocos sobre ANDAR_2 (zona 6, reta final)

    # chao unico e continuo, sem buracos/precipicios
    plataformas = [
        pygame.Rect(0, TERRENO, 3400, 50),

        # zona 1 - aquecimento
        pygame.Rect(280, ANDAR_1, 150, 20),
        # zona 2 - primeiro inimigo
        pygame.Rect(820, ANDAR_1, 120, 20),
        # zona 3 - pouso apos a primeira ponte movel
        pygame.Rect(1620, ANDAR_2, 130, 20),
        # zona 4 - segundo inimigo (chao + voador)
        pygame.Rect(1900, ANDAR_1, 130, 20),
        # zona 5 - platô alto
        pygame.Rect(2420, ANDAR_3, 110, 20),
        # zona 6 - reta final
        pygame.Rect(2900, ANDAR_2, 140, 20),
    ]

    # plataformas moveis - cada uma faz a ponte entre duas zonas e
    # exige timing pra pular em cima
    plataformas_moveis = [
        PlataformaMovel(1050, ANDAR_2 + 40, 90, 20, 1050, 1500, 2.2),   # zona 2 -> zona 3
        PlataformaMovel(2100, ANDAR_2 - 30, 90, 20, 2100, 2320, 2.8),   # zona 4 -> zona 5 (subindo)
        PlataformaMovel(2600, ANDAR_2 - 30, 100, 20, 2600, 2800, 2.5),  # zona 5 -> zona 6 (descendo)
    ]

    # espinhos no chao - sempre nos vaos entre zonas, nunca colados
    # em outro obstaculo, pra ficar claro o que e o perigo de cada trecho
    espinhos = [
        pygame.Rect(560, 388, 60, 12),    # fim da zona 1
        pygame.Rect(1300, 388, 70, 12),   # sob a primeira ponte movel
        pygame.Rect(2020, 388, 60, 12),   # fim da zona 4
        pygame.Rect(3070, 388, 70, 12),   # reta final, antes da bandeira
    ]

    # grupos de blocos: cada grupo fica logo acima da plataforma da
    # mesma zona, sempre com o mesmo espacamento de 40px entre blocos
    # e a mesma distancia vertical (GAP_BLOCO_PLATAFORMA) da plataforma
    posicoes_blocos = [
        (330, ALTURA_BLOCOS), (370, ALTURA_BLOCOS), (410, ALTURA_BLOCOS),                # zona 1 - trio
        (850, ALTURA_BLOCOS), (890, ALTURA_BLOCOS),                                      # zona 2 - dupla
        (1930, ALTURA_BLOCOS), (1970, ALTURA_BLOCOS), (2010, ALTURA_BLOCOS),             # zona 4 - trio
        (2440, ALTURA_BLOCOS_ALTOS), (2480, ALTURA_BLOCOS_ALTOS),                        # zona 5 - dupla (mais alta)
        (2930, ALTURA_BLOCOS_ZONA6), (2970, ALTURA_BLOCOS_ZONA6), (3010, ALTURA_BLOCOS_ZONA6),  # zona 6 - trio final
    ]
    blocos_quebraveis = []
    for i, (bx, by) in enumerate(posicoes_blocos):
        blocos_quebraveis.append({
            "rect": pygame.Rect(bx, by, 36, ALTURA_BLOCO_PADRAO),
            "estado": "intacto",
            "timer": 0,
            "com_moeda": (i % 3 == 0),
        })

    moedas = []
    for plat in plataformas[1:]:
        moedas.append(pygame.Rect(plat.x + plat.width // 2 - 10, plat.y - 35, 20, 20))
    moedas += [
        pygame.Rect(180, 350, 20, 20),
        pygame.Rect(650, 350, 20, 20),
        pygame.Rect(1350, 350, 20, 20),
        pygame.Rect(2750, 350, 20, 20),
        pygame.Rect(3200, 350, 20, 20),
    ]

    inimigos = [
        # zona 2 - patrulha em volta da plataforma baixa
        {"rect": pygame.Rect(850, 370, 30, 30), "min_x": 780, "max_x": 1020, "vel": 2.5, "vivo": True, "tipo": "chao"},
        # zona 4 - patrulha mais rapida
        {"rect": pygame.Rect(1950, 370, 30, 30), "min_x": 1850, "max_x": 2150, "vel": 3.5, "vivo": True, "tipo": "chao"},
        # zona 6 - reta final
        {"rect": pygame.Rect(2950, 370, 30, 30), "min_x": 2870, "max_x": 3170, "vel": 3, "vivo": True, "tipo": "chao"},
        # inimigos voadores: se movem em onda e o gato precisa pisar
        # neles (ou desviar) porque nao andam so no chao
        {"rect": pygame.Rect(1750, 150, 30, 30), "min_x": 1700, "max_x": 2050, "vel": 3,
         "vivo": True, "tipo": "voador", "base_y": 150, "fase": 0.0},
        {"rect": pygame.Rect(2450, 120, 30, 30), "min_x": 2350, "max_x": 2650, "vel": 3.5,
         "vivo": True, "tipo": "voador", "base_y": 120, "fase": 1.5},
    ]

    # power-ups: pulo duplo (zona 2, ajuda com a ponte movel logo depois)
    # e turbo de velocidade (zona 5, ajuda na reta final)
    powerups = [
        {"rect": pygame.Rect(860, ANDAR_1 - 55, 26, 26), "tipo": "pulo_duplo", "coletado": False},
        {"rect": pygame.Rect(2450, ANDAR_3 - 60, 26, 26), "tipo": "turbo", "coletado": False},
    ]

    bandeira = pygame.Rect(3250, 250, 15, 150)
    fim_fase_x = 3300

    return (plataformas, plataformas_moveis, espinhos, blocos_quebraveis, moedas,
            inimigos, powerups, bandeira, fim_fase_x)


# ---------------------------------------------------------
# FUNDO
# ---------------------------------------------------------
def criar_gradiente_ceu():
    superficie = pygame.Surface((LARGURA, ALTURA))
    for i in range(ALTURA):
        cor = [
            CEU_TOPO[c] + (CEU_BASE[c] - CEU_TOPO[c]) * i // ALTURA
            for c in range(3)
        ]
        pygame.draw.line(superficie, cor, (0, i), (LARGURA, i))
    for raio, alpha in [(70, 40), (55, 60), (40, 90)]:
        halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*AMARELO_SOL, alpha), (raio, raio), raio)
        superficie.blit(halo, (650 - raio, 70 - raio), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(superficie, AMARELO_SOL, (650, 70), 30)
    return superficie


FUNDO_GRADIENTE = criar_gradiente_ceu()


def desenhar_fundo(canvas, camera_x):
    canvas.blit(FUNDO_GRADIENTE, (0, 0))

    for nx, ny in [(-100, 80), (250, 40), (600, 90), (950, 50), (1300, 80), (1650, 40), (2000, 90),
                    (2350, 60), (2700, 90), (3050, 50)]:
        x = nx - camera_x * 0.15
        if -200 < x < LARGURA + 200:
            pygame.draw.polygon(canvas, ROXO_CLARO, [(x, 400), (x + 100, 300), (x + 200, 400)])

    for nx, ny in [(100, 60), (400, 100), (700, 50), (1000, 80), (1400, 60), (1800, 100), (2200, 60),
                    (2600, 90), (3000, 50)]:
        x = nx - camera_x * 0.3
        if -100 < x < LARGURA + 100:
            pygame.draw.ellipse(canvas, AZUL_NUVEM, (x, ny, 80, 35))
            pygame.draw.ellipse(canvas, AZUL_NUVEM, (x + 25, ny - 15, 60, 35))


def desenhar_plataformas(canvas, camera_x, plataformas):
    for plat in plataformas:
        x = plat.x - camera_x
        if x + plat.width < 0 or x > LARGURA:
            continue
        corpo = pygame.Rect(x, plat.y + 8, plat.width, plat.height - 8)
        pygame.draw.rect(canvas, MARROM_TERRA, corpo)
        pygame.draw.rect(canvas, VERDE_GRAMA, (x, plat.y, plat.width, 12))
        pygame.draw.rect(canvas, VERDE_GRAMA_ESCURO, (x, plat.y + 10, plat.width, 3))
        for tufo_x in range(0, plat.width, 14):
            pygame.draw.line(canvas, VERDE_TUFO, (x + tufo_x + 3, plat.y + 2), (x + tufo_x + 1, plat.y - 4), 2)
            pygame.draw.line(canvas, VERDE_TUFO, (x + tufo_x + 7, plat.y + 2), (x + tufo_x + 8, plat.y - 5), 2)


DURACAO_SOLAVANCO = 5  # quadros que o bloco "balanca" antes de quebrar de vez


def desenhar_blocos(canvas, camera_x, blocos):
    for bloco in blocos:
        estado = bloco["estado"]
        if estado == "sumiu":
            continue
        r = bloco["rect"]
        x = r.x - camera_x
        if x + r.width < 0 or x > LARGURA:
            continue

        offset_y = 0
        if estado == "batendo":
            # pequeno solavanco pra cima (feito com uma curva de seno)
            # antes do bloco se estilhacar de vez -- da a sensacao de
            # impacto fisico real, como um bloco de verdade sendo
            # golpeado por baixo, em vez de quebrar instantaneamente.
            progresso = bloco["timer"] / DURACAO_SOLAVANCO
            offset_y = -7 * math.sin(progresso * math.pi)

        rect_tela = pygame.Rect(x, r.y + offset_y, r.width, r.height)
        pygame.draw.rect(canvas, TIJOLO, rect_tela)
        pygame.draw.rect(canvas, TIJOLO_ESCURO, rect_tela, 3)
        pygame.draw.line(canvas, TIJOLO_ESCURO, (rect_tela.x, rect_tela.y + rect_tela.height // 2),
                          (rect_tela.x + rect_tela.width, rect_tela.y + rect_tela.height // 2), 2)


def atualizar_blocos(blocos, gato, moedas):
    gato_rect = gato.rect()
    for bloco in blocos:
        if bloco["estado"] == "intacto":
            r = bloco["rect"]
            if gato_rect.colliderect(r):
                if gato.vel_y < 0 and gato_rect.top - gato.vel_y >= r.bottom - 10:
                    # bateu por baixo -> comeca a quebrar
                    bloco["estado"] = "batendo"
                    bloco["timer"] = DURACAO_SOLAVANCO
                    gato.vel_y = 2
                elif gato.vel_y >= 0 and gato_rect.bottom - gato.vel_y <= r.top + 10:
                    # caiu/pousou em cima -> bloco funciona como plataforma solida
                    gato.y = r.top - gato.altura
                    gato.vel_y = 0
                    gato.no_chao = True
                    gato.pulo_duplo_usado = False
                    gato.quadros_fora_do_chao = 0
                    gato_rect = gato.rect()
        elif bloco["estado"] == "batendo":
            r = bloco["rect"]
            # enquanto o bloco ainda esta "balancando" antes de estourar,
            # ele continua solido por cima, entao o gato nao cai de repente
            if gato.vel_y >= 0 and gato_rect.colliderect(r) and gato_rect.bottom - gato.vel_y <= r.top + 10:
                gato.y = r.top - gato.altura
                gato.vel_y = 0
                gato.no_chao = True
                gato.pulo_duplo_usado = False
                gato.quadros_fora_do_chao = 0
                gato_rect = gato.rect()

            bloco["timer"] -= 1
            if bloco["timer"] <= 0:
                bloco["estado"] = "sumiu"
                tocar("quebrar")
                espalhar_fragmentos_bloco(r)
                espalhar_particulas(r.centerx, r.bottom - 4, (190, 190, 195), 6)
                if bloco["com_moeda"]:
                    moedas.append(pygame.Rect(r.x + 8, r.y - 30, 20, 20))


def desenhar_moedas(canvas, camera_x, moedas, quadro):
    largura_moeda = max(4, int(20 * abs(math.cos(quadro * 0.08))))
    for m in moedas:
        x = m.x - camera_x
        if x + m.width < 0 or x > LARGURA:
            continue
        centro_x = x + m.width // 2
        centro_y = m.y + m.height // 2
        pygame.draw.ellipse(canvas, AMARELO_MOEDA,
                             (centro_x - largura_moeda // 2, m.y, largura_moeda, m.height))
        pygame.draw.ellipse(canvas, AMARELO_MOEDA_ESCURO,
                             (centro_x - largura_moeda // 2, m.y, largura_moeda, m.height), 2)


def atualizar_moedas(moedas, gato):
    gato_rect = gato.rect()
    coletadas = [m for m in moedas if gato_rect.colliderect(m)]
    for m in coletadas:
        espalhar_particulas(m.centerx, m.centery, AMARELO_MOEDA, 8)
        gato.pontos += 10
        tocar("moeda")
    moedas[:] = [m for m in moedas if m not in coletadas]


def desenhar_inimigos(canvas, camera_x, inimigos):
    for inimigo in inimigos:
        if not inimigo["vivo"]:
            continue
        r = inimigo["rect"]
        x = r.x - camera_x
        if x + r.width < 0 or x > LARGURA:
            continue

        if inimigo["tipo"] == "voador":
            # asas simples, batendo
            bater = 6 * math.sin(pygame.time.get_ticks() * 0.02)
            pygame.draw.ellipse(canvas, (240, 240, 255), (x - 8, r.y + 8 + bater, 14, 8))
            pygame.draw.ellipse(canvas, (240, 240, 255), (x + r.width - 6, r.y + 8 - bater, 14, 8))
            pygame.draw.ellipse(canvas, ROXO, (x, r.y, r.width, r.height))
            pygame.draw.ellipse(canvas, (100, 40, 150), (x, r.y, r.width, r.height), 2)
        else:
            # chifres
            pygame.draw.polygon(canvas, (25, 25, 25), [(x + 5, r.y + 6), (x - 2, r.y - 9), (x + 10, r.y + 3)])
            pygame.draw.polygon(canvas, (25, 25, 25), [(x + r.width - 5, r.y + 6), (x + r.width + 2, r.y - 9), (x + r.width - 10, r.y + 3)])
            pygame.draw.ellipse(canvas, VERMELHO, (x, r.y, r.width, r.height))
            pygame.draw.ellipse(canvas, (110, 15, 15), (x, r.y, r.width, r.height), 2)

        pygame.draw.circle(canvas, BRANCO, (int(x + r.width * 0.3), r.y + 10), 4)
        pygame.draw.circle(canvas, BRANCO, (int(x + r.width * 0.7), r.y + 10), 4)
        pygame.draw.circle(canvas, PRETO, (int(x + r.width * 0.3), r.y + 10), 2)
        pygame.draw.circle(canvas, PRETO, (int(x + r.width * 0.7), r.y + 10), 2)


def atualizar_inimigos(inimigos, gato):
    gato_rect = gato.rect()
    for inimigo in inimigos:
        if not inimigo["vivo"]:
            continue
        r = inimigo["rect"]
        r.x += inimigo["vel"]
        if r.x < inimigo["min_x"] or r.x > inimigo["max_x"]:
            inimigo["vel"] *= -1
            r.x = max(inimigo["min_x"], min(r.x, inimigo["max_x"]))

        if inimigo["tipo"] == "voador":
            inimigo["fase"] += 0.05
            r.y = int(inimigo["base_y"] + 25 * math.sin(inimigo["fase"]))

        if gato_rect.colliderect(r):
            if gato.vel_y > 0 and gato_rect.bottom - gato.vel_y <= r.top + 12:
                inimigo["vivo"] = False
                gato.vel_y = PULO_FORCA * 0.6
                gato.pontos += 50
                tocar("stomp")
                espalhar_particulas(r.centerx, r.centery, ROXO, 10)
            elif gato.invencivel == 0:
                gato.perder_vida()


def desenhar_powerups(canvas, camera_x, powerups, quadro):
    for p in powerups:
        if p["coletado"]:
            continue
        r = p["rect"]
        x = r.x - camera_x
        if x + r.width < 0 or x > LARGURA:
            continue
        centro = (int(x + r.width // 2), int(r.y + r.height // 2))
        pulso = 3 * math.sin(quadro * 0.12)
        raio = int(15 + pulso)

        cor_halo = (100, 220, 255, 70) if p["tipo"] == "pulo_duplo" else (100, 255, 170, 70)
        cor_bola = (60, 170, 255) if p["tipo"] == "pulo_duplo" else (40, 200, 130)

        halo = pygame.Surface((raio * 3, raio * 3), pygame.SRCALPHA)
        pygame.draw.circle(halo, cor_halo, (raio * 3 // 2, raio * 3 // 2), raio + 6)
        canvas.blit(halo, (centro[0] - raio * 3 // 2, centro[1] - raio * 3 // 2), special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.circle(canvas, cor_bola, centro, raio)
        pygame.draw.circle(canvas, BRANCO, centro, raio, 2)

        cx_i, cy_i = centro
        if p["tipo"] == "pulo_duplo":
            # icone de seta dupla pra cima (representa o pulo duplo)
            pygame.draw.polygon(canvas, BRANCO, [(cx_i, cy_i - 9), (cx_i - 6, cy_i - 2), (cx_i + 6, cy_i - 2)])
            pygame.draw.polygon(canvas, BRANCO, [(cx_i, cy_i - 1), (cx_i - 6, cy_i + 6), (cx_i + 6, cy_i + 6)])
        else:
            # icone de raio (representa o turbo de velocidade)
            pygame.draw.polygon(canvas, BRANCO, [
                (cx_i + 4, cy_i - 10), (cx_i - 6, cy_i + 2), (cx_i, cy_i + 2),
                (cx_i - 4, cy_i + 10), (cx_i + 6, cy_i - 2), (cx_i, cy_i - 2),
            ])


def atualizar_powerups(powerups, gato):
    gato_rect = gato.rect()
    for p in powerups:
        if not p["coletado"] and gato_rect.colliderect(p["rect"]):
            p["coletado"] = True
            if p["tipo"] == "pulo_duplo":
                gato.tem_pulo_duplo = True
            elif p["tipo"] == "turbo":
                gato.turbo_timer = 60 * 8  # 8 segundos de velocidade extra
            espalhar_particulas(p["rect"].centerx, p["rect"].centery, (100, 200, 255), 14)
            tocar("powerup")


def desenhar_bandeira(canvas, camera_x, bandeira):
    x = bandeira.x - camera_x
    if x + bandeira.width < 0 or x > LARGURA:
        return
    pygame.draw.rect(canvas, (200, 200, 200), (x, bandeira.y, bandeira.width, bandeira.height))
    pygame.draw.polygon(canvas, VERMELHO, [(x + bandeira.width, bandeira.y + 5),
                                            (x + bandeira.width + 35, bandeira.y + 20),
                                            (x + bandeira.width, bandeira.y + 35)])


def desenhar_hud(canvas, gato):
    painel = pygame.Surface((230, 60), pygame.SRCALPHA)
    pygame.draw.rect(painel, HUD_FUNDO, painel.get_rect(), border_radius=14)
    canvas.blit(painel, (15, 15))

    for i in range(3):
        cor = LARANJA_GATO if i < gato.vidas else (90, 90, 90)
        pygame.draw.circle(canvas, cor, (40 + i * 28, 35), 10)
        pygame.draw.circle(canvas, PRETO, (40 + i * 28, 35), 10, 2)

    pygame.draw.circle(canvas, AMARELO_MOEDA, (40, 60), 8)
    pygame.draw.circle(canvas, AMARELO_MOEDA_ESCURO, (40, 60), 8, 2)
    texto = FONTE.render(f"x {gato.pontos}", True, BRANCO)
    canvas.blit(texto, (58, 50))

    badge_x = LARGURA - 107
    if gato.tem_pulo_duplo:
        badge = pygame.Surface((92, 34), pygame.SRCALPHA)
        pygame.draw.rect(badge, (20, 30, 60, 160), badge.get_rect(), border_radius=12)
        canvas.blit(badge, (badge_x, 15))
        texto_badge = FONTE_PEQUENA.render("PULO 2X", True, (130, 210, 255))
        canvas.blit(texto_badge, (badge_x + 10, 26))
        badge_x -= 100

    if gato.turbo_timer > 0:
        badge = pygame.Surface((92, 34), pygame.SRCALPHA)
        pygame.draw.rect(badge, (15, 50, 35, 160), badge.get_rect(), border_radius=12)
        canvas.blit(badge, (badge_x, 15))
        segundos = gato.turbo_timer // 60 + 1
        texto_badge = FONTE_PEQUENA.render(f"TURBO {segundos}s", True, VERDE_SPEED)
        canvas.blit(texto_badge, (badge_x + 6, 26))

    versao = FONTE_PEQUENA.render(VERSAO_JOGO.split(" - ")[0], True, (255, 255, 255, 120))
    canvas.blit(versao, (LARGURA - versao.get_width() - 8, ALTURA - 20))


def desenhar_menu(canvas, quadro, gato_menu):
    desenhar_fundo(canvas, 0)
    chao = pygame.Rect(-50, 400, LARGURA + 100, 60)
    desenhar_plataformas(canvas, 0, [chao])
    gato_menu.desenhar(canvas, 0)

    sombra_titulo = FONTE_GRANDE.render("GATO AVENTUREIRO", True, PRETO)
    titulo = FONTE_GRANDE.render("GATO AVENTUREIRO", True, BRANCO)
    tx = LARGURA // 2 - titulo.get_width() // 2
    ty = 70 + int(4 * math.sin(quadro * 0.05))
    canvas.blit(sombra_titulo, (tx + 3, ty + 3))
    canvas.blit(titulo, (tx, ty))

    if (quadro // 30) % 2 == 0:
        sub = FONTE.render("Toque na tela para jogar", True, BRANCO)
        canvas.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 190))

    dica = FONTE_PEQUENA.render(
        "Botoes na tela (ou setas + espaco) para mover e pular", True, BRANCO)
    canvas.blit(dica, (LARGURA // 2 - dica.get_width() // 2, ALTURA - 30))

    versao = FONTE_PEQUENA.render(VERSAO_JOGO.split(" - ")[0], True, BRANCO)
    canvas.blit(versao, (10, ALTURA - 20))


def tela_mensagem(canvas, titulo, subtitulo, cor_titulo):
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    canvas.blit(overlay, (0, 0))

    texto1 = FONTE_GRANDE.render(titulo, True, cor_titulo)
    canvas.blit(texto1, (LARGURA // 2 - texto1.get_width() // 2, ALTURA // 2 - 60))

    texto2 = FONTE.render(subtitulo, True, BRANCO)
    canvas.blit(texto2, (LARGURA // 2 - texto2.get_width() // 2, ALTURA // 2 + 10))

    texto3 = FONTE_PEQUENA.render("Toque na tela para jogar novamente", True, BRANCO)
    canvas.blit(texto3, (LARGURA // 2 - texto3.get_width() // 2, ALTURA // 2 + 55))


# ---------------------------------------------------------
# LOOP PRINCIPAL
# ---------------------------------------------------------
def novo_jogo():
    (plataformas, plataformas_moveis, espinhos, blocos, moedas,
     inimigos, powerups, bandeira, fim_fase_x) = criar_fase()
    gato = Gato(60, 100)
    PARTICULAS.clear()
    FRAGMENTOS.clear()
    return {
        "gato": gato,
        "plataformas": plataformas,
        "plataformas_moveis": plataformas_moveis,
        "espinhos": espinhos,
        "blocos": blocos,
        "moedas": moedas,
        "inimigos": inimigos,
        "powerups": powerups,
        "bandeira": bandeira,
        "fim_fase_x": fim_fase_x,
        "camera_x": 0,
        "estado": "jogando",  # jogando | venceu | perdeu
    }


def main():
    tela_carregando()
    carregar_audio()
    tocar_musica()

    tela_atual = "menu"  # "menu" ou "jogo"
    jogo = None
    gato_menu = Gato(LARGURA // 2 - 20, 360)
    quadro = 0
    rodando = True

    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                rodando = False
            elif evento.type in (pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION,
                                  pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                if tela_atual == "jogo":
                    CONTROLES.processar_evento(evento)
                if evento.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    if tela_atual == "menu":
                        tela_atual = "jogo"
                        jogo = novo_jogo()
                    elif jogo is not None and jogo["estado"] != "jogando":
                        jogo = novo_jogo()
            elif evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                if tela_atual == "menu":
                    tela_atual = "jogo"
                    jogo = novo_jogo()
                elif jogo is not None and jogo["estado"] != "jogando":
                    jogo = novo_jogo()

        teclas = pygame.key.get_pressed()

        if tela_atual == "menu":
            gato_menu.andando += 1
            gato_menu.no_chao = True
            desenhar_menu(CANVAS, quadro, gato_menu)
        else:
            gato = jogo["gato"]

            if jogo["estado"] == "jogando":
                for pm in jogo["plataformas_moveis"]:
                    pm.atualizar()

                # monta a lista de plataformas solidas (fixas + moveis) e
                # guarda o deslocamento de cada plataforma movel num
                # dicionario separado (nao da pra "colar" atributos extras
                # direto num pygame.Rect)
                plataformas_solidas = list(jogo["plataformas"])
                deslocamentos = {}
                for pm in jogo["plataformas_moveis"]:
                    r = pm.rect()
                    plataformas_solidas.append(r)
                    deslocamentos[id(r)] = pm.deslocamento_x

                gato.atualizar(teclas, plataformas_solidas, CONTROLES, deslocamentos)
                atualizar_blocos(jogo["blocos"], gato, jogo["moedas"])
                atualizar_moedas(jogo["moedas"], gato)
                atualizar_inimigos(jogo["inimigos"], gato)
                atualizar_powerups(jogo["powerups"], gato)
                checar_espinhos(jogo["espinhos"], gato)
                atualizar_particulas()
                atualizar_fragmentos(plataformas_solidas)

                # camera segue mais rapido, acompanhando o ritmo mais agil do jogo
                alvo_camera = gato.x - LARGURA // 3
                jogo["camera_x"] += (alvo_camera - jogo["camera_x"]) * 0.15
                jogo["camera_x"] = max(0, min(jogo["camera_x"], jogo["fim_fase_x"] - LARGURA + 100))

                if gato.rect().colliderect(jogo["bandeira"]):
                    jogo["estado"] = "venceu"
                    tocar("vencer")
                elif gato.vidas <= 0:
                    jogo["estado"] = "perdeu"
                    tocar("perder_jogo")

            desenhar_fundo(CANVAS, jogo["camera_x"])
            desenhar_plataformas(CANVAS, jogo["camera_x"], jogo["plataformas"])
            for pm in jogo["plataformas_moveis"]:
                pm.desenhar(CANVAS, jogo["camera_x"])
            desenhar_espinhos(CANVAS, jogo["camera_x"], jogo["espinhos"])
            desenhar_blocos(CANVAS, jogo["camera_x"], jogo["blocos"])
            desenhar_fragmentos(CANVAS, jogo["camera_x"])
            desenhar_bandeira(CANVAS, jogo["camera_x"], jogo["bandeira"])
            desenhar_moedas(CANVAS, jogo["camera_x"], jogo["moedas"], quadro)
            desenhar_powerups(CANVAS, jogo["camera_x"], jogo["powerups"], quadro)
            desenhar_inimigos(CANVAS, jogo["camera_x"], jogo["inimigos"])
            desenhar_particulas(CANVAS, jogo["camera_x"])
            gato.desenhar(CANVAS, jogo["camera_x"])
            desenhar_hud(CANVAS, gato)
            CONTROLES.desenhar(CANVAS)

            if jogo["estado"] == "venceu":
                tela_mensagem(CANVAS, "VOCE VENCEU!", f"Pontos: {gato.pontos}", AMARELO_MOEDA)
            elif jogo["estado"] == "perdeu":
                tela_mensagem(CANVAS, "FIM DE JOGO", f"Pontos: {gato.pontos}", VERMELHO)

        atualizar_tela_real()
        quadro += 1
        RELOGIO.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
