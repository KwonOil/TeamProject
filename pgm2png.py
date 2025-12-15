# pgm_to_png.py
from PIL import Image

# PGM 파일 열기
img = Image.open(r"C:\Temp\2025\TeamProject\app\static\maps\airport_map.pgm")

# PNG로 저장
img.save(r"C:\Temp\2025\TeamProject\app\static\maps\airport_map.png")

print("✅ map.png 생성 완료")