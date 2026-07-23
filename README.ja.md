<div align="center">

![Kusunoki Mono](docs/images/hero.png)

[English](README.md) | 日本語

![platform](https://img.badges.sh/platform-macOS-b4befe?labelColor=1e1e2e&logo=apple&font=Space+Grotesk&fontWeight=500&labelFontWeight=700&messageFontWeight=700)
![version](https://img.badges.sh/version-v0.7.0-a6e3a1?labelColor=1e1e2e&logo=lucide:Tag&font=Space+Grotesk&fontWeight=500&labelFontWeight=700&messageFontWeight=700)
[![homebrew](https://img.badges.sh/homebrew-peinan%2Fkusunoki--mono-fab387?labelColor=1e1e2e&logo=lucide:Beer&font=Space+Grotesk&fontWeight=500&labelFontWeight=700&messageFontWeight=700)](https://github.com/peinan/homebrew-kusunoki-mono)
[![web](https://img.badges.sh/web-peinan.github.io-89b4fa?labelColor=1e1e2e&logo=lucide:Globe&font=Space+Grotesk&fontWeight=500&labelFontWeight=700&messageFontWeight=700)](https://peinan.github.io/kusunoki-mono/)

Apple の美しい等幅フォント SF Mono を日本語と揃う正方グリッドに整え、
小さくても視認性の高い LINE Seed JP を重ねた日本語プログラミングフォント。
イタリックは SF Mono に馴染むかを一字ずつ確かめて選んだ Google Sans Code の true italic、
さらに JetBrains Mono のリガチャと Nerd Fonts のアイコンも標準装備。

</div>

## 特徴

- 半角 1 : 全角 2 の固定グリッド。日本語とコードが揃う
- 英数字は Apple **SF Mono**、和文は **LINE Seed JP** (フォールバックは Migu 1M)
- 濁点・半濁点は MigMix 流に大きく、字と重なる部分は skip ink で削る。小さいサイズでも ば ぱ ぼ ぽ が見分けられる
- **JetBrains Mono** のプログラミングリガチャ
- **Google Sans Code** の true italic
- **Nerd Fonts** アイコン

![字形見本](docs/images/specimen.png)

## インストール

出力には Apple SF Mono が含まれるため配布せず、手元でビルドします。

```sh
brew tap peinan/kusunoki-mono
brew install --cask font-kusunoki-mono
```

初回はその場でフォントをビルドするため 7 分前後かかります。
素の `brew install` は完了まで何も表示しないので、経過を見たい場合は `--verbose` を付けてください。

フォントは `~/Library/Fonts` に配置され、`brew upgrade` にも追従します。

Homebrew 6.0 以降では、サードパーティ tap を初回に信頼する必要があります: `brew trust peinan/kusunoki-mono`

端末やエディタのフォントを **Kusunoki Mono** に設定すれば完了です。

### make でビルドする

フォントを調整したいときは make でビルドします。下の表のノブを `make build` の環境変数として渡せます。
必要なもの: [Homebrew][brew]、[`uv`][uv]

```sh
brew install fontforge
make setup   # ソースフォントと nerd-fonts patcher を取得
make build   # → dist/KusunokiMono-{Regular,Bold,Italic,BoldItalic}.otf
cp dist/KusunokiMono-*.otf ~/Library/Fonts/
```

| 変数 | 既定値 | 効果 |
| --- | --- | --- |
| `JP_SCALE` | `0.82` | 和文の光学サイズ |
| `LIG_YSCALE` | `1.478` | リガチャの高さ。既定値は `//` など背の高い演算子が SF Mono の `/` に揃う値 |
| `ITALIC_INK_OFFSET` | `0.0` | italic 英字のインク位置。セル幅比で `0` は upright と同じ中央、`0.076` は SF Mono 本来の右寄り |
| `GSC_R` / `GSC_B` | `360` / `650` | 移植する italic 文字の Google Sans Code ウェイト |
| `KM_DAKUTEN_SCALE` / `KM_HANDAKUTEN_SCALE` | `1.3` / `1.25` | 濁点・半濁点の拡大率 |
| `KM_DAKUTEN_HALO` / `KM_HANDAKUTEN_HALO` | `0.48` / `0.36` | 拡大したマークの周囲を削る skip ink の幅 (マーク比)。`KM_DAKUTEN_SKIP_INK=0` で削りを無効化 |
| `KM_AMBIGUOUS_WIDTH` | `narrow` | ※ ★ ℃ など曖昧幅記号のセル数。`narrow` は 1 セルで Ghostty など厳密な端末でも被らず、`wide` は 2 セル |
| `KM_SFMS_DIR` | `~/Library/Fonts` | アイコンのサイズ合わせに使う `SFMonoSquare-*.otf` の場所。無ければこの工程はスキップ |

## 開発

パイプラインの内部は [docs/development.ja.md](docs/development.ja.md) にまとめています。

## スクリーンショット

| | |
| --- | --- |
| ![エディタ](docs/images/editor.png) | ![git log](docs/images/gitlog.png) |

![ターミナル](docs/images/terminal.png)

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

[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
