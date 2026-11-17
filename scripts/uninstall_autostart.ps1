# Removes the auto-start shortcut and stops the connector if it is running.
#   powershell -ExecutionPolicy Bypass -File "scripts\uninstall_autostart.ps1"

$ErrorActionPreference = 'SilentlyContinue'

$startup = [Environment]::GetFolderPath('Startup')
foreach ($name in @('MLM2PRO-GSPro Connector.lnk','MLM2PRO-GSPro œšYÙK›šÉÊJHÂˆ	šÈH›Ú[‹T]	İ\\	˜[YBˆYˆ
\İT]	šÊHÈ™[[İ™KR][H	šÈQ›Ü˜ÙHBŸB‚ˆÈ™[[İ™H[HÛ\ÚÈØÚY[\ˆ›Øˆœ›ÛHX\›Y\ˆ™\œÚ[ÛœË‚•[œ™YÚ\İ\‹TØÚY[Y\ÚÈU\ÚÓ˜[YH	ÓSL”“ËQÔÔ›ÈœšYÙIÈPÛÛ™š\›N‰˜[ÙB‚ˆÈİÜ[H[›š[™ÈÛÛ›™XİÜˆ
ÛÛ\[Y^HÜˆ]ÛŠK‚‘Ù]PÚ[R[œİ[˜ÙHÚ[ŒÌ—Ô›ØÙ\ÜÈQš[\ˆ“˜[YOIÜ]ÛË™^IÈÔˆ˜[YOIÜ]Û‹™^IÈÔˆ˜[YOIÛ[Lœ›ËYÜÜ›ËXÛÛ›™XİÜ‹™^IÈˆˆÚ\™KSØš™XİÈ	ËÛÛ[X[™[™H[X]Ú	Û[Lœ›×ØœšYÙWœIÈ[Üˆ	Ë“˜[YHY\H	Û[Lœ›ËYÜÜ›ËXÛÛ›™XİÜ‹™^IÈHˆ›Ü‘XXÚSØš™XİÈİÜT›ØÙ\ÜÈRY	Ë”›ØÙ\ÜÒYQ›Ü˜ÙHB‚•Üš]KRÜİ”™[[İ™Y]]Ë\İ\[™İÜY[H[›š[™ÈÛÛ›™XİÜ‹ˆ‚