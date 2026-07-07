<div align="center">

[English](README.md) | 日本語

</div>

# Kusunoki Mono

日本語まじりのコードを書くための等幅フォントです。
Latin / ASCII / 記号 / リガチャに [Iosevka][iosevka]、日本語のかなと漢字に [BIZ UDGothic][biz]、ターミナルのアイコンに [Nerd Fonts][nerd] を合成しています。
全角の CJK グリフは Latin 2 桁ぶんの幅にそろえてあるので、表示が崩れません。

## どれをダウンロードするか

4 つのバリアントがあり、それぞれに Regular / Bold / Italic / Bold Italic を用意しています。
family 名が異なるので、複数を同時にインストールしてアプリごとに使い分けられます。

| フォント family        | リガチャ | Nerd Font アイコン | 向いている用途                             |
| ---------------------- | :------: | :----------------: | ------------------------------------------ |
| **Kusunoki Mono**      |    –     |         –          | 素の構成。互換性を最優先したいとき         |
| **Kusunoki Mono NF**   |    –     |         ✓          | アイコンを表示するターミナル（リガチャなし） |
| **Kusunoki Mono LG**   |    ✓     |         –          | リガチャを使うエディタ                     |
| **Kusunoki Mono NFLG** |    ✓     |         ✓          | 全部入り（リガチャとアイコン）             |

迷ったら、アイコンとリガチャを両方使うなら **NFLG**、どちらも要らないなら素の **Kusunoki Mono** を選んでください。

## インストール

1. [Releases ページ][releases]から使いたいバリアントの zip をダウンロードします。
2. `.ttf` をインストールします。
   - **macOS**：`.ttf` を開いて「インストール」、または `~/Library/Fonts/` にコピー。
   - **Windows**：`.ttf` を選択して右クリックから「インストール」。
   - **Linux**：`~/.local/share/fonts/` にコピーして `fc-cache -f` を実行。
3. エディタやターミナルのフォントに family 名（例：`Kusunoki Mono NFLG`）を指定します。

リガチャ（`LG` と `NFLG`）は、アプリ側でも有効化が必要なことが多いです（例：VS Code の `"editor.fontLigatures": true`）。
素の構成と `NF` はリガチャを一切含みません。ターミナルではこちらを好む人もいます。

## 自分で調整する

変更したいときだけ必要です。
配布フォントはそのまま使えます。

必要なもの：macOS と [Homebrew][brew]、[`uv`][uv]、Node.js 18 以上、そしてこのリポジトリの隣（`../Iosevka`）に置いた [Iosevka][iosevka] のチェックアウト（`IOSEVKA_DIR` で変更可）。

```sh
make setup   # 初回のみ。ツール導入、BIZ UDGothic と Nerd Fonts のダウンロード
make build   # バリアントを 1 つビルド → dist/<Family>/
make verify  # dist/<Family>/specimen.html を開いて目視確認
```

好みの多くは 2 つのノブで足ります。

- **字幅（密度）**：`config.sh` の `WIDTH_EM`。`0.6`（ゆったり、既定）か `0.5`（詰まった見た目で、全角 CJK がちょうど 1em）。変更後に `make && make verify`。
- **リガチャ**：発火するリガチャの種類は `private-build-plans.toml` の `[buildPlans.KusunokiMono.ligations]`（`inherits` / `enables` / `disables`）で決まります。変更後に `make && make verify`。

ビルドパイプライン全体、バリアントの仕組み、リリースと CI の詳細は [docs/BUILD.ja.md](docs/BUILD.ja.md) にあります。

## 構成元

- [Iosevka][iosevka]：Latin、ASCII、記号、罫線、リガチャ（OFL 1.1）
- [BIZ UDGothic][biz]：日本語のかなと漢字（OFL 1.1）
- [Nerd Fonts][nerd]：アイコングリフ（MIT および各上流のグリフライセンス）

## ライセンス

[SIL Open Font License 1.1](OFL.txt)。
「Kusunoki Mono」は新しい名前で、構成元フォントいずれの予約フォント名にも該当しません。

[iosevka]: https://github.com/be5invis/Iosevka
[biz]: https://github.com/googlefonts/morisawa-biz-ud-gothic
[nerd]: https://www.nerdfonts.com/
[releases]: https://github.com/peinan/kusunoki/releases
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
