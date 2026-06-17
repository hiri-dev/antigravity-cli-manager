pkgname=antigravity-cli-manager-git
pkgver=1.0.r0
pkgrel=1
pkgdesc="A lightweight retro Terminal UI to manage and hot-swap Google Gemini account sessions for the agy CLI utility"
arch=('any')
url="https://github.com/hiri-dev/antigravity-cli-manager"
license=('MIT')
depends=('bash' 'python' 'curl' 'nodejs' 'npm')
makedepends=('git')
provides=('antigravity-cli-manager')
conflicts=('antigravity-cli-manager')
source=("git+https://github.com/hiri-dev/antigravity-cli-manager.git")
md5sums=('SKIP')

pkgver() {
  cd "${pkgname%-git}"
  printf "1.0.r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
  cd "${pkgname%-git}"
  install -Dm755 acm "$pkgdir/usr/bin/acm"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
