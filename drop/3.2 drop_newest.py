import threading
import queue
import time
import pandas as pd

# drop newest 방식을 적용한 생산자
def producer(q: queue.Queue, n_tasks: int, producer_fps: float, count: list, dropped: list, lock: threading.Lock):
    
    # frame 읽어오는 상황 가정
    interval = 1 / producer_fps
    
    for i in range(n_tasks):
        
        time.sleep(interval)
        
        # 큐에 집어 넣되 큐가 꽉차면 버리기
        try:
            input_time = time.perf_counter()
            q.put_nowait((i, input_time))
        except queue.Full:
            with lock:
                dropped[0] += 1


# 생산자의 큐로부터 값 가져오기
def consumer(q: queue.Queue, consumer_fps: float, latencies: list, count: list, lock):
    
    # frame 읽어오는 상황 가정
    interval = 1 / consumer_fps
    
    while True:
        time.sleep(interval)
        item, input_time = q.get()
        try:
            if item is None:
                break
            else:
                output_time = time.perf_counter()
                latency = output_time - input_time
                with lock:
                    latencies.append(latency)
                    count[0] += 1
        finally:
            q.task_done()
        

def main():
    
    n_tasks = 1000
    n_thread = 2
    q_size = 16
    lock = threading.Lock()
    
    producer_fps = 60.0
    consumer_fps = 20.0
    
    # 실험 결과를 저장하기 위한 저장소
    data = {'실행 횟수': []
            , '총 실행시간': []
            , '버린 작업개수': []
            , '처리율': []
            , '상위 5% 지연율': []}
    
    # 실험 30회 진행
    for j in range(30):
    
        count = [0]
        latencies = []
        dropped = [0]
        
        q = queue.Queue(maxsize = q_size)
        
        ths = []
        
        # 생성자부터 시작하면 첫 실행의 지연율이 올라 결과에 영향을 줄 수 있으므로
        # 소비자부터 시작
        
        th_p = threading.Thread(target=producer, args=(q, n_tasks, producer_fps, count, dropped, lock))
        
        for i in range(n_thread):
            ths.append(threading.Thread(target=consumer, args=(q, consumer_fps, latencies, count, lock)))
        
        
        # 스레드 시작
        start_time = time.perf_counter()
            
        for th in ths:
            th.start()
        
        th_p.start()
        th_p.join()
        
        # 스레드 수만큼 None 전달하여 종료 신호 전달
        for i in range(n_thread):
            q.put((None, None))
        
        for th in ths:
            th.join()
        
        q.join()
        
        # 지표 정리
        end_time = time.perf_counter()
            
        run_time = end_time - start_time
        throughput = count[0] / run_time
        latencies.sort()
        p95_latency = latencies[int(0.95 * (len(latencies) - 1))] if latencies else None
            
            
        print(f"총 실행횟수: {count[0]}")
        print(f"총 실행시간: {run_time}")
        print(f"버린 작업개수:{dropped[0]}")
        print(f"처리율: {throughput}")
        print(f"지연율 상위 5%: {p95_latency}")

        data['실행 횟수'].append(count[0])
        data['총 실행시간'].append(run_time)
        data['버린 작업개수'].append(dropped[0])
        data['처리율'].append(throughput)
        data['상위 5% 지연율'].append(p95_latency)
    
    # 엑셀에 저장  
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/drop_newest.xlsx', index=True, sheet_name='drop')

    

if __name__ == "__main__":
    main()
