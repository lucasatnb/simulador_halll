from ursina import Button, Entity, Text, Vec4, application, camera, color, invoke, window
from ursina.prefabs.slider import Slider

from .config import B_MAX, B_MIN, CORRENTE_MAX_MA, CORRENTE_MIN_MA, DIAMETRO_FIO_M, PLACA, VETORES


# region Unidade do voltimetro
# Exibe nV, uV ou mV conforme a ordem de grandeza da tensao.
def formatar_tensao(v_volts):
    v_abs = abs(v_volts)
    if v_abs < 1e-6:
        return f'{v_volts * 1e9:.2f} nV'
    elif v_abs < 1e-3:
        return f'{v_volts * 1e6:.2f} uV'
    else:
        return f'{v_volts * 1e3:.2f} mV'
# endregion


class InterfaceSimulador:
    # region Controles e leituras na tela
    # Corrente e campo ficam no rodape. Leituras e botao Sair acompanham as bordas da janela.
    def __init__(self):
        self.botao_sair = Button(
            parent=camera.ui, text='Sair', scale=(0.10, 0.045), y=0.45,
            color=color.Color(0.35, 0.13, 0.13, 1), text_size=0.85,
            on_click=application.quit,
        )
        Entity(parent=camera.ui, model='quad', position=(0, -0.385, 0.1),
               scale=(1.12, 0.18), color=Vec4(0.10, 0.11, 0.12, 0.96))
        self.dica_ajuda = Text(text='H - Fechar', position=(0.39, -0.435), scale=0.75)
        self.texto_sentido = Text(text='Sentido: normal', position=(-0.5, -0.435), scale=0.8)
        self.texto_cooldown = Text(text='', position=(-0.13, -0.435), scale=0.75,
                                  color=color.light_gray)
        self.corrente_slider = Slider(min=CORRENTE_MIN_MA, max=CORRENTE_MAX_MA,
                                      default=20, step=1, dynamic=True,
                                      x=-0.49, y=-0.375, scale=0.82)
        self.texto_corrente = Text(text='Corrente: 20 mA', position=(-0.5, -0.32), scale=0.95)
        self.b_slider = Slider(min=B_MIN, max=B_MAX, default=50, step=10,
                               dynamic=True, x=0.08, y=-0.375, scale=0.82)
        self.texto_b = Text(text='Campo B: 50 mT', position=(0.07, -0.32), scale=0.95)
        for slider in (self.corrente_slider, self.b_slider):
            slider.knob.text_entity.enabled = False
        self.leituras = Entity(parent=camera.ui)
        self.texto_voltimetro = Text(parent=self.leituras, text='Voltimetro (V_H): 0 nV',
                                    y=0.45, scale=1.05)
        self._criar_ajuda()
        self._criar_legenda()
        self._posicionar_interface()
        invoke(self._fechar_ajuda_automaticamente, delay=2)

    def _posicionar_interface(self):
        self.leituras.x = -window.aspect_ratio / 2 + 0.04
        self.botao_sair.x = window.aspect_ratio / 2 - 0.09
    # endregion

    # region Valores dos sliders
    # Fornece corrente em mA e campo em mT para a simulacao.
    @property
    def corrente_ma(self):
        return self.corrente_slider.value

    @property
    def campo_mt(self):
        return self.b_slider.value
    # endregion

    # region Estado exibido
    # Atualiza leituras, sentido da corrente, tempo de espera e visibilidade da ajuda.
    def alternar_ajuda(self):
        self.popup_comandos.enabled = not self.popup_comandos.enabled
        self.dica_ajuda.text = 'H - Fechar' if self.popup_comandos.enabled else 'H - Ajuda'

    def _fechar_ajuda_automaticamente(self):
        if self.popup_comandos.enabled:
            self.popup_comandos.enabled = False
            self.dica_ajuda.text = 'H - Ajuda'

    def atualizar(self, tensao, sentido, cooldown):
        self._posicionar_interface()
        self.texto_corrente.text = f'Corrente: {self.corrente_ma:.0f} mA'
        self.texto_b.text = f'Campo B: {self.campo_mt:.0f} mT'
        self.texto_voltimetro.text = f'Voltimetro (V_H): {formatar_tensao(tensao)}'
        self.texto_sentido.text = 'Sentido: normal' if sentido > 0 else 'Sentido: invertido'
        self.texto_cooldown.text = f'Aguarde {cooldown:.1f}s' if cooldown > 0 else ''
    # endregion

    # region Ajuda e legenda
    # A ajuda abre com H. Cores identificam os vetores; cruz e ponto indicam entrada e saida do
    # plano.
    def _criar_ajuda(self):
        self.popup_comandos = Entity(parent=camera.ui, enabled=True, z=-1)
        Entity(parent=self.popup_comandos, model='quad', scale=(0.64, 0.38),
               color=Vec4(0.10, 0.11, 0.12, 1), z=0.1)
        Text(parent=self.popup_comandos,
             text=('COMANDOS\n\n'
                   'M - descer / subir o ima\n'
                   'I - inverter a corrente e a pilha\n'
                   'F - inverter os polos\n\n'
                   'Botao direito - girar a camera\n'
                   'Roda do mouse - aproximar / afastar\n\n'
                   'H - fechar ajuda'),
             position=(-0.27, 0.15), scale=0.85, line_height=1.25)

    def _criar_legenda(self):
        Text(parent=self.leituras, text='Vetores do eletron', y=0.35,
             scale=0.8, color=color.light_gray)
        for i, (rotulo, descricao, cor) in enumerate(VETORES.values()):
            Text(parent=self.leituras, text=f'{rotulo}: {descricao}',
                 y=0.315 - i * 0.033, scale=0.85, color=cor)
        Text(parent=self.leituras,
             text='Cruz: entrando no plano\nPonto: saindo do plano',
             y=0.20, scale=0.7, color=color.light_gray)
        Text(parent=self.leituras,
             text=(f'Fio de cobre, diametro assumido: {DIAMETRO_FIO_M * 1000:.1f} mm\n'
                   f'Placa de cobre, espessura {PLACA.espessura * 1000:.2f} mm\n'
                   '(por isso V_H fica na casa de nV: cobre tem n alto,\n'
                   'sensores Hall reais usam semicondutor)'),
             y=0.11, scale=0.62, color=color.light_gray)
        Text(parent=self.leituras, text='Eixos na cena: X vermelho, Y verde, Z azul',
             y=-0.03, scale=0.65, color=color.light_gray)
    # endregion
