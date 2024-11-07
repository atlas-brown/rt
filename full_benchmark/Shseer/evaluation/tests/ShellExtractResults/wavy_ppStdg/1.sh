cd ../wavytool
#pyside-uic -o mw_wavy.py mw_wavy.ui 
pyuic5 mw_wavy.ui -o mw_wavy.py
#pyside-uic -o dlg_wav2dat.py dlg_wav2dat.ui 
pyuic5 dlg_wav2dat.ui -o dlg_wav2dat.py
#pyside-rcc -o images/rc_wavy_rc.py images/rc_wavy.qrc 
pyrcc5 images/rc_wavy.qrc -o images/rc_wavy_rc.py
cd ../..

