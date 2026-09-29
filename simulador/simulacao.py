from ursina import EditorCamera, Entity, Vec3, camera, color, invoke, time

from . import config
from .fisica import calcular_forca_magnetica, calcular_tensao_hall, calcular_velocidade_deriva
from .interface import InterfaceSimulador
from .particulas import Percurso, SistemaBolinhasCircuito, SistemaBolinhasHall
from .vetores import ReferencialEixos, VetoresEletron


class SimulacaoHall(Entity):
    # region Estado inicial
    # Comeca com o ima afastado e as particulas no percurso sem desvio.
    def __init__(self):
        super().__init__()
        self.magneto_baixo = False
        self.magneto_invertido = False
        self.sentido_corrente = 1
        self.cooldown_restante = 0.0

        self._criar_cena()
        self.interface = InterfaceSimulador()
        self.vetores_eletron = VetoresEletron()
        percurso = Percurso(config.CAMINHO)
        self.sistema_circuito = SistemaBolinhasCircuito(percurso)
        self.sistema_hall = SistemaBolinhasHall(percurso, config.PLACA, config.B_MAX)
        self.sistema_atual = self.sistema_circuito
    # endregion

    # region Cena e pivos
    # Pilha e ima giram pelo centro dos modelos; o circuito permanece fixo.
    def _criar_cena(self):
        self.camera_editor = EditorCamera(rotation=(45, 0, 0), position=(0.35, -0.4, 0))
        camera.z = -13
        self.camera_editor.target_z = camera.z
        self.modelo = Entity(model='models/circuito_sem_pilha.glb', scale=0.02)
        self.pilha = Entity(scale=0.02)
        self.corpo_pilha = Entity(parent=self.pilha, model='models/pilha.glb')
        minimo, maximo = self.corpo_pilha.model.getTightBounds()
        centro = (minimo + maximo) / 2
        self.corpo_pilha.model.setPos(-centro)
        self.pilha.position = centro * self.pilha.scale_x
        self.chao = Entity(model='plane', scale=20, color=color.dark_gray, y=-1)
        self.referencial_eixos = ReferencialEixos(Vec3(-1.3, 0.05, -1.6))
        self.ima = Entity(model='models/ima.glb', scale=0.02,
                          position=(config.PLACA.centro_x, 2.5, config.PLACA.centro_z))
        limites = self.ima.model.getTightBounds()
        if limites:
            self.ima.model.setPos(-(limites[0] + limites[1]) / 2)
    # endregion

    # region Teclado
    # M, I e F respeitam o intervalo entre comandos. H alterna a ajuda a qualquer momento.
    def input(self, key):
        if key == 'h':
            self.interface.alternar_ajuda()
            return
        if self.cooldown_restante > 0:
            return
        if key == 'm':
            self._acionar_ima()
        elif key == 'i':
            self._inverter_corrente()
        elif key == 'f':
            self.magneto_invertido = not self.magneto_invertido
            self.ima.animate_rotation_z(self.ima.rotation_z + 180, duration=0.6)
        else:
            return
        self.cooldown_restante = config.COOLDOWN_TECLAS
    # endregion

    # region Inversao da corrente e da pilha
    # O giro em Y troca os terminais; o giro local em Z mantem os sinais voltados para dentro.
    def _inverter_corrente(self):
        self.sentido_corrente *= -1

        angulo = 180 if self.sentido_corrente < 0 else 0
        self.pilha.animate_rotation_y(angulo, duration=0.6)

        self.corpo_pilha.animate_rotation_z(angulo, duration=0.6)
    # endregion

    # region Entrada e saida do campo na placa
    # Troca o sistema de particulas ao terminar o deslocamento do ima.
    def _acionar_ima(self):
        self.magneto_baixo = not self.magneto_baixo
        altura = config.Y_IMA_BAIXO if self.magneto_baixo else config.Y_IMA_CIMA
        self.ima.animate_position(
            (config.PLACA.centro_x, altura, config.PLACA.centro_z), duration=1)
        if self.magneto_baixo:
            self.sistema_circuito.set_ativo(False)
            invoke(self._ativar_hall, delay=1)
        else:
            self.sistema_hall.set_ativo(False)
            invoke(self._ativar_circuito, delay=1)

    def _ativar_hall(self):
        self.sistema_hall.set_ativo(True)
        self.sistema_atual = self.sistema_hall

    def _ativar_circuito(self):
        self.sistema_circuito.set_ativo(True)
        self.sistema_atual = self.sistema_circuito
    # endregion

    # region Atualizacao por quadro
    # Os sliders definem I e B. A velocidade visual varia com I; a tensao usa B = 0 com o ima
    # afastado.
    def update(self):
        self.cooldown_restante = max(0.0, self.cooldown_restante - time.dt)
        corrente_ma = self.interface.corrente_ma
        campo_mt = self.interface.campo_mt
        sinal_polo = -1 if self.magneto_invertido else 1
        fracao_velocidade = ((corrente_ma - config.CORRENTE_MIN_MA)
                             / (config.CORRENTE_MAX_MA - config.CORRENTE_MIN_MA))
        velocidade = (config.VELOCIDADE_MIN
                      + fracao_velocidade * (config.VELOCIDADE_MAX - config.VELOCIDADE_MIN))
        velocidade *= self.sentido_corrente

        fracao_corrente = corrente_ma / config.CORRENTE_MAX_MA
        self.sistema_hall.campo_b_mt = campo_mt * sinal_polo
        self.sistema_hall.frac_corrente = fracao_corrente
        self.sistema_hall.corrente_mA = corrente_ma
        campo_efetivo = campo_mt if self.magneto_baixo else 0
        tensao = calcular_tensao_hall(
            corrente_ma, campo_efetivo, self.sentido_corrente, sinal_polo)
        self.interface.atualizar(tensao, self.sentido_corrente, self.cooldown_restante)
        self.sistema_atual.update(velocidade, time.dt)

        velocidade_deriva = calcular_velocidade_deriva(corrente_ma)
        forca = calcular_forca_magnetica(velocidade_deriva, campo_efetivo)
        self.vetores_eletron.update(
            self.sentido_corrente, sinal_polo,
            self.magneto_baixo and self.sistema_hall.ativo and campo_mt > 0,
            velocidade_ms=velocidade_deriva, campo_mt=campo_efetivo, forca_n=forca,
        )
    # endregion