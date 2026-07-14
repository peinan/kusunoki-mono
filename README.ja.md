<div align="center">

[English](README.md) | 日本語

</div>

# Kusunoki Mono

日本語コーディング向けの個人用等幅フォント。
[SF Mono Square][sfms] 系のベースに独自の変換を重ねて作ります。
全角 CJK がちょうど Latin 2 桁ぶんになり、和文とコードがグリッドに揃います。

| 部位 | ソース |
| --- | --- |
| Latin / ASCII / 記号 / 数字 | Apple SF Mono を正方グリッドに凝縮 |
| 和文 | LINE Seed JP。カバー外は Migu 1M でフォールバック |
| プログラミングリガチャ | JetBrains Mono を正方セルに合わせて移植 |
| イタリック小文字 | Google Sans Code の true italic から 14 字。残りは SF Mono italic を中央寄せ |
| アイコン | Nerd Fonts v3.4.0。可変幅で SF Mono Square と同サイズ |

## 配布せず、自分でビルドする

出力には Apple SF Mono が含まれます。
Apple はローカル利用を許諾する一方、再配布は認めていません。
そのため SF Mono Square と同じくフォントバイナリは同梱せず、このリポジトリが配布するのはビルドレシピです。
SF Mono を Apple から、OFL/MIT のソースフォントを各配布元から取得し、手元の Mac でビルドします。

## インストール (macOS)

どちらのルートもソースを取得して手元の Mac でビルドします。

### Homebrew

```sh
brew tap peinan/kusunoki
brew install kusunoki-mono
cp "$(brew --prefix)/share/fonts/KusunokiMono-"*.otf ~/Library/Fonts/
```

### make

必要なもの: macOS、[Homebrew][brew]、[`uv`][uv]

```sh
brew install fontforge
make setup   # ソースフォントと nerd-fonts patcher を取得
make build   # → build/sfms/dist/KusunokiMono-{Regular,Bold,Italic,BoldItalic}.otf
cp build/sfms/dist/KusunokiMono-*.otf ~/Library/Fonts/
```

端末やエディタのフォントを **Kusunoki Mono** に設定すれば完了です。

## 調整ノブ

`make build` の環境変数です。
Homebrew 経由では独自の環境変数が渡らないため、ノブを変えるときは make ルートでビルドします。

| 変数 | 既定値 | 効果 |
| --- | --- | --- |
| `JP_SCALE` | `0.82` | 和文の光学サイズ |
| `LIG_YSCALE` | `1.478` | リガチャの高さ。既定値は `//` など背の高い演算子が SF Mono の `/` に揃う値 |
| `ITALIC_INK_OFFSET` | `0.0` | italic 英字のインク位置。セル幅比で `0` は upright と同じ中央、`0.076` は SF Mono 本来の右寄り |
| `GSC_R` / `GSC_B` | `360` / `650` | 移植する italic 文字の Google Sans Code ウェイト |
| `KM_AMBIGUOUS_WIDTH` | `narrow` | ※ ★ ℃ など曖昧幅記号のセル数。`narrow` は 1 セルで Ghostty など厳密な端末でも被らず、`wide` は SF Mono Square と同じ 2 セル |
| `KM_SFMS_DIR` | `~/Library/Fonts` | アイコンのサイズ合わせに使う `SFMonoSquare-*.otf` の場所。無ければこの工程はスキップ |

## 開発

パイプラインの内部は [docs/development.ja.md](docs/development.ja.md) にまとめています。

## ライセンス

ビルド済みフォントは Apple SF Mono を含む、個人用で再配布不可の成果物です。
ソースフォントは各々のライセンスに従います。
ビルドスクリプトは作者のものです。

| ソース | ライセンス |
| --- | --- |
| SF Mono | © Apple |
| Migu 1M | M+ / IPA |
| LINE Seed JP | OFL 1.1 |
| Google Sans Code | OFL 1.1 |
| JetBrains Mono | OFL 1.1 |
| Nerd Fonts | MIT + upstream |

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
