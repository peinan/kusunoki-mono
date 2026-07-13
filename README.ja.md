<div align="center">

[English](README.md) | 日本語

</div>

# Kusunoki Mono (SF Mono Square edition)

日本語コーディング向けの個人用等幅フォント。
[SF Mono Square][sfms] 系のベースに独自変換を重ねて作ります。

- **Latin / ASCII / 記号 / 数字**：Apple **SF Mono** を正方グリッドに詰めたもの(全角 CJK = ちょうど 2 Latin 列。和文とコードがグリッドに揃う)。
- **和文**：**LINE Seed JP**。カバー外の仮名や漢字は **Migu 1M** でフォールバック。
- **リガチャ**：**JetBrains Mono** のプログラミングリガチャ(`->` `=>` `!=` など)を正方セルに合わせて移植。
- **イタリック**：小文字 14 字を **Google Sans Code** の true italic から移植。残りは SF Mono の italic をセル中央寄せ。
- **アイコン**：**Nerd Fonts**(公式 v3.4.0 patcher。可変幅で SF Mono Square 同様のサイズ)。

## 配布しません(自分でビルド)

出力には **Apple SF Mono が含まれ**、Apple はローカル利用を許諾していますが**再配布は認めていません**。
そのためフォントバイナリは同梱しません。
SF Mono Square と同じく、この repo は**ビルドレシピ**です(SF Mono を Apple から、OFL/MIT のソースフォントを取得し、手元の Mac でビルド)。

## ビルド(macOS)

必要: macOS、[Homebrew][brew](`brew install fontforge`)、[`uv`][uv]。

```sh
make setup   # SF Mono(Apple)/ Migu 1M / LINE Seed JP / Google Sans Code / JetBrains Mono / nerd-fonts patcher を取得
make build   # → build/sfms/dist/KusunokiMono-{Regular,Bold,Italic,BoldItalic}.otf
```

4 つの `.otf` を `~/Library/Fonts/` に入れ、端末やエディタのフォントを
**Kusunoki Mono** に設定します。

## 調整ノブ

`make build` の環境変数:

- **`JP_SCALE`**：和文の光学サイズ(既定 `0.82`)。
- **`LIG_YSCALE`**：リガチャの高さ(既定 `1.478`。`//` のような背の高い演算子が SF Mono の `/` に揃う値。大きすぎると感じたら下げる)。
- **`ITALIC_INK_OFFSET`**：italic の英字インク位置(セル比)。`0.0`=upright と同じ中央(既定)、`0.076`=SF Mono 本来の右寄り。
- **`GSC_R`** / **`GSC_B`**：移植する italic 文字の Google Sans Code ウェイト。
- **`KM_AMBIGUOUS_WIDTH`**：`※ ★ ℃` など East Asian Width が曖昧な記号のセル幅。`narrow`(既定)は 1 セルで、Ghostty など厳密な端末で被らない。`wide` は 2 セル(SF Mono Square 相当。端末側で ambiguous=wide 設定が必要)。
- **`KM_SFMS_DIR`**：`SFMonoSquare-*.otf` のあるディレクトリ。アイコンを SF Mono Square のサイズに合わせるのに使います(既定 `~/Library/Fonts`、無ければスキップ)。

## 開発

パイプラインの内部(フェーズ、スクリプト、メトリクス、手法の参照元)は
[docs/development.ja.md](docs/development.ja.md) にまとめています。

## ライセンス

ビルド済みフォントは Apple SF Mono を含む、**個人用で再配布不可**の成果物です。
ソースフォントは各々のライセンスに従います: SF Mono(© Apple)、Migu 1M(M+ / IPA)、LINE Seed JP(OFL 1.1)、Google Sans Code(OFL 1.1)、JetBrains Mono(OFL 1.1)、Nerd Fonts(MIT + upstream)。
ビルドスクリプトは作者のものです。

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
