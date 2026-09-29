import math

from ursina import Vec3

from .config import CARGA_ELETRON, DIAMETRO_FIO_M, N_PORTADORES_COBRE, PLACA

# Area de secao transversal do fio, assumido cilindrico e de cobre (ver DIAMETRO_FIO_M).
AREA_FIO_M2 = math.pi * (DIAMETRO_FIO_M / 2) ** 2


# region Tensao Hall: V_H = I B / (n e t)
# Converte mA e mT para SI. Retorna volts; corrente e polos definem o sinal.
def calcular_tensao_hall(corrente_ma, campo_mt, sentido_corrente, sinal_polo):
    corrente_a = corrente_ma / 1000 * sentido_corrente
    campo_t = campo_mt / 1000 * sinal_polo
    return corrente_a * campo_t / (N_PORTADORES_COBRE * CARGA_ELETRON * PLACA.espessura)
# endregion


# region Velocidade de deriva: v_d = I / (n e A)
# So a magnitude importa aqui -- o sentido do vetor ja vem de direcoes_vetores_eletron.
def calcular_velocidade_deriva(corrente_ma):
    corrente_a = abs(corrente_ma) / 1000
    return corrente_a / (N_PORTADORES_COBRE * CARGA_ELETRON * AREA_FIO_M2)
# endregion


# region Forca magnetica: F = e v_d B
# Usa magnitudes; o sentido do vetor forca ja vem de direcoes_vetores_eletron.
def calcular_forca_magnetica(velocidade_ms, campo_mt):
    campo_t = abs(campo_mt) / 1000
    return CARGA_ELETRON * velocidade_ms * campo_t
# endregion


# region Forca magnetica sobre o eletron
# A placa esta em XZ e B aponta para -Y no estado inicial. Como q < 0, F se opoe a v x B.
def direcoes_vetores_eletron(sentido_movimento, sinal_polo):
    velocidade = Vec3(0, 0, sentido_movimento)
    campo = Vec3(0, -sinal_polo, 0)
    forca = -velocidade.cross(campo)
    return velocidade, campo, forca
# endregion
