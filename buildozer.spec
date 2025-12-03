[app]
title = UtkaSky
package.name = com.utka.utkaaky
version = 0.2 
source.dir = . 
android.api = 34
android.min_api = 26
android.target_api = 34
orientation = portrait
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
source.include_exts = py,png,jpg,kv,atlas,pc

# --- Требования (ffpyplayer удален) ---
requirements = python3==3.9.10,kivy,pillow,requests,filetype

buildozer.build_mode = debug
icon.filename = %(source.dir)s/ni.png

[buildozer]
log_level = 2
