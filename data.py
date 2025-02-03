from pathlib import Path

# Get the current directory (which is the strategy folder)
current_dir = Path(__file__).resolve().parent

# Reference the parent directory of the current strategy folder
parent_dir = current_dir.parent

# variables and another stuf
entrada = 0.6   # ths is the minimum qty of money to use
autoentrada = True
porcentajeentrada = 0.075
leverage = 20

timeframe = 3  # esta variable controla cada cuanto se checan las órdenes
slmax = 0.1  # esta variable controla la pérdida máxima
tp = 0.1
sl = 0.01

path = ""
pathGan = str(parent_dir) + "/"

sistema = "tangentZ "
usuario = " ingega "
bahia = 1
bahias = 3  # este controla el ajuste del saldoO

pausa = 10  # son los segundos que el sistema necesita para no empalmar las lecturas de simula.py

barras = 1440   # son los minutos que hacen que el sistema se vaya  a empate

debug_mode = True

# parameters necessaries for strategy
# gap=0.03
distance = 0.015
forbidden_hour = 25
bet = 0.03
time = 20  # this is for prevent loops in each4hrs()
bars = 10  # used for tangent and cv
tangent = 0.025
cv = 0.02

# config for time
hours = 1  # 1 raise zero in preview
minutes = 15  # starts minus 1 minute
seconds = 40

# the review hour
review_hour = 4
review_minute = 60
review_second = 40

interval = "15m"

reverse = True  # in this system it doesn't matter because is double bet
