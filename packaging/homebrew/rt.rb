# TODO before this formula works:
#   1. Tag a release on the atlas-brown/rt repo and paste its source tarball
#      URL + sha256 below.
class RtArtifact < Formula
  desc "Rt: an overlay type system for shell pipelines -- static checker for shell pipelines"
  homepage "https://github.com/atlas-brown/rt"
  url "TODO-source-tarball-url"
  sha256 "TODO-source-tarball-sha256"
  version "0.1.0"

  depends_on "openjdk@21"
  depends_on "python@3.12"

  depends_on "autoconf" => :build
  depends_on "automake" => :build
  depends_on "libtool" => :build
  depends_on "openssl@3" => :build
  depends_on "pkg-config" => :build
  depends_on "rust" => :build
  depends_on "uv" => :build

  def install
    system "patch", "-p1", "-i", "packaging/patches/001-portable-paths.patch"

    ENV["CFLAGS"] = "-std=gnu17 -O2"
    ENV.prepend_path "PKG_CONFIG_PATH", Formula["openssl@3"].opt_lib/"pkgconfig"

    python = Formula["python@3.12"].opt_bin/"python3.12"
    system "uv", "sync", "--locked", "--no-dev", "--python", python

    site_packages = Pathname.glob(".venv/lib/python3.*/site-packages").first
    raise "uv sync did not produce a site-packages directory" if site_packages.nil?

    ["_rt.pth", "rt.pth"].each do |pth|
      (site_packages/pth).unlink if (site_packages/pth).exist?
    end
    rm_rf site_packages/"rt"
    rm_rf site_packages/"rti"
    cp_r "src/rt", site_packages/"rt"
    cp_r "src/rti", site_packages/"rti"
    Dir.glob("#{site_packages}/**/__pycache__").each { |d| rm_rf d }
    %w[rt rti].each do |pkg|
      unit_tests = site_packages/pkg/"unit_tests"
      rm_rf unit_tests if unit_tests.exist?
    end

    libexec.install site_packages => "site-packages"
    libexec.install "jars"

    java_home = Formula["openjdk@21"].opt_prefix/"libexec/openjdk.jdk/Contents/Home"

    {
      "rt" => "rt.main",
      "rti" => "rti.main",
    }.each do |cmd, entry_module|
      (bin/cmd).write <<~SH
        #!/bin/sh
        export PYTHONPATH="#{libexec}/site-packages${PYTHONPATH:+:$PYTHONPATH}"
        export RT_JARS_DIR="#{libexec}/jars"
        export JAVA_HOME="#{java_home}"
        exec "#{python}" -m #{entry_module} "$@"
      SH
      (bin/cmd).chmod 0755
    end
  end

  test do
    system bin/"rt", "--help"
    system bin/"rti", "--help"
  end
end
