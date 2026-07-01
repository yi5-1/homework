"""
🌧️ 場景：出門帶傘的時機（下雨天 或 出大太陽）
我們什麼時候會想要帶傘出門？下雨天（怕淋濕）或者大太陽（怕曬黑）。
只要中一個就得帶！
"""
is_raining = False
is_sunny = True
# 只要其中一個是 True，結果就是 True
if is_raining == True or is_sunny == True:
    print("記得帶傘出門 ☂️")
else:
    print("天氣真舒服，不用帶傘！")