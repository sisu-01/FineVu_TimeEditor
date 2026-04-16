import os
import glob
import numpy as np
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip

# =====================================================================
# 설정
# =====================================================================
FONT_PATH = "VT323-Regular.ttf"
FONT_SIZE = 30 
STRETCH_FACTOR = 1.168  # 가로로 늘릴 비율 (1.0은 원본, 1.5는 1.5배 넓게)

def process_frame(get_frame, t, start_datetime, font):
    # 1. 원본 프레임 가져오기
    frame = get_frame(t)
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    
    # 2. 기존 정보칸 가리기
    draw.rectangle([(448, 4), (1469, 23)], fill="black")
    
    # 3. 현재 프레임의 시간 계산
    current_time = start_datetime + timedelta(seconds=t)
    time_str = current_time.strftime("%Y%m%d-%Hh%Mm%Ss")
    text = f"FINEVu LX3000 V1.00.002 {time_str} ———km⁄h 14.30V MIC ON  2CH ANV"
    
    # A. 텍스트 크기 측정
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    # B. 여유 공간 확보
    padding_bottom = 10
    txt_img = Image.new("RGBA", (tw, th + padding_bottom), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    
    # 글자를 도화지 맨 꼭대기(0)보다 살짝 아래(1)에 그립니다.
    txt_draw.text((0, 1), text, font=font, fill="white")
    
    # C. 가로 리사이징
    new_width = int(tw * STRETCH_FACTOR)
    stretched_txt = txt_img.resize((new_width, th + padding_bottom), Image.LANCZOS)
    
    # D. 붙여넣기 위치 조정
    img.paste(stretched_txt, (447, -2), stretched_txt) 
    
    return np.array(img)

def main():
    os.makedirs("source", exist_ok=True)
    os.makedirs("done", exist_ok=True)
    
    if not os.path.exists(FONT_PATH):
        print(f"오류: '{FONT_PATH}' 파일이 없습니다. 폰트 파일을 준비해주세요.")
        return
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    
    print("\n" + "="*50)
    print("블랙박스 영상에 덧씌울 시작 시간을 설정합니다.")
    print("아래 예시와 정확히 같은 형식으로 입력해주세요.")
    print("▶ 예시: 20260101-20h13m25s")
    print("="*50)
    
    while True:
        target_start_time = input("시작 시간 입력: ").strip()
        
        try:
            start_datetime = datetime.strptime(target_start_time, "%Y%m%d-%Hh%Mm%Ss")
            break 
        except ValueError:
            print("\n❌ 입력 형식이 올바르지 않습니다!")
            print("다시 입력해주세요. (예시: 20260101-20h13m25s)\n")
            
    # .avi 파일과 .mp4 파일을 모두 찾도록 확장
    video_files = glob.glob("source/*.avi") + glob.glob("source/*.mp4")
    
    if not video_files:
        print("source 폴더에 변환할 영상(.avi 또는 .mp4)이 없습니다.")
        return

    print(f"\n총 {len(video_files)}개의 영상 변환을 시작합니다...\n")

    for file_path in video_files:
        filename = os.path.basename(file_path) # 예: yyyymmdd-00h00m00s_E.avi
        
        # 파일명에서 확장자를 제외한 부분과 확장자 분리
        name_without_ext, _ = os.path.splitext(filename)
        
        # '_E' 등 원본 영상의 접미사가 있다면 추출 (전/후방 카메라 구분 등을 위해)
        if '_' in name_without_ext:
            suffix = name_without_ext[name_without_ext.find('_'):] # 예: '_E'
        else:
            suffix = ""
            
        # 새로운 파일명 생성 (사용자입력시간 + 접미사 + .mp4)
        new_filename = f"{target_start_time}{suffix}.mp4"
        output_path = os.path.join("done", new_filename)
        
        print(f"작업 시작: {filename} -> {new_filename}")
        
        clip = VideoFileClip(file_path)
        
        try:
            modified_clip = clip.transform(lambda get_frame, t: process_frame(get_frame, t, start_datetime, font))
        except AttributeError:
            modified_clip = clip.fl(lambda get_frame, t: process_frame(get_frame, t, start_datetime, font))
        
        modified_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=clip.fps,
            preset="fast"
        )
        
        clip.close()
        modified_clip.close()
        print(f"저장 완료: {output_path}\n")

if __name__ == "__main__":
    main()
    print("="*50)
    input("모든 작업이 완료되었습니다. 엔터(Enter) 키를 누르면 창이 닫힙니다...")