security create-keychain -p travis ios-build.keychain
security import ./scripts/travis/apple.cer -k ~/Library/Keychains/ios-build.keychain -T /usr/bin/codesign
security import ./scripts/travis/dev.cer -k ~/Library/Keychains/ios-build.keychain -T /usr/bin/codesign
security import ./scripts/travis/dev.p12 -k ~/Library/Keychains/ios-build.keychain -P $DEV_KEY_PASSWORD -T /usr/bin/codesign
security import ./scripts/travis/dist.p12 -k ~/Library/Keychains/ios-build.keychain -P $DIST_KEY_PASSWORD -T /usr/bin/codesign
security import ./scripts/travis/dist.p12 -k ~/Library/Keychains/ios-build.keychain -P $DIST_KEY_PASSWORD -T /usr/bin/codesign

echo "Unlock keychain"
security unlock-keychain -p secret ios-build.keychain

echo "Increase keychain unlock timeout"
security set-keychain-settings -lut 7200 ios-build.keychain

echo "Add keychain to keychain-list"
security list-keychains -s ios-build.keychain

echo "Add Provisioning Profiles"
mkdir -p ~/Library/MobileDevice/Provisioning\ Profiles
cp ./scripts/travis/profiles/* ~/Library/MobileDevice/Provisioning\ Profiles/
