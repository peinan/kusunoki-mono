<div align="center">

[English](README.md) | 日本語

</div>

# Kusunoki Mono (SF Mono Square edition)

日本語コーディング向けの個人用等幅フォント。[SF Mono Square][sfms] 系のベースに
独自変換を重ねて作ります:

- **Latin / ASCII / 記号 / 数字** — Apple **SF Mono** を正方グリッドに詰めたもの
  (全角 CJK = ちょうど 2 Latin 列。和文とコードがグリッドに揃う)。
- **和文** — カバーする仮名・漢字は **LINE Seed JP**、残りは **Migu 1M** を
  フォールバック。
- **イタリック** — 小文字 14 字を **Google Sans Code** の true italic から移植、
  残りは SF Mono の italic をセル中央寄せ。
- **アイコン** — **Nerd Fonts**(公式 v3.4.0 patcher、可変幅で SF Mono Square 同様のサイズ)。

## 配布しません — 自分でビルド

出力には **Apple SF Mono が含まれ**、Apple はローカル利用を許諾していますが
**再配布は認めていません**。そのためフォントバイナリは同梱せず、この repo は
**ビルドレシピ**です(SF Mono を Apple から、OFL/MIT のソースフォントを取得し、
手元の Mac でビルド)。

## ビルド(macOS)

必要: macOS、[Homebrew][brew](`brew install fontforge`)、[`uv`][uv]。

```sh
make setup   # SF Mono(Apple)/ Migu 1M / nerd-fonts patcher / LINE Seed JP / Google Sans Code を取得
make build   # → build/sfms/dist/KusunokiMono-{Regular,Bold,Italic,BoldItalic}.otf
```

4 つの `.otf` を `~/Library/Fonts/` に入れ、端末/エディタのフォントを
**Kusunoki Mono** に設定します。

調整ノブ(`make build` の環境変数):

- `JP_SCALE` — 和文の光学サイズ(既定 `0.82`)。
- `ITALIC_INK_OFFSET` — italic の英字インク位置(セル比)。`0.0`=upright と同じ中央
  (既定)、`0.076`=SF Mono 本来の右寄り。
- `GSC_R` / `GSC_B` — 移植する italic 文字の Google Sans Code ウェイト。

## ビルドの流れ

`scripts/sfmono/`(`build.sh` が統括):

1. `build_base.py` — SF Mono ×0.809(正方)+ Migu 1M ×0.82。SF Mono に無い記号
   (※・矢印など)も Migu から補完 → ベース。
2. nerd-fonts `font-patcher --variable-width-glyphs` → アイコン(CJK は全角のまま)。
3. `plan_icon_scale.py` + `apply_icon_scale.py` — SF Mono Square より大きいアイコンを
   同サイズに縮小(同一グリフのみ・ローカルの SFMS 参照が必要、無ければスキップ)。
4. `swap_lineseed.py` — 仮名/漢字を LINE Seed JP に差替(Migu フォールバック)。
5. `graft_italic.py` + `center_italic.py` — Google Sans Code の italic 文字を中央寄せで移植。
6. `finalize.py` — RIBBI name / OS2 / メトリクス。

依存は `fontforge` + `uv`(fonttools)+ `setup.sh` が取得する nerd-fonts patcher のみ。

## ライセンス

ビルド済みフォントは Apple SF Mono を含む **個人用・再配布不可**の成果物です。
ソースフォントは各々のライセンス: SF Mono(© Apple)、Migu 1M(M+ / IPA)、
LINE Seed JP(OFL 1.1)、Google Sans Code(OFL 1.1)、Nerd Fonts(MIT + upstream)。
ビルドスクリプトは作者のものです。

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
