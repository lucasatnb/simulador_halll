from dataclasses import dataclass

from ursina import Vec3, color


# region Escala visual e controles
# Corrente em mA, campo em mT e espera em segundos. Desvio e velocidade usam a escala da cena.
FATOR_DEFLEXAO_VISUAL = 2
COOLDOWN_TECLAS = 1.0
MARCADORES_POR_FAIXA = 3
FAIXA_CORRENTE_MA = 20
CORRENTE_MIN_MA = 2
CORRENTE_MAX_MA = 100
MAX_MARCADORES_POSSIVEL = (CORRENTE_MAX_MA // FAIXA_CORRENTE_MA) * MARCADORES_POR_FAIXA
VELOCIDADE_MIN = 0.5
VELOCIDADE_MAX = 3.0
Y_IMA_CIMA = 2.7
Y_IMA_BAIXO = 0.8
B_MIN, B_MAX = 0, 200
# endregion


# region Constantes do cobre
# Densidade de portadores em m^-3 e modulo da carga do eletron em coulombs.
N_PORTADORES_COBRE = 8.49e28
CARGA_ELETRON = 1.6e-19
# Diametro assumido do fio (m), so pra fechar a area de secao transversal na velocidade de
# deriva -- a cena nao modela o fio em escala real, entao e um palpite razoavel (fio fino de
# bancada), nao uma medida do modelo 3D.
DIAMETRO_FIO_M = 1e-3
# endregion


# region Coordenadas do circuito
# Parte do terminal preto, percorre o fio, cruza a placa entre os pontos 3 e 4 e termina no terminal
# laranja.
CAMINHO = [
    Vec3(-1.001, 0.2, -0.255),
    Vec3(-1.001, 0.2, -1.367),
    Vec3(0.811,  0.2, -1.367),
    Vec3(0.811,  0.2, -0.739),
    Vec3(0.811,  0.2,  0.994),
    Vec3(0.811,  0.2,  1.433),
    Vec3(-1.007, 0.2,  1.415),
    Vec3(-1.007, 0.2,  0.336),
]
# endregion

# region Geometria da placa
# Limites em coordenadas da cena; espessura fisica em metros para o calculo de V_H.
@dataclass(frozen=True)
class Placa:
    minimo: Vec3
    maximo: Vec3
    espessura: float = 1.5e-4
    eixo_corrente: float = 0.811
    segmento_caminho: int = 3

    @property
    def centro_x(self):
        return (self.minimo.x + self.maximo.x) / 2

    @property
    def centro_z(self):
        return (self.minimo.z + self.maximo.z) / 2


PLACA = Placa(Vec3(0.208, 0.2, -0.637), Vec3(1.346, 0.2, 0.906))
# endregion


# region Identificacao dos vetores
# Cada entrada define rotulo, descricao e cor. A ordem e a mesma na legenda e nos indicadores.
VETORES = {
    'velocidade': ('v_e', 'velocidade', color.lime),
    'forca': ('F_B', 'forca magnetica', color.orange),
    'campo': ('B', 'campo magnetico', color.azure),
}
# endregion
