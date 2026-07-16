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
| `dist/` | 最終成果物の 4 OTF |

FontForge を使うスクリプトは `fontforge -script`、fontTools を使うスクリプトは PEP 723 宣言により `uv run` で単体実行できる。
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
| P2.8 | `enlarge_dakuten.py` | 濁点・半濁点を拡大し skip ink で削る |
| P3 | `swap_lineseed.py` | 仮名と漢字を LINE Seed JP に差し替え |
| P4 | `graft_italic.py` `center_italic.py` | true italic の小文字を移植。イタリックのみ |
| P5 | `finalize.py` | name テーブル、OS/2、メトリクス |

### P1 ベース合成

SF Mono と Migu 1M を正方グリッドで合成する。

- SF Mono は一様に 0.809 倍 = 1024/1266。EM 2048 で Latin の送り幅が 1024 になり、全角 CJK の 2048 がちょうど 2 桁
- 仮名、漢字、CJK 約物は Migu 1M から。em 1000→2048 のうえ `JP_SCALE` 倍して全角セル中央へ、半角カタカナは半角セルへ
- ※ や矢印や ★ など SF Mono に無い記号も Migu から補う
- 補った記号の送り幅は Unicode の East Asian Width に従う。端末はセル数を EAW から決めるため。曖昧幅は `KM_AMBIGUOUS_WIDTH` で選ぶ
- 全角空白 U+3000 は ☐ U+2610 と ✚ U+271A の共通部分で可視化。Ricty 由来で SF Mono Square も使う手法
- イタリックでは和文を SF Mono のイタリック角度に傾ける

### P2 Nerd アイコン

v3.4.0 に固定した patcher を `--complete --variable-width-glyphs --careful` で実行する。

- 「Propo」モードはアイコン本来の幅とセットごとのサイズを保つ。SF Mono Square と同じ
- `--single-width-glyphs` は全アイコンを半角セルに詰め、Powerline 以外が約半分に縮む。issue #9 の症状
- どちらでも既存の Latin と CJK の送り幅は不変

### P2.5 アイコン縮小

nerd-fonts v3.4.0 には SF Mono Square 内蔵の旧版セットより大きいアイコンがあるため、`KM_SFMS_DIR` の SFMS 参照フォントより背の高いものを同じ高さへ縮める。

- 対象は両フォントが同じ絵のグリフのみ。ラスタライズしてインクを切り出し、正規化したマスクの IoU 0.6 以上で判定
- 絵柄はバージョン間で入れ替わるので、別の絵をサイズ合わせしても意味がないため
- セルを埋める必要がある Powerline、罫線、点字は除外
- 縮小計画は Regular から一度だけ `build/sfms/iconscale.json` に作り、全スタイルへ適用。インク中心を基準に縮め、送り幅は不変
- SFMS 参照が無ければスキップ。SFMS 由来のデータはリポジトリに入らない

### P2.6 リガチャ

リガチャは JetBrains Mono から移植する。
wght 400 と 700 でインスタンス化して使う。

- JetBrains の `calt` は端末セーフ。連続の先頭セルを空白スペーサに、最後のセルに幅広の `.liga` グリフを置き、N 桁ぶんの幅を保つ
- コピーは非等方スケール。横はセル比 1024/600、縦は `LIG_YSCALE`
- スクリプト既定は x ハイト合わせ、ビルドは `1.478` に固定。`//` など背の高い演算子が SF Mono の `/` に揃う値で、issue #7 を解消
- イタリックではリガチャもフォントの角度に傾ける

### P2.8 濁点・半濁点の拡大

MigMix 1P のように濁点・半濁点を大きくして、小さいサイズでも ば/ぱ を
見分けやすくする。issue #6 の対応。P3 が拾う前に LINE Seed の
ウェイトごとに 1 回走り、ログは `build/sfms/dakuten.<weight>.log`。

