from pathlib import Path

marker = "PROJECT_CODENAME: ORBIT-7\nDATE_MARKER: 2025-05-01\nSIGNOFF_MARKER: Best regards\n"
Path('input_marker.txt').write_text(marker, encoding='utf-8')
