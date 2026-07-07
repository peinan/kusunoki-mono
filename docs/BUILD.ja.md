<div align="center">

[English](BUILD.md) | 日本語

</div>

# Kusunoki Mono のビルドとリリース

メンテナー向けのメモです。
インストールと使い方は [README](../README.ja.md) を参照してください。

## 全体の流れ

1. **Iosevka** を `private-build-plans.toml` から一度だけビルドします（peinan の設計：`ss14` と `cv` の上書き、リガチャ有効、`exportGlyphNames`、そして TrueType の 65535 グリフ上限に収めるための `noCvSs`）。これが Latin / ASCII / 記号 / 罫線 / リガチャの土台になります。
2. **LINE Seed JP** と **Nerd Fonts** を FontForge（`scripts/merge.py`）で変換します。1000 UPM に再スケールし、全角 CJK が Latin セルちょうど 2 つ分になるよう字幅を正規化し、斜体はグリフごとの中心を軸に擬似斜体化します。
3. **fontTools**（`scripts/fix.py`）で、Iosevka が既に持つコードポイントを除き、Iosevka を先頭にしてマージし（Iosevka のリガチャ GSUB をそのまま保持）、`name` / `OS/2`（CP932、USE_TYPO_METRICS）/ `post`（isFixedPitch）/ 縦メトリクスの各テーブルを整えます。
4. `scripts/specimen.py` がメトリクスを検査し、specimen HTML を書き出します。

Iosevka のビルドは常に一度だけです。
4 バリアントの違いはマージ段階だけにあります。

## 必要なもの

- macOS（Homebrew）または Linux（apt）：`fontforge`、`ttfautohint`
- `fonttools` 用の [`uv`](https://docs.astral.sh/uv/)
- Node.js 18 以上と、`../Iosevka`（または `IOSEVKA_DIR`）に置いた Iosevka のチェックアウト

`make setup` が、システムツールの導入（brew か apt）、構成元フォントのダウンロード、Iosevka チェックアウトでの `npm install` をまとめて行います。

## コマンド

| コマンド        | 内容                                                              |
| --------------- | ----------------------------------------------------------------- |
| `make setup`    | 依存の導入、LINE Seed JP と Nerd Fonts のダウンロード、npm install |
| `make iosevka`  | Iosevka の土台をビルド（全バリアント共通）                        |
| `make build`    | バリアントを 1 つ（iosevka + merge）。ローカル反復用              |
| `make variants` | 4 バリアントすべて（先に `make iosevka`）                         |
| `make package`  | 各バリアントを zip 化 → `dist/release-assets/`                    |
| `make dist-all` | `iosevka` + `variants` + `package`                               |
| `make verify`   | メトリクス検査と、現在のバリアントの specimen                     |

## バリアント

軸は 2 つで、環境変数で指定します（`config.sh` がそこから family 名、basename、出力ディレクトリを導出します）。

- `NERD_FONTS` = `1`/`0`：Nerd Fonts のアイコンを合成する。
- `LIGATURES` = `1`/`0`：Iosevka の既定リガチャ `calt` を残す。`0` のときはマージ時（`fix.py`）に `calt` を GSUB の LangSys から外します。Iosevka は再ビルドしません。

命名は加算式です。
素の構成はどちらの機能も持たず、`NF` がアイコンを、`LG` がリガチャを足します。

| `NERD_FONTS` | `LIGATURES` | family               |
| :----------: | :---------: | -------------------- |
|      0       |      0      | `Kusunoki Mono`      |
|      1       |      0      | `Kusunoki Mono NF`   |
|      0       |      1      | `Kusunoki Mono LG`   |
|      1       |      1      | `Kusunoki Mono NFLG` |

## 設定

- `config.sh`：マージ側のノブ。`VERSION`、`WIDTH_EM`（`0.6`/`0.5`）、`TARGET_EM`、`ITALIC_ANGLE`、`STYLES`、`NERD_FONTS`、`LIGATURES`、縦位置の微調整（`CJK_Y_SCALE` / `CJK_Y_SHIFT`）。
- `private-build-plans.toml`：Iosevka の設計（variants、`ligations`、`exportGlyphNames`、weights、widths、slopes）。

## リリース（CI）

`.github/workflows/release.yml` は 4 バリアントをビルドして GitHub Release に公開します。
トリガーは **`v*` タグの push**（タグ名がリリース名になる）、または手動の **workflow_dispatch**（`config.sh` の `v<VERSION>` で公開）です。
`main` への通常の push ではリリースしないので、作業途中でも自由に push できます。

**リリースを切るには**：`config.sh` の `VERSION` を上げてコミットし、対応するタグを push します。

```sh
git tag v0.4.0
git push origin v0.4.0
```
