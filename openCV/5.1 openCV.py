import cv2
import queue
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from ultralytics import YOLO
import os
import pandas as pd



# videoCapture를 통해 실시간 웹캠 영상 받음
def reader(in_q: queue.Queue, width: int, height: int, fps: float, stop_event: threading.Event, lock: threading.Lock, metrics: dict):

    # 0은 웹캠과 연결됨
    capture = cv2.VideoCapture(0)
    
    # 가져올 frame의 크기를 지정
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # 영상의 속도 지정
    frame_interval = 1.0 / fps
    
    # 영상 속도 조절을 위한 시간
    next_time = time.perf_counter()

    try:
        # 스레드에 stop이 선언되지 않았으면 실행
        while not stop_event.is_set():
            now = time.perf_counter()
            
            # 프레임 속도 조절
            if now < next_time:
                time.sleep(min(0.001, next_time - now))
                continue
            
            # 받아온 프레임이 없으면 실행 종료
            ret, frame = capture.read()
            if not ret:
                break
            
            # frame 가져온 시간 추가
            cap_time = time.perf_counter()
            meta = {"cap_time": cap_time}
            
            # 큐가 꽉 차면 가장 오래된 frame 버리기 - drop-oldest 방식
            try:
                # 기다리지 않고 즉시 넣기
                meta["input_time"] = time.perf_counter()
                in_q.put_nowait((ret, frame, meta))
            except queue.Full:
                try:
                    # 가장 오래된 프레임 하나를 강제로 제거
                    in_q.get_nowait()
                    with lock:
                        metrics['dropped'] += 1
                   
                   # 입력 시간 기록
                    meta["input_time"] = time.perf_counter()
                    
                     # 그 자리에 새 프레임 넣기
                    in_q.put_nowait((ret, frame, meta))
                except:
                    pass
            
            # 다음 프레임을 위한 시간 설정
            next_time += frame_interval

    # 종료 신호
    finally:
        capture.release()
        try:
            meta["input_time"] = time.perf_counter()
            in_q.put((None, None, meta), timeout=0.1)
        except:
            pass


# YOLO를 활용한 객체 인식
def detect_person(frame, model, meta):

    """
    의도적으로 drop이 잘 측정되는 지 확인
    time.sleep(1)"""
    
    # 시작 시간
    t0 = time.perf_counter()
    
    # YOLO 모델을 사용마다 호출하는 것을 방지
    if not hasattr(detect_person, "yolo"):
        detect_person.yolo = YOLO(model)

    # yolo의 result[0]에는 추론한 객체의 사각형 좌표, 윤곽선, 관절 위치에 대한 정보가 들어있음
    results = detect_person.yolo.predict(frame, save=False, conf=0.5, verbose=False)
    result = results[0]

    # COCO 데이터 셋에서 class 0이 사람
    for box in result.boxes:
        if box.cls == 0:
            coords = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = coords
            frame = cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

    t1 = time.perf_counter()
   
    meta["detect_start_time"] = t0
    meta["detect_end_time"] = t1
    
    return frame, meta


# YOLO의 결과 값을 받아와 출력
def writer(in_q: queue.Queue, out_q: queue.Queue, fps: float, stop_event: threading.Event, lock: threading.Lock, metrics: dict):

    # 영상을 파일에 저장할 객체
    vw = None
 
    try:
        # 스레드에 stop이 선언되지 않았으면 실행
        while not stop_event.is_set():

            # out_q 비어있으면 대기
            try:
                ret, frame, meta = out_q.get(timeout=0.05)
                out_get_time = time.perf_counter()
                meta["out_get_time"] = out_get_time
            except queue.Empty:
                continue

            # 받아온 프레임이 없으면 실행 종료
            if ret is None:
                break
            
            # frame videdWriter 객체에 전달
            if vw is None:
                h, w = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                vw = cv2.VideoWriter("/Users/wnwlt/Desktop/실험 결과/out5.mp4", fourcc, fps, (w, h))

            # 화면에 출력 및 저장
            cv2.imshow("Video Frame", frame)
            vw.write(frame)
            
            # 각종 지연율 저장
            with lock:
                
                # in_q 넣음 ~ in_q에서 뺌 시간
                if "in_latencies" in meta and "in_get_time" in meta:
                    metrics["in_latencies"].append(meta["in_get_time"] - meta["input_time"])

                # 추론 시작 ~ 추론 끝난 시간
                if "detect_start_time" in meta and "detect_end_time" in meta:
                    metrics["detect_latencies"].append(meta["detect_end_time"] - meta["detect_start_time"])
                
                # in_q에서 뺌 ~ out_q에 넣음 시간
                if "in_get_time" in meta and "out_put_time" in meta:
                    metrics["total_execution_latencies"].append(meta["out_put_time"] - meta["in_get_time"])
                
                # out_q에서 뺌 ~ 추론 끝난 시간
                if "out_get_time" in meta and "detect_end_time" in meta:
                    metrics["out_latencies"].append(meta["out_get_time"] - meta["detect_end_time"])
                    
            # q 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord("q"):
                stop_event.set()
                # 빠르게 종료할 수 있게 in_q에도 종료 신호
                try:
                    in_q.put((None, None, None), timeout=0.1)
                except:
                    pass
                break
            
    # 사용했던 자원 반납
    finally:
        if vw is not None:
            vw.release()
        cv2.destroyAllWindows()