- 濁音かなを NFD で分解して再構築する。マークは「グリフ − 清音の親字」、本体は親字そのもの。本体に溶接・融合したマークでも輪郭の推測が要らない。溶接で欠けた半濁点の輪は、穴の輪郭を中心に同心円で復元する
- 本体が貼り付けではなく描き直されている字（ヅ デ など）は、右上の小さい輪郭群をマークとして扱う
- 拡大したマークを合成し直す前に、少し大きいコピーで本体を削る。重なる部分に白いギャップが残る skip ink の見た目になる
- `KM_DAKUTEN_SCALE` / `KM_HANDAKUTEN_SCALE` がマークの倍率 (1.3 / 1.25)、`KM_DAKUTEN_HALO` / `KM_HANDAKUTEN_HALO` が削りギャップ (0.48 / 0.36)、`KM_DAKUTEN_SKIP_INK=0` で削りを無効化、`KM_DAKUTEN_EXCLUDE` が対象外の字 (既定 ゞヾヷヸヹヺ)

グローバル値の上に字ごとの調整を重ねられる。リポジトリルートで
`uv run scripts/dakuten_tuner.py` を実行すると `http://localhost:8765` に
ビジュアルエディタが立つ。濁音かなの一覧から字を選び、マークの倍率と
削りギャップはスライダー、位置はドラッグ、除外はチェックボックスで調整する。
保存すると `scripts/dakuten_overrides.json`
(字 → `scale` / `halo` / `dx` / `dy` / `skip_ink` / `exclude`、font units) に
書き出され、次のビルドから反映される。プレビューは本体の上にハロを紙色で
塗る方式で、ブーリアン削りと見た目が完全に一致する。

### P3 和文の差し替え

ベースと LINE Seed JP の両方にある仮名、カタカナ、漢字、CJK 約物を差し替える。
SF Mono の Latin、アイコン、LINE Seed に無い稀な漢字はそのまま残る。

- 各グリフは 国永日 で測ったベースの CJK サイズへ拡縮し、全角セル中央へ。送り幅は不変
- 例外は `、。` と全角括弧。中央寄せせず LINE Seed 本来の水平位置を保つ。issue #4 の挙動
- 左サイドベアリングをセル幅へ比例配分するため、開き括弧は右へ、閉じ括弧は左へ寄る

### P4 イタリックの移植

イタリック 2 スタイルだけに走る。

- 小文字 14 字 a b c d e f i j k l p v y z を Google Sans Code の true italic から移植
- `GSC_R` と `GSC_B` で対象より細くインスタンス化して SF Mono のステムに合わせ、x ハイトを揃え、残留する SF Mono 文字のインク中心の中央値に配置
- `center_italic.py` が ASCII を一様にずらし、インク中心の中央値を `ITALIC_INK_OFFSET` × セル幅へ。0 は upright と同じ中央、SF Mono 本来の右寄りは +7.6%

### P5 仕上げ

- 4 スタイルを単一ファミリー「Kusunoki Mono」へ。name テーブルは RIBBI 構成
- 垂直メトリクスは 2048 UPM で 1638/-410。SF Mono Square と同値
- PANOSE は等幅サンズ。コードページは Latin と日本語
- SF Mono を含み再配布できない旨をコピーライトとライセンス文に記載
- バージョン文字列は `KM_VERSION` で指定

## ソースの取得と固定

`setup.sh` は冪等で、再実行すると取得済みのものはスキップする。
Apple の DMG を hdiutil と pkgutil で展開するため macOS 専用。

| ソース | 固定先 |
| --- | --- |
| SF Mono | Apple 公式の `SF-Mono.dmg` |
| Migu 1M | v2020.0307 のリリース zip |
| nerd-fonts FontPatcher | v3.4.0 |
| LINE Seed JP、Google Sans Code、JetBrains Mono | google/fonts の `main`、OFL |

## Homebrew tap

formula は [peinan/homebrew-kusunoki-mono][tap] にある。
固定した同じソースを `sources/` へ配置して `scripts/build.sh` を無改変で実行するので、`brew install` と `make build` の成果物は同じになる。
リリースの流れ:

- このリポジトリで `vX.Y.Z` タグを打つ
- formula の `url` と `sha256` をそのタグの tarball に向ける
- 最初のタグを打つまで formula は head-only なので、インストールには `--HEAD` が要る

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

[tap]: https://github.com/peinan/homebrew-kusunoki-mono
[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[qiita]: https://qiita.com/delphinus/items/f472eb04ff91daf44274
