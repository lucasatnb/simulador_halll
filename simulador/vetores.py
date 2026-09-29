import math

from ursina import Entity, Text, Vec3, Vec4, camera, color, load_model, scene, window

from .config import VETORES
from .fisica import direcoes_vetores_eletron


# region Unidades dos valores exibidos
# Escolhe a unidade conforme a ordem de grandeza; forca fica em notacao cientifica por ser
# tipicamente muito pequena (ordem de 1e-20 N).
def formatar_velocidade(v_ms):
    v_abs = abs(v_ms)
    if v_abs < 1e-3:
        return f'{v_ms * 1e6:.2f} um/s'
    if v_abs < 1:
        return f'{v_ms * 1e3:.2f} mm/s'
    return f'{v_ms:.2f} m/s'


def formatar_campo(campo_mt):
    return f'{campo_mt:.0f} mT'


def formatar_forca(forca_n):
    if forca_n == 0:
        return '0 N'
    return f'{forca_n:.2e} N'


FORMATADORES = {
    'velocidade': formatar_velocidade,
    'campo': formatar_campo,
    'forca': formatar_forca,
}
# endregion


# region Referencial de eixos do mundo
# Vermelho = X, verde = Y, azul = Z. Fica fixo na cena (nao acompanha a camera.ui), entao ajuda a
# ver a olho nu pra que lado cada eixo aponta ao girar a camera -- sem isso, "esquerda" ou "baixo"
# na tela dependem do angulo e enganam.
class ReferencialEixos:
    TAMANHO = 0.3
    ESPESSURA = 0.015

    def __init__(self, origem):
        eixos = [
            (Vec3(1, 0, 0), color.red, (self.TAMANHO, self.ESPESSURA, self.ESPESSURA)),
            (Vec3(0, 1, 0), color.green, (self.ESPESSURA, self.TAMANHO, self.ESPESSURA)),
            (Vec3(0, 0, 1), color.blue, (self.ESPESSURA, self.ESPESSURA, self.TAMANHO)),
        ]
        self.hastes = [
            Entity(model='cube', color=cor, position=origem + direcao * self.TAMANHO / 2,
                  scale=escala)
            for direcao, cor, escala in eixos
        ]
        self.pontas = [
            Entity(model='sphere', color=cor, scale=self.ESPESSURA * 2.5,
                  position=origem + direcao * self.TAMANHO)
            for direcao, cor, _ in eixos
        ]
# endregion


class IndicadorVetor:
    # region Icone e rotulo do vetor
    # A seta importada aponta para -Z; o giro de 90 graus a coloca em +Y na interface.
    def __init__(self, nome, cor):
        self.nome = nome
        self.grupo = Entity(parent=camera.ui)
        self.giro = Entity(parent=self.grupo)
        self.seta = self._modelo('Arrow', self.giro, cor, 0.045)

        self.seta.rotation_x = 90
        self.entrada = self._modelo('VectorIn', self.grupo, cor, 0.030)
        self.saida = self._modelo('VectorOut', self.grupo, cor, 0.030)
        self.fundo = Entity(parent=self.grupo, model='quad',
                            position=(0.1215, 0, 0.01), scale=(0.19, 0.035),
                            color=Vec4(0.047, 0.063, 0.086, 0.96))
        Entity(parent=self.grupo, model='quad', position=(0.028, 0, -0.01),
               scale=(0.003, 0.035), color=cor)
        self.rotulo = Text(parent=self.grupo, text=nome, color=color.white,
                           position=(0.1215, 0, -0.02), origin=(0, 0), scale=0.68)
        self.modo = 'seta'
    # endregion

    # region Escala dos icones
    # Centraliza cada GLB e ajusta sua maior dimensao ao tamanho definido para a tela.
    @staticmethod
    def _modelo(nome, pai, cor, tamanho):
        entidade = Entity(parent=pai,
                          model=load_model(f'models/{nome}.glb', use_deepcopy=True),
                          color=cor, unlit=True, double_sided=True)
        minimo, maximo = entidade.model.getTightBounds()
        entidade.model.setPos(-(minimo + maximo) / 2)
        entidade.scale = tamanho / max(maximo - minimo)
        return entidade
    # endregion

    # region Projecao na camera
    # Usa cruz ou ponto a menos de 28 graus do eixo visual; volta a seta acima de 35 graus para
    # evitar oscilacao.
    def update(self, direcao, ativo, texto_valor=None):
        local = camera.getRelativeVector(scene, direcao).normalized()

        limite = 0.82 if self.modo in ('entrada', 'saida') else 0.88
        if abs(local.z) >= limite:
            self.modo = 'entrada' if local.z > 0 else 'saida'
        else:
            self.modo = 'seta'
            self.giro.rotation_z = math.degrees(math.atan2(local.x, local.y))
        self.seta.enabled = ativo and self.modo == 'seta'
        self.entrada.enabled = ativo and self.modo == 'entrada'
        self.saida.enabled = ativo and self.modo == 'saida'
        if ativo and texto_valor is not None:
            texto = f'{self.nome}: {texto_valor}'
        elif ativo:
            texto = self.nome
        else:
            texto = f'{self.nome} = 0'
        if self.rotulo.text != texto:
            self.rotulo.text = texto
    # endregion


# region Coluna de vetores
# As posicoes seguem a ordem da legenda. Apenas as direcoes e os simbolos acompanham a camera.
class VetoresEletron:
    def __init__(self):
        self.indicadores = {
            chave: IndicadorVetor(rotulo, cor)
            for chave, (rotulo, descricao, cor) in VETORES.items()
        }
        self._posicionar_indicadores()

    def _posicionar_indicadores(self):
        x = window.aspect_ratio / 2 - 0.30
        for linha, indicador in enumerate(self.indicadores.values()):
            indicador.grupo.position = (x, 0.10 - linha * 0.075, 0)

    def update(self, sentido_movimento, sinal_polo, campo_ativo,
               velocidade_ms=0, campo_mt=0, forca_n=0):
        direcoes = direcoes_vetores_eletron(sentido_movimento, sinal_polo)
        valores = {'velocidade': velocidade_ms, 'campo': campo_mt, 'forca': forca_n}
        for chave, direcao in zip(('velocidade', 'campo', 'forca'), direcoes):
            ativo = chave == 'velocidade' or campo_ativo
            texto_valor = FORMATADORES[chave](valores[chave]) if ativo else None
            self.indicadores[chave].update(direcao, ativo, texto_valor)
        self._posicionar_indicadores()
# endregion