def main():

    # 영상 설정
    fps = 60
    width = 1080
    height = 720

    # 코어 수 설정
    n_worker = 2

    # 큐 사이즈 설정
    in_q_size = 2
    out_q_size = 8

    # 지표
    metrics = {"count" : 0, "dropped": 0, "in_latencies": [], "detect_latencies": [], "total_execution_latencies": [], "out_latencies": []}

    # 큐, 모델, 이벤트 설정
    in_q = queue.Queue(maxsize=in_q_size)
    out_q = queue.Queue(maxsize=out_q_size)

    lock = threading.Lock()
    model = "yolov8n.pt"

    stop_event = threading.Event()

    # 시작 시간
    start_time = time.perf_counter()

    # 초기 지연율을 줄이기 위해 wirter먼저 실행
    t_reader = threading.Thread(target=reader, args=(in_q, width, height, fps, stop_event, lock, metrics), daemon=True)
    t_writer = threading.Thread(target=writer, args=(in_q, out_q, fps, stop_event, lock, metrics), daemon=True)

    t_writer.start()
    t_reader.start()
    

    # in_q에서 받아 ProcessPool에 submit하고, 완료되면 out_q로 전달
    futures = []
    
    # 동작 중인 작업 너무 많지 않게 조절
    max_inflight = max(1, n_worker * 2)
    
    with ProcessPoolExecutor(max_workers=n_worker) as ex:

        while not stop_event.is_set():

            # 프레임을 받아 submit
            while len(futures) < max_inflight and not stop_event.is_set():
                try:
                    ret, frame, meta = in_q.get(timeout=0.05)
                    
                    # 꺼낸 시간
                    in_get_time = time.perf_counter()
                    
                except queue.Empty:
                    break

                if ret is None:
                    
                    stop_event.set()
                    break
                
                
                # in_get_time과 지연율 입력
                meta["in_get_time"] = in_get_time
                latency = in_get_time - meta["input_time"]
                metrics["in_latencies"].append(latency)

                futures.append(ex.submit(detect_person, frame, model, meta))

            # 완료된 작업 수거 후 out_q로 전달
            i = 0
            while i < len(futures):
                f = futures[i]
                if f.done():
                    try:
                        processed, meta = f.result()
                    except:
                        # 에러 나면 해당 프레임은 스킵하고 계속
                        futures.pop(i)
                        continue

                    # out_q가 꽉 차면 block, timeout으로 stop_event 체크
                    while not stop_event.is_set():
                        try:
                            meta["out_put_time"] = time.perf_counter()
                            out_q.put((True, processed, meta), timeout=0.05)
                            break
                        except queue.Full:
                            continue

                    metrics["count"] += 1
                    futures.pop(i)
                else:
                    i += 1

            time.sleep(0.001)

    # 종료 정리: writer에게 종료 신호
    try:
        meta["out_put_time"] = time.perf_counter()
        out_q.put((None, None, meta), timeout=0.1)
    except:
        pass

    # 스레드 조인
    t_reader.join(timeout=2.0)
    t_writer.join(timeout=2.0)

    # --------------------------- 지표 정리-------------------------------
   
    # 시간, 처리율, p95 지연율
    end_time = time.perf_counter()
    run_time = end_time - start_time
    
    throughput = metrics["count"] / run_time
    
    metrics['in_latencies'].sort()
    metrics['detect_latencies'].sort()
    metrics['total_execution_latencies'].sort()
    metrics['out_latencies'].sort()
    
    in_latencies = metrics['in_latencies']
    detect_latencies = metrics['detect_latencies']
    total_execution_latencies = metrics['total_execution_latencies']
    out_latencies = metrics['out_latencies']
    
    p95_in_latency = in_latencies[int(0.95 * (len(in_latencies) - 1))] if in_latencies else None
    p95_detect_latency = detect_latencies[int(0.95 * (len(detect_latencies) - 1))] if detect_latencies else None
    p95_total_execution_latencies = total_execution_latencies[int(0.95 * (len(total_execution_latencies) - 1))] if total_execution_latencies else None
    p95_out_latency = out_latencies[int(0.95 * (len(out_latencies) - 1))] if out_latencies else None

    print(f"처리율: {throughput}")
    print(f"총 실행 횟수: {metrics["count"]}")
    print(f"총 실행 시간: {run_time}")
    
    
    print(f"버린 개수: {metrics['dropped']}")
    
    print(f"in 큐 지연율: {p95_in_latency}")
    print(f"추론 지연율: {p95_detect_latency}")
    print(f"처리 지연율: {p95_total_execution_latencies}")
    print(f"out 큐 지연율: {p95_out_latency}")
    
    # ---------------------------------------- 엑셀에 저장 -------------------------------------
    
    # 파일 경로 설정
    file_path = '/Users/wnwlt/Desktop/실험 결과/video_result2.xlsx'

    # 신규 데이터 생성
    new_data = {
        '처리율': [throughput],
        '총 실행 횟수': [metrics["count"]],
        '총 실행 시간': [run_time],
        '버린 개수': [metrics['dropped']],
        'in 큐 지연율': [p95_in_latency],
        '추론 지연율': [p95_detect_latency],
        '처리 지연율': [p95_total_execution_latencies],
        'out 큐 지연율': [p95_out_latency]
    }
    
    new_df = pd.DataFrame(new_data)

    # 기존 파일 존재 여부 확인
    if os.path.exists(file_path):
        # 기존 데이터가 있으면 불러와서 합침
        old_df = pd.read_excel(file_path)
        combined_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        # 파일이 없으면 새로 생성
        combined_df = new_df

    # 저장
    combined_df.to_excel(file_path, index=False, sheet_name='drop')


if __name__ == "__main__":
    main()
