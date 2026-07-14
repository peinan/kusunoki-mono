require "etc"

# Builds Kusunoki Mono locally, delphinus/homebrew-sfmono-square style:
# every source (Apple SF Mono included) is fetched at install time and the
# font is built on this machine, so no font binary is ever distributed.
class KusunokiMono < Formula
  desc "Japanese coding font: SF Mono on a square grid + LINE Seed JP, built locally"
  homepage "https://github.com/peinan/kusunoki"
  license :cannot_represent # scripts by the author; output embeds Apple SF Mono, personal use only
  head "https://github.com/peinan/kusunoki.git", branch: "main"

  depends_on :macos
  depends_on "fontforge"
  depends_on "python@3.13"
  depends_on "uv"

  resource "sf-mono" do
    url "https://devimages-cdn.apple.com/design/resources/download/SF-Mono.dmg"
    sha256 "6d4a0b78e3aacd06f913f642cead1c7db4af34ed48856d7171a2e0b55d9a7945"
  end

  resource "migu-1m" do
    url "https://github.com/itouhiro/mixfont-mplus-ipa/releases/download/v2020.0307/migu-1m-20200307.zip"
    sha256 "e4806d297e59a7f9c235b0079b2819f44b8620d4365a8955cb612c9ff5809321"
  end

  resource "font-patcher" do
    url "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/FontPatcher.zip"
    sha256 "a8f11e511ed7c69e96680858c06b50a643ea7752e26d5cd13dd5e5cc53ab1760"
  end

  # The google/fonts files are pinned to a commit so the sha256 stays stable.
  resource "lineseed-jp-regular" do
    url "https://raw.githubusercontent.com/google/fonts/ec0464b978de222073645d6d3366f3fdf03376d8/ofl/lineseedjp/LINESeedJP-Regular.ttf"
    sha256 "04a6c0077ddb8ba5af3638bd76b4600708dde7b38df047b40fbe6f3af358d3c3"
  end

  resource "lineseed-jp-bold" do
    url "https://raw.githubusercontent.com/google/fonts/ec0464b978de222073645d6d3366f3fdf03376d8/ofl/lineseedjp/LINESeedJP-Bold.ttf"
    sha256 "67aec2dc10b3ad210d6f7d53b33bbfea42ea28e32fa3834624eee699a638d5ff"
  end

  resource "google-sans-code" do
    url "https://raw.githubusercontent.com/google/fonts/ec0464b978de222073645d6d3366f3fdf03376d8/ofl/googlesanscode/GoogleSansCode-Italic%5Bwght%5D.ttf"
    sha256 "bdf116292f27aca16e2aefb5534042a25f244d3a9187a521ce97fc2117a4a844"
  end

  resource "jetbrains-mono" do
    url "https://raw.githubusercontent.com/google/fonts/ec0464b978de222073645d6d3366f3fdf03376d8/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
    sha256 "48715a42ec242c21e9f02692891e147d022299a52e48d5e413e1a942193ffeda"
  end

  def install
    # uv would otherwise write into the sandboxed fake HOME
    ENV["UV_CACHE_DIR"] = (buildpath/".uv-cache").to_s
    ENV["UV_PYTHON_INSTALL_DIR"] = (buildpath/".uv-python").to_s
    # The sandbox fakes HOME, so point the optional SF Mono Square reference
    # (icon sizing, P2.5) at the real user fonts dir; skipped when absent.
    ENV["KM_SFMS_DIR"] = "#{Etc.getpwuid.dir}/Library/Fonts"

    # Stage every source where scripts/setup.sh would have put it, then the
    # normal build pipeline runs unchanged (and needs no network for fonts).
    resource("sf-mono").stage do
      system "xar", "-xf", "SF Mono Fonts.pkg"
      system "/bin/bash", "-c", "cat SFMonoFonts.pkg/Payload | gunzip -dc | cpio -i"
      (buildpath/"sources/sf-mono").install Dir["Library/Fonts/SF-Mono-*.otf"]
    end

    resource("migu-1m").stage do
      (buildpath/"sources/migu-1m").install Dir["**/migu-1m-{regular,bold}.ttf"]
    end

    resource("font-patcher").stage do
      (buildpath/"sources/nerd-patcher").install Dir["*"]
    end

    resource("lineseed-jp-regular").stage do
      (buildpath/"sources/lineseed-jp").install Dir["*.ttf"].first => "LINESeedJP-Regular.ttf"
    end

    resource("lineseed-jp-bold").stage do
      (buildpath/"sources/lineseed-jp").install Dir["*.ttf"].first => "LINESeedJP-Bold.ttf"
    end

    resource("google-sans-code").stage do
      (buildpath/"sources/google-sans-code").install Dir["*.ttf"].first => "GoogleSansCode-Italic[wght].ttf"
    end

    resource("jetbrains-mono").stage do
      (buildpath/"sources/jetbrains-mono").install Dir["*.ttf"].first => "JetBrainsMono[wght].ttf"
    end

    system "bash", "scripts/build.sh"
    (share/"fonts").install Dir["build/sfms/dist/KusunokiMono-*.otf"]
  end

  def caveats
    <<~EOS
      The built fonts are in:
        #{opt_share}/fonts
      Homebrew does not register fonts with macOS; copy them yourself:
        cp "#{opt_share}/fonts/KusunokiMono-"*.otf ~/Library/Fonts/
    EOS
  end

  test do
    assert_path_exists share/"fonts/KusunokiMono-Regular.otf"
  end
end
