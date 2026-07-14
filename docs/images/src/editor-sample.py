# 楠 Kusunoki Mono ── エディタ実写用サンプル
"""受注を集計して日報を出す。

全角スペース「　」も可視化される。
"""
from dataclasses import dataclass
from datetime import date


@dataclass
class 注文:
    品名: str
    単価: int          # 税込、円
    数量: int = 1      # 取り寄せは 0


def 集計(注文一覧: list[注文]) -> dict[str, int]:
    """品名ごとの売上。空なら {} を返す。"""
    売上: dict[str, int] = {}
    for o in 注文一覧:
        if o.数量 != 0 and o.単価 >= 0:
            売上[o.品名] = 売上.get(o.品名, 0) + o.単価 * o.数量
    return 売上


注文一覧 = [
    注文("ほうじ茶ラテ", 700, 2),   # 定番
    注文("最中アイス", 380),        # 夏季限定
    注文("楠のどら焼き", 450, 3),
]

合計 = sum(集計(注文一覧).values())
assert 合計 == 700 * 2 + 380 + 450 * 3
print(f"{date.today():%m/%d} の売上は {合計:,} 円")  # => 3,130 円
