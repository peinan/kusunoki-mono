<div align="center">

[English](development.md) | 日本語

</div>

# 開発ノート

パイプラインを変更する人向けに、ビルドの仕組みと各変換の意図を説明する。
ビルドとインストールの手順は [README](../README.ja.md) を参照。

## リポジトリ構成

| パス | 内容 |
| --- | --- |
| `scripts/` | パイプライン本体。`setup.sh` がソースを取得し、`build.sh` がフェーズを順に実行する。変換ごとに Python スクリプトが 1 つ |
| `sources/` | 取得したソースフォント類。gitignore 対象で、バージョンは `setup.sh` で固定 |
| `build/sfms/` | フェーズごとの中間生成物とログ。gitignore 対象 |
| `build/sfms/dist/` | 最終成果物の 4 OTF |

FontForge を使うスクリプトは `fontforge -script` で実行する。
fontTools を使うスクリプトは PEP 723 のインライン依存宣言を持ち、`uv run` で単体実行できる。
venv の準備は要らない。
使い方は各スクリプトの docstring に書いてある。

## パイプライン

`build.sh` は Regular、Bold、Italic、BoldItalic の順にビルドする。
1 スタイルおよそ 2 分かかる。
各フェーズのログは `build/sfms/<style>.p<n>.log` に残る。

| フェーズ | スクリプト | 内容 |
| --- | --- | --- |
| P1 | `build_base.py` | SF Mono と Migu 1M を正方グリッドへ合成 |
| P2 | nerd-fonts `font-patcher` | アイコンを本来の幅のまま追加 |
| P2.5 | `plan_icon_scale.py` `apply_icon_scale.py` | SF Mono Square より大きいアイコンを縮小 |
| P2.6 | `instance_vf.py` `add_ligatures.py` | JetBrains Mono のリガチャを移植 |
| P3 | `swap_lineseed.py` | 仮名と漢字を LINE Seed JP に差し替え |
| P4 | `graft_italic.py` `center_italic.py` | true italic の小文字を移植。イタリックのみ |
| P5 | `finalize.py` | name テーブル、OS/2、メトリクス |

### P1 ベース合成

SF Mono を一様に 0.809 倍、つまり 1024/1266 に詰めて正方グリッドへ載せる。
EM 2048 で Latin の送り幅は 1024 になり、全角 CJK の 2048 がちょうど 2 桁になる。
仮名、漢字、CJK 約物は Migu 1M から取る。
em を 1000 から 2048 へ揃えたうえで `JP_SCALE` 倍し、全角セルの中央に置く。
半角カタカナは半角セルに入れる。
SF Mono に無い記号も Migu から補う。
※、矢印、★ などがこれにあたる。
補った記号の送り幅は Unicode の East Asian Width に従わせる。
端末はセル数をフォントではなく EAW から決めるからである。
曖昧幅の記号をどちらに寄せるかは `KM_AMBIGUOUS_WIDTH` で選ぶ。
全角空白 U+3000 には、☐ U+2610 と ✚ U+271A の共通部分を薄い目印として与える。
Ricty に始まり SF Mono Square も使う手法である。
イタリック 2 スタイルでは和文を SF Mono のイタリック角度に合わせて傾ける。

### P2 Nerd アイコン

v3.4.0 に固定した patcher を `--complete --variable-width-glyphs --careful` で実行する。
この「Propo」モードはアイコン本来の幅とセットごとのサイズを保つ。
SF Mono Square と同じ方式である。
`--single-width-glyphs` だと全アイコンが半角セルに詰め込まれ、Powerline 以外は高さが約半分に縮んでしまう。
これが issue #9 の症状だった。
どちらのモードでも、既存の Latin と CJK の送り幅は変わらない。

### P2.5 アイコン縮小

nerd-fonts v3.4.0 には、SF Mono Square が内蔵する旧版セットより大きく描かれるアイコンがある。
そこで `KM_SFMS_DIR` にあるローカルの SFMS 参照フォントより背の高いアイコンを、同じ高さへ縮める。
対象は両フォントが同じ絵を描いているグリフに限る。
ラスタライズしてインク部分を切り出し、正規化したマスクの IoU が 0.6 以上なら同じ絵と判定する。
アイコンセットの絵柄はバージョン間で入れ替わるため、別の絵を他方のサイズに合わせても意味がないからである。
セルを埋める必要がある Powerline、罫線、点字は除外する。
縮小計画は Regular から一度だけ `build/sfms/iconscale.json` に作り、全スタイルへ適用する。
各グリフはインク中心を基準に縮み、送り幅は変えない。
SFMS 参照が無ければこのフェーズはスキップされ、SFMS 由来のデータがリポジトリに入ることはない。

