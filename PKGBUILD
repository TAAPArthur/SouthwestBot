# Maintainer: Arthur Williams <taaparthur@gmail.com>


pkgname='southwest-bot'
pkgver='0.9.6'
_language='en-US'
pkgrel=1
pkgdesc='Scan Southwest Airlines for a decrease in price'

arch=('any')
license=('MIT')
depends=('python3' 'python-selenium' 'at' 'geckodriver' 'firefox' )
opt_depends=('python-mysql-connector')
md5sums=('SKIP')

source=("git://github.com/TAAPArthur/SouthwestBot.git")
_srcDir="SouthwestBot"

package() {

    cd "$_srcDir"
    echo "$pkgdir/usr/lib/$pkgname/"
    mkdir -p "$pkgdir/usr/bin/"
    mkdir -p "$pkgdir/usr/lib/$pkgname/"
    
    install -D -m 0755 southwest-bot "$pkgdir/usr/bin/"
    install -D -m 0755 *.py timezones.txt "$pkgdir/usr/lib/$pkgname/" 
    mkdir -p ~/.config/"$pkgname"


    tokenFile=~/.config/"$pkgname"/token
    echo $tokenFile
    if [[ ! -s $tokenFile ]]; then
        echo "Please enter your chat token"
        read t
        echo $t > "$tokenFile"
    fi
    ln -s "$tokenFile" $pkgdir/usr/lib/$pkgname/token
    
}
