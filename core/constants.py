# core/constants.py
# Минимальные и максимальные ставки
ROLLS_MIN_STARS = "rolls_min_stars"
ROLLS_MAX_STARS = "rolls_max_stars"
ROLLS_MIN_TON = "rolls_min_ton"
ROLLS_MAX_TON = "rolls_max_ton"

# Весовые коэффициенты
ROLLS_WEIGHT_W_STARS = "rolls_weight_w_stars"   # весовая доля Stars при расчёте r
ROLLS_WEIGHT_W_TON = "rolls_weight_w_ton"       # весовая доля Ton при расчёте r
ROLLS_WEIGHT_ALPHA = "rolls_weight_alpha"       # множитель буста вероятности
ROLLS_WEIGHT_GAMMA = "rolls_weight_gamma"       # кривизна зависимости (0.5 = sqrt, 1 = линейно, >1 = выпукло)

# Блокированные сектора (список индексов)
ROLLS_BLOCKED_SECTORS = "rolls_blocked_sectors"