### P2.6 リガチャ

プログラミングリガチャは JetBrains Mono から移植する。
wght 400 と 700 でインスタンス化して使う。
JetBrains の `calt` は端末セーフな方式で、連続の先頭セルを空白スペーサに置き換え、最後のセルに幅広の `.liga` グリフを置く。
リガチャは N 桁ぶんの幅を保つ。
グリフは非等方スケールでコピーする。
横はセル比の 1024/600 で拡大する。
縦は `LIG_YSCALE` で決める。
スクリプト単体の既定は x ハイト合わせで、ビルドでは `1.478` に固定している。
`//` のような背の高い演算子が SF Mono の `/` と揃う値で、issue #7 を解消した。
イタリックではリガチャもフォントの角度に傾ける。

### P3 和文の差し替え

ベースと LINE Seed JP の両方にある仮名、カタカナ、漢字、CJK 約物を LINE Seed に差し替える。
SF Mono の Latin、アイコン、LINE Seed に無い稀な漢字はそのまま残る。
各グリフは 国永日 で計測したベースの CJK サイズに合わせて拡縮し、全角セルの中央に置く。
送り幅は変えない。
例外が 2 つある。
`、。` と全角括弧は中央寄せせず、LINE Seed 本来の水平位置を保つ。
issue #4 で決めた挙動である。
左サイドベアリングをセル幅へ比例配分するので、開き括弧は右へ、閉じ括弧は左へ寄る。

### P4 イタリックの移植

イタリック 2 スタイルだけに走る。
小文字 14 字、a b c d e f i j k l p v y z を Google Sans Code の true italic から移植する。
SF Mono のステム太さに合うよう、`GSC_R` と `GSC_B` で対象ウェイトより細くインスタンス化する。
x ハイトを合わせ、残留する SF Mono 文字のインク中心オフセットの中央値に置く。
続いて `center_italic.py` が ASCII 全体を一様にずらし、インク中心オフセットの中央値を `ITALIC_INK_OFFSET` × セル幅に合わせる。
0 なら upright と同じ中央になり、SF Mono 本来の右寄りは +7.6% にあたる。

### P5 仕上げ

name テーブルを RIBBI 構成に整え、4 スタイルを単一ファミリー「Kusunoki Mono」にまとめる。
垂直メトリクスは 2048 UPM で 1638/-410 とし、SF Mono Square と同値にする。
PANOSE は等幅サンズ、コードページは Latin と日本語を宣言する。
Apple SF Mono を含み再配布できない旨のコピーライトとライセンス文も書き込む。
バージョン文字列は `KM_VERSION` で指定する。

## ソースの取得と固定

`setup.sh` は冪等で、再実行すると取得済みのものはスキップする。
Apple の DMG を hdiutil と pkgutil で展開するため macOS 専用。

| ソース | 固定先 |
| --- | --- |
| SF Mono | Apple 公式の `SF-Mono.dmg` |
| Migu 1M | v2020.0307 のリリース zip |
| nerd-fonts FontPatcher | v3.4.0 |
| LINE Seed JP、Google Sans Code、JetBrains Mono | google/fonts の `main`、OFL |

## メトリクス早見

| 項目 | 値 |
| --- | --- |
| EM | 2048 |
| Latin 送り幅 | 1024 = SF Mono の 1266 × 0.809 |
| CJK 送り幅 | 2048 |
| ascent / descent | 1638 / -410。Nerd パッチの前に設定 |
| 和文の光学スケール | 0.82。delphinus の `MIGU1M_SCALE` と同値 |

## ビルドの確認

インストール済みの SF Mono Square も 2048 UPM なので、fontTools でバウンディングボックスの高さや送り幅を直接比較できる。
確認する点:

- 後続フェーズを経ても GSUB に `calt` が残っているか
- `、。` が左に寄っているか。xMin はおよそ 155 で、LINE Seed 本来のベアリング
- U+3000 にインクがあるか
- ※ や ★ の送り幅が設定どおりか。`narrow` なら 1024、`wide` なら 2048
- SFMS の同じアイコンより背が高いものがないか

## 手法の参照元

- [delphinus/homebrew-sfmono-square][sfms]：このビルドが再現している手法。正方メトリクス、Propo アイコン、可視の全角空白、括弧のベアリング。スクリプトは独自の再実装で、コードは取り込んでいない
- [作者の Qiita 記事][qiita]：SF Mono Square 自体の背景

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[qiita]: https://qiita.com/delphinus/items/f472eb04ff91daf44274
